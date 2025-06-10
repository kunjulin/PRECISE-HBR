#!/usr/bin/env python3
"""
Test script for verifying fhirclient connection to Cerner sandbox.
This script tests the basic connectivity and data fetching capabilities.
"""

import os
import sys
import logging
from fhirclient import client
from fhirclient.models import patient, observation, condition

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

# Cerner Open Sandbox Configuration
CERNER_SANDBOX_CONFIG = {
    'fhir_base': 'https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d',
    'test_patient_ids': [
        '12724066',  # Patient with good test data
        '12724065',  # Another test patient
        '12742400'   # Third test patient
    ]
}

def test_fhir_client_connection():
    """Test basic FHIR client connection to Cerner sandbox."""
    print("🧪 Testing FHIR Client Connection to Cerner Sandbox")
    print("=" * 60)
    
    try:
        # Initialize FHIR client for Cerner Open Sandbox (no auth required)
        settings = {
            'app_id': 'test-app',
            'api_base': CERNER_SANDBOX_CONFIG['fhir_base'],
        }
        
        smart = client.FHIRClient(settings=settings)
        print(f"✅ FHIR Client initialized successfully")
        print(f"   Server: {smart.server.base_uri}")
        
        # Test server capabilities
        try:
            capability = smart.server.request_json('metadata')
            print(f"✅ Server metadata retrieved successfully")
            print(f"   FHIR Version: {capability.get('fhirVersion', 'Unknown')}")
            print(f"   Implementation: {capability.get('implementation', {}).get('description', 'Unknown')}")
        except Exception as e:
            print(f"❌ Failed to get server metadata: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize FHIR client: {e}")
        return False

def test_patient_data_fetching():
    """Test fetching patient data using fhirclient."""
    print("\n🏥 Testing Patient Data Fetching")
    print("=" * 60)
    
    try:
        settings = {
            'app_id': 'test-app',
            'api_base': CERNER_SANDBOX_CONFIG['fhir_base'],
        }
        
        smart = client.FHIRClient(settings=settings)
        
        for patient_id in CERNER_SANDBOX_CONFIG['test_patient_ids']:
            print(f"\n📋 Testing Patient ID: {patient_id}")
            
            try:
                # Fetch patient resource
                patient_resource = patient.Patient.read(patient_id, smart.server)
                
                if patient_resource:
                    print(f"✅ Patient resource fetched successfully")
                    
                    # Extract basic info
                    name_data = patient_resource.name[0] if patient_resource.name else None
                    if name_data:
                        given_name = " ".join(name_data.given or [])
                        family_name = name_data.family or ""
                        full_name = f"{given_name} {family_name}".strip()
                        print(f"   Name: {full_name}")
                    
                    print(f"   Gender: {patient_resource.gender}")
                    print(f"   Birth Date: {patient_resource.birthDate}")
                    
                    # Test fetching observations
                    try:
                        obs_search = observation.Observation.where({
                            'patient': patient_id,
                            'code': '33914-3',  # eGFR LOINC code
                            '_count': '1'
                        }).perform(smart.server)
                        
                        obs_count = len(obs_search.entry) if obs_search.entry else 0
                        print(f"   eGFR Observations: {obs_count} found")
                        
                    except Exception as e:
                        print(f"   ⚠️  Failed to fetch observations: {e}")
                    
                    # Test fetching conditions
                    try:
                        cond_search = condition.Condition.where({
                            'patient': patient_id,
                            '_count': '5'
                        }).perform(smart.server)
                        
                        cond_count = len(cond_search.entry) if cond_search.entry else 0
                        print(f"   Conditions: {cond_count} found")
                        
                    except Exception as e:
                        print(f"   ⚠️  Failed to fetch conditions: {e}")
                        
                else:
                    print(f"❌ Patient resource not found")
                    
            except Exception as e:
                print(f"❌ Failed to fetch patient {patient_id}: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ General error in patient data fetching: {e}")
        return False

def test_search_parameters():
    """Test various FHIR search parameters."""
    print("\n🔍 Testing FHIR Search Parameters")
    print("=" * 60)
    
    try:
        settings = {
            'app_id': 'test-app', 
            'api_base': CERNER_SANDBOX_CONFIG['fhir_base'],
        }
        
        smart = client.FHIRClient(settings=settings)
        patient_id = CERNER_SANDBOX_CONFIG['test_patient_ids'][0]
        
        # Test different observation searches
        test_searches = [
            ('Hemoglobin', {'patient': patient_id, 'code': '718-7', '_count': '1'}),
            ('Creatinine', {'patient': patient_id, 'code': '2160-0', '_count': '1'}),
            ('Platelet', {'patient': patient_id, 'code': '26515-7', '_count': '1'}),
        ]
        
        for search_name, search_params in test_searches:
            try:
                result = observation.Observation.where(search_params).perform(smart.server)
                count = len(result.entry) if result.entry else 0
                print(f"✅ {search_name} search: {count} results")
                
                if result.entry and result.entry[0].resource:
                    obs = result.entry[0].resource
                    if hasattr(obs, 'valueQuantity') and obs.valueQuantity:
                        value = obs.valueQuantity.value
                        unit = obs.valueQuantity.unit
                        print(f"   Sample value: {value} {unit}")
                        
            except Exception as e:
                print(f"❌ {search_name} search failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search parameter testing failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 FHIR Client Testing Suite for Cerner Sandbox")
    print("=" * 60)
    
    tests = [
        ("Connection Test", test_fhir_client_connection),
        ("Patient Data Fetching", test_patient_data_fetching),
        ("Search Parameters", test_search_parameters),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your fhirclient setup is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 