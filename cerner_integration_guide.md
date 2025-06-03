# Cerner EHR 系統整合指南

## 1. Cerner 開發者註冊流程

### 步驟 1: 註冊 Cerner 開發者帳戶
1. 前往 [Cerner Developer Portal](https://fhir.cerner.com/)
2. 建立開發者帳戶
3. 完成身份驗證流程

### 步驟 2: 應用程式註冊
```json
{
  "application_name": "ARC-HBR Bleeding Risk Calculator",
  "description": "SMART on FHIR app for calculating bleeding risk using ARC-HBR criteria",
  "redirect_uris": [
    "https://yourdomain.com/callback"
  ],
  "scopes": [
    "launch/patient",
    "openid",
    "fhirUser",
    "profile",
    "patient/Patient.read",
    "patient/Observation.read",
    "patient/Condition.read",
    "patient/MedicationRequest.read",
    "patient/Procedure.read"
  ],
  "launch_uri": "https://yourdomain.com/launch"
}
```

## 2. Cerner FHIR 實施特性

### 支援的 FHIR 版本
- **R4** (推薦)
- **DSTU2** (舊版，逐步淘汰)

### Cerner 特定的 FHIR 擴展
```python
# 處理 Cerner 特定的擴展
def handle_cerner_extensions(resource):
    """處理 Cerner 特定的 FHIR 擴展"""
    extensions = resource.get('extension', [])
    
    for ext in extensions:
        if ext.get('url') == 'https://fhir-ehr.cerner.com/r4/StructureDefinition/client-organization':
            # 處理組織資訊
            pass
        elif ext.get('url') == 'https://fhir-ehr.cerner.com/r4/StructureDefinition/encounter-guarantor':
            # 處理保證人資訊
            pass
```

### 常見的 Cerner LOINC 代碼對應
```python
# Cerner 環境中常見的實驗室檢驗代碼
CERNER_LOINC_MAPPINGS = {
    "CREATININE": {
        "primary": "2160-0",  # Creatinine [Mass/volume] in Serum or Plasma
        "alternatives": ["38483-4", "59826-8"]
    },
    "HEMOGLOBIN": {
        "primary": "718-7",   # Hemoglobin [Mass/volume] in Blood
        "alternatives": ["30313-1", "59260-0"]
    },
    "PLATELET": {
        "primary": "777-3",   # Platelets [#/volume] in Blood by Automated count
        "alternatives": ["26515-7", "778-1"]
    }
}
```

## 3. Cerner 特定的安全要求

### OAuth 2.0 / SMART on FHIR 配置
```python
# Cerner 特定的 OAuth 配置
CERNER_OAUTH_CONFIG = {
    "authorization_endpoint": "https://authorization.cerner.com/tenants/{tenant_id}/protocols/oauth2/profiles/smart-v1/personas/provider/authorize",
    "token_endpoint": "https://authorization.cerner.com/tenants/{tenant_id}/protocols/oauth2/profiles/smart-v1/token",
    "jwks_uri": "https://authorization.cerner.com/tenants/{tenant_id}/keys",
    "scopes_supported": [
        "launch/patient",
        "openid",
        "fhirUser",
        "profile",
        "patient/*.read",
        "user/*.read"
    ]
}
```

### 憑證管理
```python
# 生產環境憑證配置
import ssl
import certifi

def configure_ssl_context():
    """配置 SSL 上下文以符合 Cerner 安全要求"""
    context = ssl.create_default_context(cafile=certifi.where())
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return context
```

## 4. 資料對應與轉換

### Cerner 特定的資料結構
```python
def parse_cerner_patient(patient_resource):
    """解析 Cerner Patient 資源"""
    # Cerner 可能使用不同的識別符系統
    identifiers = patient_resource.get('identifier', [])
    
    mrn = None
    for identifier in identifiers:
        if identifier.get('type', {}).get('coding', [{}])[0].get('code') == 'MR':
            mrn = identifier.get('value')
            break
    
    return {
        'id': patient_resource.get('id'),
        'mrn': mrn,
        'name': get_human_name_text(patient_resource.get('name')),
        'birth_date': patient_resource.get('birthDate'),
        'gender': patient_resource.get('gender')
    }
```

### 藥物資料處理
```python
def parse_cerner_medication(med_request):
    """解析 Cerner MedicationRequest"""
    # Cerner 可能使用 medicationReference 而非 medicationCodeableConcept
    if 'medicationReference' in med_request:
        # 需要額外的 API 呼叫來獲取藥物詳細資訊
        med_ref = med_request['medicationReference']['reference']
        # 實施藥物參考解析邏輯
        pass
    elif 'medicationCodeableConcept' in med_request:
        return med_request['medicationCodeableConcept']
    
    return None
```

## 5. 測試與驗證

### Cerner 沙盒環境
```python
# 沙盒環境配置
CERNER_SANDBOX_CONFIG = {
    "fhir_base_url": "https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d",
    "client_id": "your_sandbox_client_id",
    "redirect_uri": "https://your-app.com/callback"
}
```

### 測試病患資料
```python
# Cerner 沙盒中的測試病患 ID
TEST_PATIENTS = {
    "adult_male": "12724066",
    "adult_female": "12724067",
    "pediatric": "12724068"
}
```

## 6. 效能優化

### Cerner API 限制
```python
import time
from functools import wraps

def rate_limit(calls_per_minute=60):
    """實施 API 呼叫頻率限制"""
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = 60.0 / calls_per_minute - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

@rate_limit(calls_per_minute=50)  # 保守的限制
def make_fhir_request(url, headers):
    """受限制的 FHIR API 請求"""
    return requests.get(url, headers=headers)
```

## 7. 監控與日誌

### Cerner 特定的日誌格式
```python
def log_cerner_interaction(action, resource_type, patient_id, response_time):
    """記錄與 Cerner 的互動"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'vendor': 'cerner',
        'action': action,
        'resource_type': resource_type,
        'patient_id': patient_id,
        'response_time_ms': response_time,
        'app_version': app.config.get('VERSION', 'unknown')
    }
    app.logger.info(json.dumps(log_entry))
```

## 8. 部署檢查清單

- [ ] **Cerner 開發者帳戶已建立**
- [ ] **應用程式已在 Cerner 註冊**
- [ ] **生產環境 Client ID 和 Secret 已獲得**
- [ ] **HTTPS 憑證已配置**
- [ ] **Cerner 特定的 FHIR 擴展已處理**
- [ ] **API 限制已實施**
- [ ] **錯誤處理已針對 Cerner 特性優化**
- [ ] **在 Cerner 沙盒環境中測試完成**
- [ ] **臨床工作流程已驗證**
- [ ] **使用者培訓材料已準備** 