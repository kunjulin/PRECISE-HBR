#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的測試腳本，用於驗證 FHIR 服務器和患者連接
使用方法: python test_patient_connection.py
"""
import requests
import json
import sys

# 設置 UTF-8 編碼以支持中文輸出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置 - 可以修改這些值來測試不同的服務器和患者
FHIR_SERVER = "http://10.29.99.18:9091/fhir/"
PATIENT_ID = "0322400H12092976400000000000000"

print(f"正在測試 FHIR 服務器: {FHIR_SERVER}")
print(f"患者 ID: {PATIENT_ID}")
print("-" * 60)

# 測試 1: 檢查服務器是否可訪問
print("\n1. 檢查 FHIR 服務器連接...")
try:
    response = requests.get(
        f"{FHIR_SERVER}metadata",
        headers={'Accept': 'application/fhir+json'},
        timeout=10
    )
    if response.status_code == 200:
        print("[OK] FHIR 服務器連接成功")
        metadata = response.json()
        if 'resourceType' in metadata:
            print(f"   FHIR 版本: {metadata.get('fhirVersion', 'Unknown')}")
    else:
        print(f"[WARN] 服務器響應狀態碼: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"[ERROR] 無法連接到 FHIR 服務器: {e}")
    exit(1)

# 測試 2: 獲取患者資源
print(f"\n2. 獲取患者資源 Patient/{PATIENT_ID}...")
try:
    response = requests.get(
        f"{FHIR_SERVER}Patient/{PATIENT_ID}",
        headers={'Accept': 'application/fhir+json'},
        timeout=10
    )
    
    if response.status_code == 200:
        patient = response.json()
        print("[OK] 成功獲取患者資源")
        
        # 顯示患者基本信息
        if 'name' in patient and patient['name']:
            name = patient['name'][0]
            if 'text' in name:
                print(f"   姓名: {name['text']}")
            else:
                given = ' '.join(name.get('given', []))
                family = name.get('family', '')
                print(f"   姓名: {given} {family}".strip())
        
        if 'gender' in patient:
            print(f"   性別: {patient['gender']}")
        
        if 'birthDate' in patient:
            print(f"   出生日期: {patient['birthDate']}")
        
        print(f"   資源 ID: {patient.get('id', 'N/A')}")
        
    elif response.status_code == 404:
        print(f"[ERROR] 患者未找到 (404)")
        print("   請確認患者 ID 是否正確")
    elif response.status_code == 401:
        print(f"[WARN] 需要認證 (401)")
        print("   此服務器可能需要 OAuth 認證")
    elif response.status_code == 403:
        print(f"[WARN] 訪問被拒絕 (403)")
        print("   您可能沒有訪問此患者數據的權限")
    else:
        print(f"[WARN] 響應狀態碼: {response.status_code}")
        print(f"   響應內容: {response.text[:200]}")
        
except requests.exceptions.RequestException as e:
    print(f"[ERROR] 請求失敗: {e}")

# 測試 3: 生成測試模式 URL
print(f"\n3. 測試模式訪問 URL:")
test_url = f"http://localhost:8081/test-mode?server={FHIR_SERVER}&patient_id={PATIENT_ID}"
print(f"   {test_url}")
print("\n   您可以在瀏覽器中訪問此 URL 來測試患者數據")

print("\n" + "=" * 60)
print("測試完成！")









