# PRECISE-DAPT SMART on FHIR 應用程式
## Google Cloud Platform 部署指南 - SMART-LU 專案

### 📋 概述
此指南將協助您將 PRECISE-DAPT 出血風險評估應用程式部署到 Google Cloud Platform 的 SMART-LU 專案。

### 🛠️ 前置需求

#### 1. Google Cloud 帳戶設置
- 確保您有 Google Cloud Platform 帳戶
- 已創建或有權限訪問 `smart-lu` 專案
- 安裝 Google Cloud CLI ([安裝指南](https://cloud.google.com/sdk/docs/install))

#### 2. 權限檢查
確保您的帳戶在 SMART-LU 專案中具有以下權限：
- App Engine Admin
- Cloud Build Editor
- Service Account User
- Project Editor (或更高權限)

#### 3. 本地環境
- Python 3.11 或更高版本
- Git (用於版本控制)

### 🚀 部署步驟

#### 步驟 1: 準備配置
1. **更新 SMART 客戶端 ID**
   ```bash
   # 編輯 app.yaml
   nano app.yaml
   ```
   更新以下值：
   ```yaml
   SMART_CLIENT_ID: your-actual-client-id-here
   FLASK_SECRET_KEY: your-secure-random-key-here
   ```

2. **生成安全的 Flask Secret Key**
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

#### 步驟 2: 登入並設置 Google Cloud
```bash
# 登入 Google Cloud
gcloud auth login

# 設置專案
gcloud config set project smart-lu

# 驗證專案設置
gcloud config get-value project
```

#### 步驟 3: 啟用必要的 API
```bash
# 啟用 App Engine API
gcloud services enable appengine.googleapis.com

# 啟用 Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# 啟用 Logging API
gcloud services enable logging.googleapis.com
```

#### 步驟 4: 初始化 App Engine (僅首次需要)
```bash
# 檢查是否已初始化
gcloud app describe

# 如果尚未初始化，執行以下命令
gcloud app create --region=us-central1
```

#### 步驟 5: 部署應用程式

**方法 1: 使用自動化腳本**
```bash
# 給予執行權限
chmod +x deploy.sh

# 執行部署腳本
./deploy.sh
```

**方法 2: 手動部署**
```bash
# 部署到 App Engine
gcloud app deploy app.yaml --project=smart-lu --version=v1

# 查看部署狀態
gcloud app versions list --project=smart-lu
```

### 🔧 部署後配置

#### 1. 獲取應用程式 URL
```bash
gcloud app browse --project=smart-lu --no-launch-browser
```
預期 URL: `https://smart-fhir-app-dot-smart-lu.uc.r.appspot.com`

#### 2. EHR 系統註冊
在您的 EHR 系統（如 Epic、Cerner）中註冊以下信息：
- **App Name**: PRECISE-DAPT Risk Assessment
- **Redirect URI**: `https://smart-fhir-app-dot-smart-lu.uc.r.appspot.com/callback`
- **Launch URI**: `https://smart-fhir-app-dot-smart-lu.uc.r.appspot.com/launch`
- **Scopes**: `launch patient/Patient.read patient/Observation.read patient/Condition.read patient/MedicationRequest.read patient/Procedure.read fhirUser openid profile online_access`

#### 3. 更新應用程式配置
使用從 EHR 獲得的 Client ID 更新 app.yaml：
```bash
# 重新部署更新的配置
gcloud app deploy app.yaml --project=smart-lu --version=v2
```

### 📊 監控和維護

#### 查看應用程式日誌
```bash
# 即時日誌
gcloud app logs tail --project=smart-lu

# 歷史日誌
gcloud app logs read --project=smart-lu --limit=50
```

#### 檢查應用程式狀態
```bash
# 查看版本列表
gcloud app versions list --project=smart-lu

# 查看服務狀態
gcloud app services list --project=smart-lu
```

#### 版本管理
```bash
# 切換到特定版本
gcloud app versions migrate v2 --project=smart-lu

# 停止舊版本（節省成本）
gcloud app versions stop v1 --project=smart-lu

# 刪除舊版本
gcloud app versions delete v1 --project=smart-lu
```

### 🛡️ 安全設置

#### 1. App Engine 防火牆
```bash
# 創建防火牆規則（僅允許 HTTPS）
gcloud app firewall-rules create 100 \
    --source-range="*" \
    --action=allow \
    --description="Allow HTTPS traffic" \
    --project=smart-lu
```

#### 2. 自定義域名（可選）
```bash
# 映射自定義域名
gcloud app domain-mappings create your-domain.com --project=smart-lu
```

### 🧪 測試

#### 1. 基本功能測試
- 訪問: `https://smart-fhir-app-dot-smart-lu.uc.r.appspot.com`
- 測試 Cerner Sandbox: `https://smart-fhir-app-dot-smart-lu.uc.r.appspot.com/launch/cerner-sandbox`

#### 2. SMART on FHIR 測試
使用 SMART App Gallery 或 EHR 測試環境測試完整的 SMART launch 流程。

### 🚨 疑難排解

#### 常見問題

**1. 部署失敗 - 權限錯誤**
```
ERROR: You do not have permission to access project [smart-lu]
```
**解決方案**: 確保您的帳戶有 smart-lu 專案的訪問權限。

**2. App Engine 區域錯誤**
```
ERROR: The region [us-central1] does not support App Engine
```
**解決方案**: 選擇支持的區域，如 `us-east1` 或 `europe-west1`。

**3. 建置失敗 - 依賴項錯誤**
```
ERROR: Could not find a version that satisfies the requirement
```
**解決方案**: 檢查 requirements.txt 中的套件版本相容性。

**4. SMART Launch 失敗**
```
Error: Invalid redirect_uri parameter
```
**解決方案**: 確保在 EHR 系統中註冊的 redirect_uri 與 app.yaml 中的完全一致。

#### 日誌分析
```bash
# 搜尋特定錯誤
gcloud app logs read --project=smart-lu --filter="ERROR"

# 搜尋 FHIR 相關日誌
gcloud app logs read --project=smart-lu --filter="fhir"
```

### 💰 成本管理

#### 自動縮放設置
App Engine 會根據流量自動縮放，但您可以設置限制：
```yaml
# 在 app.yaml 中
automatic_scaling:
  max_instances: 3  # 限制最大實例數
  min_instances: 0  # 最小實例數
```

#### 監控費用
- 定期檢查 [Google Cloud Console](https://console.cloud.google.com) 中的計費報告
- 設置預算警告以控制成本

### 📞 支援

如果遇到問題，可以：
1. 檢查 Google Cloud 文檔
2. 查看應用程式日誌
3. 參考 [SMART on FHIR 規範](http://docs.smarthealthit.org/)
4. 聯繫技術支援團隊

### 📝 部署檢查清單

- [ ] Google Cloud CLI 已安裝
- [ ] 已登入正確的 Google 帳戶
- [ ] smart-lu 專案已設置且有訪問權限
- [ ] app.yaml 中的 SMART_CLIENT_ID 已更新
- [ ] app.yaml 中的 FLASK_SECRET_KEY 已設置
- [ ] App Engine API 已啟用
- [ ] 應用程式已成功部署
- [ ] EHR 系統中已註冊 redirect_uri
- [ ] SMART launch 流程已測試
- [ ] 監控和日誌已設置

---

**最後更新**: {{ date }}
**版本**: PRECISE-DAPT v1.0
**專案**: SMART-LU 