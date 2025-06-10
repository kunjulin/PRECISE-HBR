# FHIR Client Migration Guide

## 概述

本指南說明如何從原本的 `requests` 基礎實現遷移到使用 `fhirclient` 庫，以便在 Cerner 沙盒環境中進行測試。

## 🔄 主要變更

### 1. 依賴庫變更
- **移除**: `requests` 和 `concurrent.futures` 直接調用
- **新增**: `fhirclient` 庫的使用
- **保持**: 現有的 `requirements.txt` 已包含 `fhirclient>=4.3.1`

### 2. 數據獲取方式
- **之前**: 直接使用 `requests.get()` 調用 FHIR API
- **現在**: 使用 `fhirclient` 的資源模型和搜索方法
- **優勢**: 更好的類型安全性、自動序列化/反序列化、更好的錯誤處理

### 3. Cerner 沙盒支援
- **新增**: `/launch/cerner-sandbox` 路由用於直接測試
- **優化**: Cerner 特定的端點配置
- **改進**: 更好的錯誤處理和日誌記錄

## 🧪 測試步驟

### 1. 運行連接測試
```bash
python test_fhirclient_connection.py
```

這個測試會驗證：
- FHIR 客戶端初始化
- 服務器元數據獲取
- 患者數據獲取
- 搜索參數功能

### 2. 配置 Cerner 沙盒
1. 複製 `cerner_sandbox.env` 到 `.env`
2. 在 [Cerner Developer Portal](https://code.cerner.com/developer/smart-on-fhir/apps) 註冊您的應用
3. 更新 `SMART_CLIENT_ID` 為您的客戶端 ID
4. 確保 `SMART_REDIRECT_URI` 與註冊的完全一致

### 3. 啟動應用測試
```bash
# 啟動 Flask 應用
python APP.py

# 或使用 gunicorn
gunicorn -w 1 -b 0.0.0.0:5000 APP:app
```

### 4. 測試 URL
- **直接沙盒啟動**: `http://localhost:5000/launch/cerner-sandbox`
- **標準 SMART 啟動**: `http://localhost:5000/launch?iss=https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d`

## 📋 代碼對比

### 舊的 requests 方式
```python
# 舊代碼示例
response = requests.get(
    f"{fhir_server_url}/Patient/{patient_id}",
    headers={"Authorization": f"Bearer {access_token}"}
)
patient_data = response.json()
```

### 新的 fhirclient 方式
```python
# 新代碼示例
from fhirclient import client
from fhirclient.models import patient

smart = client.FHIRClient(settings=settings)
patient_resource = patient.Patient.read(patient_id, smart.server)
patient_data = patient_resource.as_json()
```

## 🔧 主要功能改進

### 1. 類型安全
- fhirclient 提供強類型的 FHIR 資源模型
- 自動驗證和錯誤檢查
- 更好的 IDE 支援和自動完成

### 2. 搜索功能
```python
# 搜索觀察值
observations = observation.Observation.where({
    'patient': patient_id,
    'code': '33914-3',  # eGFR LOINC code
    '_sort': '-date',
    '_count': '1'
}).perform(smart.server)
```

### 3. 錯誤處理
- 更細粒度的異常處理
- 自動重試機制
- 更好的日誌記錄

## 🏥 Cerner 沙盒測試數據

### 測試患者 ID
- `12724066` - 主要測試患者，有豐富的測試數據
- `12724065` - 次要測試患者
- `12742400` - 第三個測試患者

### 可用的測試數據
- **觀察值**: 血紅蛋白、肌酐、血小板、eGFR
- **條件**: 各種疾病狀態
- **藥物**: 抗凝劑、NSAID 等
- **程序**: 輸血記錄等

## 🚀 部署注意事項

### 1. 環境變數
確保在生產環境中設置正確的環境變數：
```bash
SMART_CLIENT_ID=your-production-client-id
SMART_REDIRECT_URI=https://your-domain.com/callback
FLASK_SECRET_KEY=your-secure-secret-key
```

### 2. HTTPS 需求
- 生產環境必須使用 HTTPS
- Cerner 要求所有 OAuth 流程使用安全連接

### 3. 會話管理
- 使用服務器端會話存儲
- 確保會話安全性

## 🐛 常見問題解決

### 1. 授權失敗
- 檢查客戶端 ID 是否正確
- 確保重定向 URI 完全匹配
- 驗證 scopes 是否正確

### 2. 數據獲取失敗
- 檢查訪問令牌是否有效
- 確認患者 ID 存在
- 驗證 FHIR 服務器 URL

### 3. 搜索無結果
- 檢查 LOINC 代碼是否正確
- 確認搜索參數格式
- 驗證患者是否有對應數據

## 📚 相關資源

- [fhirclient 文檔](https://github.com/smart-on-fhir/client-py)
- [Cerner FHIR 文檔](https://fhir.cerner.com/)
- [SMART on FHIR 規範](http://hl7.org/fhir/smart-app-launch/)
- [Cerner 開發者門戶](https://code.cerner.com/)

## ✅ 遷移檢查清單

- [ ] 安裝 fhirclient 依賴
- [ ] 更新 fhir_data_service.py
- [ ] 配置 Cerner 沙盒設置
- [ ] 運行連接測試
- [ ] 測試患者數據獲取
- [ ] 驗證風險計算功能
- [ ] 測試完整的 SMART 授權流程
- [ ] 確認生產環境配置

---

如有任何問題或需要進一步協助，請參考日誌文件或聯繫開發團隊。 