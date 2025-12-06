#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 FHIR 服務器連接腳本
用於測試 10.29.99.18:8080 FHIR 服務器
"""
import requests
import json
import sys

# 設置 UTF-8 編碼以支持中文輸出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置 FHIR 服務器
FHIR_SERVER_BASE = "10.29.99.18:8080"
# 嘗試不同的 URL 格式
FHIR_SERVER_URLS = [
    f"http://{FHIR_SERVER_BASE}",
    f"http://{FHIR_SERVER_BASE}/fhir",
    f"http://{FHIR_SERVER_BASE}/fhir/",
]

print("=" * 60)
print("FHIR 服務器連接測試")
print("=" * 60)
print(f"目標服務器: {FHIR_SERVER_BASE}\n")

# 測試每個可能的 URL 格式
working_url = None
for url in FHIR_SERVER_URLS:
    print(f"測試 URL: {url}")
    print("-" * 60)
    
    # 測試 1: 檢查服務器是否可訪問
    print("1. 檢查服務器連接...")
    try:
        # 先嘗試 metadata 端點
        metadata_url = f"{url}/metadata" if not url.endswith('/') else f"{url}metadata"
        response = requests.get(
            metadata_url,
            headers={'Accept': 'application/fhir+json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"   [✓] 連接成功！使用 URL: {url}")
            working_url = url
            metadata = response.json()
            if 'resourceType' in metadata:
                print(f"   FHIR 版本: {metadata.get('fhirVersion', 'Unknown')}")
                print(f"   資源類型: {metadata.get('resourceType', 'Unknown')}")
            
            # 檢查是否支持 SMART
            print("\n2. 檢查 SMART on FHIR 支持...")
            smart_config_url = f"{url}/.well-known/smart-configuration" if not url.endswith('/') else f"{url}.well-known/smart-configuration"
            try:
                smart_response = requests.get(
                    smart_config_url,
                    headers={'Accept': 'application/json'},
                    timeout=10
                )
                if smart_response.status_code == 200:
                    smart_config = smart_response.json()
                    print("   [✓] 支持 SMART on FHIR")
                    print(f"   授權端點: {smart_config.get('authorization_endpoint', 'N/A')}")
                    print(f"   Token 端點: {smart_config.get('token_endpoint', 'N/A')}")
                else:
                    print(f"   [!] 不支持 SMART on FHIR (狀態碼: {smart_response.status_code})")
            except:
                print("   [!] 不支持 SMART on FHIR 配置發現")
            
            break
        else:
            print(f"   [!] 響應狀態碼: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"   [✗] 無法連接到服務器")
    except requests.exceptions.Timeout:
        print(f"   [✗] 連接超時")
    except Exception as e:
        print(f"   [✗] 錯誤: {e}")
    
    print()

if working_url:
    print("\n" + "=" * 60)
    print("測試結果")
    print("=" * 60)
    print(f"✓ 服務器 URL: {working_url}")
    print("\n可用測試方式：")
    print("\n1. 測試患者列表頁面（推薦，無需 OAuth）：")
    print(f"   http://localhost:8080/test-patients?server={working_url}")
    
    print("\n2. 測試模式（直接指定患者 ID）：")
    print(f"   http://localhost:8080/test-mode?server={working_url}&patient_id=YOUR_PATIENT_ID")
    
    print("\n3. Standalone Launch（如果服務器支持 SMART）：")
    print(f"   http://localhost:8080/standalone")
    print(f"   然後輸入服務器 URL: {working_url}")
    
    print("\n" + "=" * 60)
else:
    print("\n" + "=" * 60)
    print("無法連接到 FHIR 服務器")
    print("=" * 60)
    print("請檢查：")
    print("1. 服務器是否正在運行")
    print("2. 網絡連接是否正常")
    print("3. URL 格式是否正確")
    print("4. 防火牆設置是否允許連接")


