# Standalone Launch 運行指南

本指南將幫助您設置並運行 PRECISE-HBR 應用的 Standalone Launch 版本。

## 📋 前置要求

1. Python 3.11+ 已安裝
2. 所有依賴已安裝 (`pip install -r requirements.txt`)
3. `.env` 文件已配置

## 🔧 步驟 1: 配置環境變量

### 1.1 檢查 .env 文件

確保您的 `.env` 文件包含以下必要配置：

```env
# Flask 應用密鑰（必須）
FLASK_SECRET_KEY=dev-local-secret-key-for-docker-testing-only-change-in-production

# SMART on FHIR 配置（必須）
SMART_CLIENT_ID=your-client-id-here
SMART_REDIRECT_URI=http://localhost:8080/callback

# 可選配置
SMART_CLIENT_SECRET=  # Standalone launch 通常不需要（公共客戶端）
FLASK_ENV=development
FLASK_DEBUG=true
PORT=8080
```

### 1.2 獲取 SMART Client ID

#### 選項 A: 使用 SMART Health IT Launcher（推薦測試）

1. 訪問 [SMART Health IT Launcher](https://launch.smarthealthit.org/)
2. 點擊右上角的 **"Register"** 或 **"Manage Apps"**
3. 註冊一個新的應用：
   - **App Name**: PRECISE-HBR (或任何名稱)
   - **Redirect URI**: `http://localhost:8080/callback`
   - **Launch Type**: 選擇 **"Standalone Launch"**
   - **Scopes**: 選擇您需要的權限（至少需要 `patient/Patient.read`, `patient/Observation.read` 等）
4. 複製生成的 **Client ID**
5. 將 Client ID 更新到 `.env` 文件中的 `SMART_CLIENT_ID`

#### 選項 B: 使用其他 FHIR 服務器

如果您使用其他 FHIR 服務器（如 Cerner、Epic 等），請：
1. 在該服務器的開發者門戶註冊應用
2. 獲取 Client ID
3. 確保 Redirect URI 設置為 `http://localhost:8080/callback`
4. 更新 `.env` 文件

## 🚀 步驟 2: 啟動應用

### 方法 1: 使用啟動腳本（推薦）

**Windows:**
```bash
start_app.bat
```

**Linux/Mac:**
```bash
python start_app.py
```

### 方法 2: 直接運行 Python

```bash
python APP.py
```

### 方法 3: 使用 Docker Compose

```bash
docker-compose up -d --build
```

應用將在 `http://localhost:8080` 上運行。

## 🎯 步驟 3: 訪問 Standalone Launch

### 3.1 打開 Standalone Launch 頁面

在瀏覽器中訪問：
```
http://localhost:8080/standalone
```

### 3.2 選擇或輸入 FHIR 服務器

頁面會顯示：

1. **快速測試模式選項**：
   - 點擊 "進入測試模式" 可跳過 OAuth（僅開發測試）
   - 點擊 "選擇測試患者" 查看可用患者列表

2. **預設服務器按鈕**：
   - **SMART Health IT R4 Launcher**: `https://launch.smarthealthit.org/v/r4/fhir`
   - 點擊按鈕自動填入 URL

3. **手動輸入**：
   - 在輸入框中輸入您的 FHIR 服務器 URL（ISS）
   - 例如：`https://launch.smarthealthit.org/v/r4/fhir`

### 3.3 啟動應用

1. 點擊 "Launch" 按鈕
2. 系統會：
   - 自動發現 FHIR 服務器的 SMART 配置
   - 生成 PKCE 參數（code_verifier 和 code_challenge）
   - 重定向到授權服務器進行 OAuth 登錄

### 3.4 完成授權

1. 在授權頁面登錄（使用測試帳號）
2. 選擇要授權的患者（如果適用）
3. 授予應用所需的權限
4. 系統會自動重定向回應用並完成 token 交換

## ✅ 步驟 4: 驗證成功

成功後，您應該：
- 被重定向到主應用頁面 (`/main`)
- 看到患者 ID 顯示在頁面上
- 可以開始使用風險計算功能

## 🔍 故障排除

### 問題 1: "SMART_CLIENT_ID and SMART_REDIRECT_URI must be set"

**解決方案：**
- 檢查 `.env` 文件是否存在
- 確認 `SMART_CLIENT_ID` 和 `SMART_REDIRECT_URI` 已設置
- 確保 `.env` 文件在項目根目錄

### 問題 2: "Configuration Discovery Error"

**可能原因：**
- FHIR 服務器 URL 不正確
- 服務器不支持 SMART on FHIR
- 網絡連接問題

**解決方案：**
- 確認 FHIR 服務器 URL 正確（應以 `/fhir` 或 `/r4/fhir` 結尾）
- 嘗試訪問服務器的 `.well-known/smart-configuration` 端點
- 檢查防火牆設置

### 問題 3: "State parameter mismatch"

**解決方案：**
- 清除瀏覽器 cookies 和 session
- 重新啟動應用
- 確保沒有多個瀏覽器標籤同時進行授權

### 問題 4: "PKCE parameter validation failed"

**解決方案：**
- 確保 session 存儲正常工作
- 檢查 `instance/flask_session` 目錄權限
- 重新啟動應用

### 問題 5: Redirect URI 不匹配

**錯誤信息：** "redirect_uri_mismatch"

**解決方案：**
- 確認 `.env` 中的 `SMART_REDIRECT_URI` 與註冊應用時設置的完全一致
- 檢查是否有尾隨斜線差異（`/callback` vs `/callback/`）
- 確認協議正確（`http://` vs `https://`）

## 📝 Standalone Launch vs EHR Launch

| 特性 | Standalone Launch | EHR Launch |
|------|------------------|------------|
| Launch Token | ❌ 不需要 | ✅ 需要 |
| Launch Scope | ❌ 自動移除 | ✅ 包含 |
| 患者選擇 | ✅ 用戶選擇 | ✅ EHR 提供 |
| 使用場景 | 獨立應用 | EHR 內嵌應用 |

## 🔐 安全注意事項

1. **開發環境**：
   - `FLASK_SECRET_KEY` 僅用於開發測試
   - 生產環境必須使用強隨機密鑰

2. **Client Secret**：
   - Standalone launch 通常使用公共客戶端（無 Client Secret）
   - 如果使用機密客戶端，請妥善保管 Client Secret

3. **HTTPS**：
   - 生產環境必須使用 HTTPS
   - 本地開發可以使用 HTTP

## 📚 相關資源

- [SMART Health IT Launcher](https://launch.smarthealthit.org/)
- [SMART on FHIR Documentation](http://hl7.org/fhir/smart-app-launch/)
- [FHIR R4 Specification](http://hl7.org/fhir/R4/)
- [README_TEST_VERSION.md](README_TEST_VERSION.md) - 測試版本說明

## 🆘 獲取幫助

如果遇到問題：
1. 檢查應用日誌輸出
2. 查看瀏覽器控制台的錯誤信息
3. 確認所有環境變量正確設置
4. 參考 [README_TEST_VERSION.md](README_TEST_VERSION.md) 了解更多信息

---

**最後更新**: 2025-01-XX
**版本**: Standalone Launch v1.0


