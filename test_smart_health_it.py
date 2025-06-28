#!/usr/bin/env python3
"""
SMART Health IT Random Patient Testing Script
============================================

This script fetches random patients from the SMART Health IT test server,
calculates bleeding risk scores, and generates a comprehensive test report.

Usage:
    python test_smart_health_it.py

Features:
- Fetches 30+ random patients from SMART Health IT
- Calculates PRECISE-DAPT bleeding risk scores
- Generates detailed test report with statistics
- Includes patient demographics and risk distributions
- Exports results to JSON and HTML formats
"""

import requests
import json
import logging
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import statistics
from collections import Counter

# Import our existing FHIR data service
from fhir_data_service import get_fhir_data, calculate_risk_components, get_patient_demographics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_health_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class PatientTestResult:
    """Data class to store test results for each patient"""
    patient_id: str
    name: str
    age: Optional[int]
    gender: str
    total_score: int
    risk_level: str
    test_successful: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0

class SmartHealthITTester:
    """Main testing class for SMART Health IT integration"""
    
    def __init__(self):
        # SMART Health IT public FHIR server endpoints
        self.fhir_base_url = "https://r4.smarthealthit.org"
        self.patient_endpoint = f"{self.fhir_base_url}/Patient"
        
        # Test configuration
        self.target_patient_count = 30
        self.results: List[PatientTestResult] = []
        self.test_start_time = datetime.now()
        
        # Statistics tracking
        self.stats = {
            'total_patients_tested': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'total_processing_time': 0.0,
            'risk_distribution': Counter(),
            'age_distribution': [],
            'gender_distribution': Counter(),
            'score_distribution': []
        }

    def fetch_random_patients(self, count: int = 30) -> List[str]:
        """
        Fetch random patient IDs from SMART Health IT server
        
        Args:
            count: Number of patients to fetch
            
        Returns:
            List of patient IDs
        """
        logger.info(f"Fetching {count} random patients from SMART Health IT...")
        
        patient_ids = []
        
        try:
            response = requests.get(
                self.patient_endpoint,
                params={'_count': count},
                headers={'Accept': 'application/fhir+json'},
                timeout=30
            )
            
            if response.status_code == 200:
                bundle = response.json()
                
                if 'entry' in bundle:
                    for entry in bundle['entry']:
                        if 'resource' in entry:
                            patient_id = entry['resource']['id']
                            patient_ids.append(patient_id)
                            
                logger.info(f"Successfully fetched {len(patient_ids)} patient IDs")
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Error fetching patients: {e}")
            
        return patient_ids[:count]

    def test_patient_risk_calculation(self, patient_id: str) -> PatientTestResult:
        """
        Test bleeding risk calculation for a single patient
        
        Args:
            patient_id: FHIR patient ID
            
        Returns:
            PatientTestResult object with test results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Testing patient {patient_id}...")
            
            # Fetch FHIR data (no access token needed for public SMART Health IT)
            raw_data, error = get_fhir_data(
                fhir_server_url=self.fhir_base_url,
                access_token=None,  # Public endpoint doesn't require auth
                patient_id=patient_id,
                client_id="test-client"
            )
            
            if error:
                return PatientTestResult(
                    patient_id=patient_id,
                    name="Unknown",
                    age=None,
                    gender="Unknown",
                    total_score=0,
                    risk_level="Error",
                    test_successful=False,
                    error_message=error,
                    processing_time=time.time() - start_time
                )
            
            # Get patient demographics
            demographics = get_patient_demographics(raw_data.get("patient"))
            
            # Calculate risk components and total score
            components, total_score = calculate_risk_components(raw_data, demographics)
            
            # Determine risk level based on PRECISE-DAPT thresholds
            if total_score >= 25:
                risk_level = 'High Bleeding Risk (≥25)'
            elif total_score >= 16:
                risk_level = 'Moderate Bleeding Risk (16-24)'
            else:
                risk_level = 'Low Bleeding Risk (0-15)'
            
            # Create successful test result
            result = PatientTestResult(
                patient_id=patient_id,
                name=demographics.get('name', 'Unknown'),
                age=demographics.get('age'),
                gender=demographics.get('gender', 'Unknown'),
                total_score=total_score,
                risk_level=risk_level,
                test_successful=True,
                processing_time=time.time() - start_time
            )
            
            logger.info(f"✓ Patient {patient_id}: Score={total_score}, Risk={risk_level}")
            return result
            
        except Exception as e:
            logger.error(f"✗ Error testing patient {patient_id}: {e}")
            return PatientTestResult(
                patient_id=patient_id,
                name="Unknown",
                age=None,
                gender="Unknown",
                total_score=0,
                risk_level="Error",
                test_successful=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )

    def run_test(self) -> Dict[str, Any]:
        """
        Run comprehensive test with multiple patients
        
        Returns:
            Dictionary containing test results and statistics
        """
        logger.info("🚀 Starting SMART Health IT test...")
        
        # Fetch random patients
        patient_ids = self.fetch_random_patients(self.target_patient_count)
        
        if not patient_ids:
            logger.error("❌ No patients found. Test aborted.")
            return {"error": "No patients found"}
        
        # Test each patient
        for i, patient_id in enumerate(patient_ids, 1):
            logger.info(f"📊 Testing patient {i}/{len(patient_ids)}: {patient_id}")
            
            result = self.test_patient_risk_calculation(patient_id)
            self.results.append(result)
            
            # Rate limiting to be respectful to the server
            time.sleep(0.5)
        
        # Generate final report
        report = self.generate_report()
        
        logger.info("✅ Comprehensive test completed!")
        return report

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        test_duration = datetime.now() - self.test_start_time
        successful_results = [r for r in self.results if r.test_successful]
        failed_results = [r for r in self.results if not r.test_successful]
        
        # Calculate statistics
        scores = [r.total_score for r in successful_results]
        ages = [r.age for r in successful_results if r.age is not None]
        
        risk_distribution = Counter(r.risk_level for r in successful_results)
        gender_distribution = Counter(r.gender for r in successful_results)
        
        report = {
            'test_metadata': {
                'test_date': self.test_start_time.isoformat(),
                'test_duration_seconds': test_duration.total_seconds(),
                'fhir_server': self.fhir_base_url,
                'target_patient_count': self.target_patient_count,
                'software_version': 'FHIR Bleeding Risk Calculator v1.0'
            },
            'summary': {
                'total_patients': len(self.results),
                'successful_tests': len(successful_results),
                'failed_tests': len(failed_results),
                'success_rate': round(len(successful_results) / len(self.results) * 100, 2) if self.results else 0
            },
            'risk_analysis': {
                'risk_distribution': dict(risk_distribution),
                'score_stats': {
                    'mean': round(statistics.mean(scores), 2) if scores else 0,
                    'median': round(statistics.median(scores), 2) if scores else 0,
                    'min': min(scores) if scores else 0,
                    'max': max(scores) if scores else 0
                },
                'age_stats': {
                    'mean': round(statistics.mean(ages), 1) if ages else 0,
                    'min': min(ages) if ages else 0,
                    'max': max(ages) if ages else 0
                },
                'gender_distribution': dict(gender_distribution)
            },
            'detailed_results': [
                {
                    'patient_id': r.patient_id,
                    'name': r.name,
                    'age': r.age,
                    'gender': r.gender,
                    'score': r.total_score,
                    'risk_level': r.risk_level,
                    'success': r.test_successful,
                    'error': r.error_message,
                    'time': round(r.processing_time, 3)
                }
                for r in self.results
            ]
        }
        
        return report

    def save_report(self, report: Dict[str, Any], filename_prefix: str = "smart_health_test"):
        """Save report to JSON and HTML files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"📄 JSON report saved: {json_filename}")
        
        # Save HTML report
        html_filename = f"{filename_prefix}_{timestamp}.html"
        self.generate_html_report(report, html_filename)
        logger.info(f"🌐 HTML report saved: {html_filename}")
        
        return json_filename, html_filename

    def generate_html_report(self, report: Dict[str, Any], filename: str):
        """Generate an HTML report with visualizations"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FHIR 出血風險計算器測試報告</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1 class="text-center mb-4">
                    <i class="fas fa-heartbeat text-danger"></i>
                    FHIR 出血風險計算器測試報告
                </h1>
                <p class="text-center text-muted">
                    測試日期: {report['test_metadata']['test_date']}<br>
                    FHIR 伺服器: <a href="{report['test_metadata']['fhir_server']}">{report['test_metadata']['fhir_server']}</a>
                </p>
            </div>
        </div>

        <!-- Summary Statistics -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-center bg-primary text-white">
                    <div class="card-body">
                        <h5 class="card-title">總測試患者</h5>
                        <h2>{report['summary']['total_patients']}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center bg-success text-white">
                    <div class="card-body">
                        <h5 class="card-title">成功測試</h5>
                        <h2>{report['summary']['successful_tests']}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center bg-danger text-white">
                    <div class="card-body">
                        <h5 class="card-title">失敗測試</h5>
                        <h2>{report['summary']['failed_tests']}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center bg-info text-white">
                    <div class="card-body">
                        <h5 class="card-title">成功率</h5>
                        <h2>{report['summary']['success_rate']}%</h2>
                    </div>
                </div>
            </div>
        </div>

        <!-- Risk Distribution Chart -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-pie"></i> 風險等級分佈</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="riskChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar"></i> 分數分佈</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="scoreChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Statistics Table -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-table"></i> 詳細統計</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>分數統計</h6>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>平均分數:</span>
                                        <strong>{report['risk_analysis']['score_stats']['mean']}</strong>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>中位數分數:</span>
                                        <strong>{report['risk_analysis']['score_stats']['median']}</strong>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>最低分數:</span>
                                        <strong>{report['risk_analysis']['score_stats']['min']}</strong>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>最高分數:</span>
                                        <strong>{report['risk_analysis']['score_stats']['max']}</strong>
                                    </li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6>年齡統計</h6>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>平均年齡:</span>
                                        <strong>{report['risk_analysis']['age_stats']['mean']} 歲</strong>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>最小年齡:</span>
                                        <strong>{report['risk_analysis']['age_stats']['min']} 歲</strong>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>最大年齡:</span>
                                        <strong>{report['risk_analysis']['age_stats']['max']} 歲</strong>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Detailed Results Table -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-list"></i> 詳細測試結果</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>患者ID</th>
                                        <th>姓名</th>
                                        <th>年齡</th>
                                        <th>性別</th>
                                        <th>分數</th>
                                        <th>風險等級</th>
                                        <th>狀態</th>
                                    </tr>
                                </thead>
                                <tbody>
        """
        
        # Add patient rows
        for result in report['detailed_results']:
            status_badge = "success" if result['success'] else "danger"
            status_text = "成功" if result['success'] else "失敗"
            risk_badge = "danger" if "High" in result['risk_level'] else ("warning" if "Moderate" in result['risk_level'] else "success")
            
            html_content += f"""
                                    <tr>
                                        <td><code>{result['patient_id']}</code></td>
                                        <td>{result['name']}</td>
                                        <td>{result['age'] if result['age'] else 'N/A'}</td>
                                        <td>{result['gender']}</td>
                                        <td><span class="badge bg-{risk_badge}">{result['score']}</span></td>
                                        <td><small>{result['risk_level']}</small></td>
                                        <td><span class="badge bg-{status_badge}">{status_text}</span></td>
                                    </tr>
            """
        
        html_content += """
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Risk Distribution Pie Chart
        const riskData = """ + json.dumps(report['risk_analysis']['risk_distribution']) + """;
        const riskCtx = document.getElementById('riskChart').getContext('2d');
        new Chart(riskCtx, {
            type: 'pie',
            data: {
                labels: Object.keys(riskData),
                datasets: [{
                    data: Object.values(riskData),
                    backgroundColor: ['#dc3545', '#ffc107', '#28a745']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // Score Distribution Histogram (simplified)
        const scoreStats = """ + json.dumps(report['risk_analysis']['score_stats']) + """;
        const scoreCtx = document.getElementById('scoreChart').getContext('2d');
        new Chart(scoreCtx, {
            type: 'bar',
            data: {
                labels: ['最低分', '平均分', '中位數', '最高分'],
                datasets: [{
                    label: 'PRECISE-DAPT 分數',
                    data: [scoreStats.min, scoreStats.mean, scoreStats.median, scoreStats.max],
                    backgroundColor: ['#28a745', '#17a2b8', '#ffc107', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """Main execution function"""
    print("🚀 FHIR 出血風險計算器 - SMART Health IT 測試")
    print("=" * 50)
    
    # Create tester instance
    tester = SmartHealthITTester()
    
    try:
        # Run comprehensive test
        report = tester.run_test()
        
        if 'error' in report:
            logger.error(f"❌ Test failed: {report['error']}")
            return 1
        
        # Save reports
        json_file, html_file = tester.save_report(report)
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 測試摘要")
        print("=" * 50)
        print(f"✅ 總測試患者: {report['summary']['total_patients']}")
        print(f"✅ 成功測試: {report['summary']['successful_tests']}")
        print(f"❌ 失敗測試: {report['summary']['failed_tests']}")
        print(f"📈 成功率: {report['summary']['success_rate']}%")
        print(f"⏱️  測試持續時間: {report['test_metadata']['test_duration_seconds']} 秒")
        print(f"📄 JSON 報告: {json_file}")
        print(f"🌐 HTML 報告: {html_file}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("測試被用戶中斷")
        return 1
    except Exception as e:
        logger.error(f"測試執行錯誤: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 