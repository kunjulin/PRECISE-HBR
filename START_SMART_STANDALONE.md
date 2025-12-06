# SMART on FHIR Standalone 啟動指南

## 🚀 快速啟動步驟

### 步驟 1: 獲取 SMART Client ID

#### 使用 SMART Health IT Launcher（推薦）

1. **訪問註冊頁面**:
   ```
   https://launch.smarthealthit.org/register
   ```
   或訪問主頁後點擊右上角的 "Register" 或 "Manage Apps"

2. **註冊新應用**:
   - **App Name**: `PRECISE-HBR` (或任何名稱)
   - **Redirect URI**: `http://localhost:8080/callback` ⚠️ 必須完全匹配
   - **Launch Type**: 選擇 **"Standalone Launch"**
   - **Scopes**: 至少選擇以下權限：
     - `patient/Patient.read`
     - `patient/Observation.read`
     - `patient/Condition.read`
     - `patient/MedicationRequest.read`
     - `patient/Procedure.read`
     - `openid`
     - `profile`
     - `fhirUser`

3. **複製 Client ID**:
   - 註冊成功後，複製生成的 **Client ID**
   - 格式類似：`your-client-id-here-12345`

### 步驟 2: 更新環境變量

打開 `.env` 文件，更新以下配置：

```env
SMART_CLIENT_ID=your-actual-client-id-here  # 替換為步驟1獲取的 Client ID
SMART_REDIRECT_URI=http://localhost:8080/callback
FLASK_SECRET_KEY=dev-local-secret-key-for-docker-testing-only-change-in-production
FLASK_ENV=development
FLASK_DEBUG=true
PORT=8080
```

**重要**: 
- `SMART_CLIENT_ID` 必須是真實的 Client ID，不能是 `your-test-client-id`
- `SMART_REDIRECT_URI` 必須與註冊時設置的完全一致

### 步驟 3: 啟動應用

**Windows:**
```powershell
python start_app.py
```

**或使用批處理文件:**
```powershell
.\start_app.bat
```

應用將在 `http://localhost:8080` 啟動。

### 步驟 4: 訪問 Standalone Launch

1. **打開瀏覽器訪問**:
   ```
   http://localhost:8080/standalone
   ```

2. **選擇 FHIR 服務器**:
   - 點擊預設的 **"SMART Health IT R4 Launcher"** 按鈕
   - 或手動輸入: `https://launch.smarthealthit.org/v/r4/fhir`

3. **點擊 "Launch" 按鈕**

4. **完成 OAuth 授權**:
   - 系統會重定向到 SMART Health IT 授權頁面
   - 登錄測試帳號（或使用提供的測試憑證）
   - 選擇要授權的患者
   - 授予應用所需的權限
   - 系統會自動重定向回應用並完成 token 交換

5. **開始使用應用**:
   - 成功後會自動重定向到主應用頁面 (`/main`)
   - 可以看到患者 ID 和風險計算功能

## ✅ 驗證檢查清單

啟動前請確認：

- [ ] `.env` 文件存在
- [ ] `SMART_CLIENT_ID` 已更新為真實值（不是 `your-test-client-id`）
- [ ] `SMART_REDIRECT_URI` 設置為 `http://localhost:8080/callback`
- [ ] `FLASK_SECRET_KEY` 已設置
- [ ] Python 3.11+ 已安裝
- [ ] 所有依賴已安裝 (`pip install -r requirements.txt`)
- [ ] 端口 8080 未被佔用

## 🐛 常見問題

### 問題 1: "SMART_CLIENT_ID and SMART_REDIRECT_URI must be set"

**解決方案**:
- 檢查 `.env` 文件是否存在
- 確認變量名稱正確（無空格）
- 確認值不為空
- 重啟應用

### 問題 2: "redirect_uri_mismatch"

**錯誤信息**: OAuth 授權時顯示 redirect URI 不匹配

**解決方案**:
- 確認 `.env` 中的 `SMART_REDIRECT_URI` 與註冊時設置的完全一致
- 檢查是否有尾隨斜線（`/callback` vs `/callback/`）
- 確認協議正確（`http://` vs `https://`）
- 在 SMART Health IT 中更新應用的 Redirect URI

### 問題 3: "Configuration Discovery Error"

**原因**: FHIR 服務器不支持 SMART on FHIR

**解決方案**:
- 使用支持 SMART 的服務器（如 SMART Health IT）
- 或使用測試模式（無需 OAuth）

### 問題 4: 應用無法啟動

**檢查**:
1. 端口是否被佔用:
   ```powershell
   netstat -ano | findstr :8080
   ```
2. 依賴是否已安裝:
   ```powershell
   pip install -r requirements.txt
   ```
3. 查看錯誤日誌

## 📝 完整啟動命令序列

```powershell
# 1. 進入項目目錄
cd D:\repos\PRECISEHBR_test

# 2. 檢查環境變量（確認 SMART_CLIENT_ID 已更新）
Get-Content .env | Select-String "SMART_CLIENT_ID"

# 3. 啟動應用
python start_app.py

# 4. 在瀏覽器中訪問
# http://localhost:8080/standalone
```

## 🎯 測試流程

1. **啟動應用** → `python start_app.py`
2. **訪問 Standalone 頁面** → `http://localhost:8080/standalone`
3. **選擇服務器** → SMART Health IT
4. **完成授權** → 登錄並選擇患者
5. **驗證成功** → 看到主應用頁面和患者 ID

## 📚 相關資源

- [SMART Health IT Launcher](https://launch.smarthealthit.org/)
- [SMART on FHIR Documentation](http://hl7.org/fhir/smart-app-launch/)
- [STANDALONE_LAUNCH_GUIDE.md](STANDALONE_LAUNCH_GUIDE.md) - 詳細指南
- [QUICK_START_STANDALONE.md](QUICK_START_STANDALONE.md) - 快速啟動

---

**提示**: 如果只是想快速測試功能而不進行 OAuth，可以使用測試模式：
```
http://localhost:8080/test-mode
```

