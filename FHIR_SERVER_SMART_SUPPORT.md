# FHIR 服務器 SMART on FHIR 支持問題解決指南

## 🔍 問題說明

當您嘗試使用 Standalone Launch 連接到 FHIR 服務器時，如果遇到 "Configuration Discovery Error"，這通常意味著：

1. **服務器不支持 SMART on FHIR** - 服務器沒有實現 SMART 配置發現端點
2. **服務器配置不完整** - 服務器支持 FHIR 但不支持 SMART 認證流程
3. **網絡問題** - 無法訪問服務器的配置端點

## ✅ 您的當前情況

根據您的描述：
- ✅ **可以通過 `/test-patients` 訪問** - 說明 FHIR 服務器本身是可用的
- ❌ **Standalone Launch 失敗** - 說明服務器不支持 SMART on FHIR 配置發現

**服務器**: 請在 `.env` 文件中配置 `DEFAULT_FHIR_SERVER`
- 這通常是內部/本地 FHIR 服務器
- 支持標準 FHIR R4 API（可以獲取患者數據）
- 可能不支持 SMART on FHIR 配置發現（無法進行 OAuth 授權）

## 🎯 解決方案

### 方案 1: 使用測試模式（推薦，無需 OAuth）

對於不支持 SMART 的服務器，您可以直接使用測試模式：

#### 選項 A: 通過測試患者列表頁面

1. **訪問測試患者頁面**:
   ```
   http://localhost:8080/test-patients
   ```
   
   或指定服務器：
   ```
   http://localhost:8080/test-patients?server=YOUR_FHIR_SERVER_URL
   ```

2. **選擇患者**:
   - 從列表中選擇一個患者，或
   - 直接輸入 Patient ID（如：`0322400H12092976400000000000000`）

3. **開始測試**:
   - 點擊「使用此患者測試」按鈕
   - 應用會直接載入患者數據（無需 OAuth）

#### 選項 B: 直接使用測試模式

訪問以下 URL（替換 `YOUR_FHIR_SERVER_URL` 和 `PATIENT_ID` 為實際值）:
```
http://localhost:8080/test-mode?server=YOUR_FHIR_SERVER_URL&patient_id=PATIENT_ID
```

**注意**: 如果不指定參數，將使用 `.env` 文件中配置的 `DEFAULT_FHIR_SERVER` 和 `DEFAULT_TEST_PATIENT_ID`。

### 方案 2: 使用支持 SMART 的公開服務器

如果您需要測試完整的 Standalone Launch（包括 OAuth 流程），請使用支持 SMART on FHIR 的服務器：

#### SMART Health IT Launcher（推薦）

1. **訪問 Standalone Launch 頁面**:
   ```
   http://localhost:8080/standalone
   ```

2. **選擇 SMART Health IT**:
   - 點擊預設的 "SMART Health IT R4 Launcher" 按鈕
   - 或手動輸入: `https://launch.smarthealthit.org/v/r4/fhir`

3. **完成 OAuth 授權**:
   - 登錄測試帳號
   - 選擇患者
   - 授予權限

### 方案 3: 配置服務器支持 SMART（需要服務器管理員）

如果您的 FHIR 服務器需要支持 SMART on FHIR，需要：

1. **實現 SMART 配置發現端點**:
   ```
   GET /.well-known/smart-configuration
   ```
   應返回包含以下字段的 JSON：
   ```json
   {
     "authorization_endpoint": "https://.../authorize",
     "token_endpoint": "https://.../token",
     "capabilities": ["launch-standalone", "client-confidential-symmetric"]
   }
   ```

2. **實現 OAuth 2.0 授權流程**:
   - Authorization endpoint
   - Token endpoint
   - 支持 PKCE（Proof Key for Code Exchange）

3. **在 FHIR Metadata 中聲明 SMART 支持**:
   - 在 CapabilityStatement 中添加 OAuth URIs extension

## 📊 服務器類型對比

| 服務器類型 | FHIR API | SMART 支持 | 適用場景 |
|-----------|---------|-----------|---------|
| **標準 FHIR 服務器** | ✅ | ❌ | 數據獲取、測試模式 |
| **SMART on FHIR 服務器** | ✅ | ✅ | Standalone Launch、完整 OAuth |
| **您的服務器** | ✅ | ❌ | 測試模式、數據獲取 |

## 🔧 改進的錯誤處理

應用已更新，當檢測到不支持 SMART 的服務器時，會提供：

1. **清晰的錯誤說明** - 解釋為什麼無法發現配置
2. **針對性建議** - 根據服務器類型提供不同的解決方案
3. **快速訪問鏈接** - 直接引導到測試模式或支持的服務器

## 📝 使用建議

### 對於內部 FHIR 服務器

**推薦工作流程**:

1. **配置預設服務器**（在 `.env` 文件中）:
   ```env
   DEFAULT_FHIR_SERVER=http://your-internal-server/fhir
   DEFAULT_TEST_PATIENT_ID=your-default-patient-id
   ```

2. **開發和測試功能**:
   ```
   http://localhost:8080/test-patients
   ```
   
   或指定服務器：
   ```
   http://localhost:8080/test-patients?server=YOUR_FHIR_SERVER_URL
   ```
   - 無需 OAuth
   - 快速測試
   - 直接訪問患者數據

2. **測試完整 OAuth 流程**:
   ```
   http://localhost:8080/standalone
   ```
   - 使用 SMART Health IT 或其他支持 SMART 的服務器
   - 測試完整的授權流程

## 🆘 故障排除

### 問題: 測試模式可以訪問，但 Standalone Launch 失敗

**原因**: 服務器不支持 SMART on FHIR

**解決方案**: 
- ✅ 使用測試模式進行功能測試
- ✅ 使用支持 SMART 的服務器測試 OAuth 流程

### 問題: 測試模式也無法訪問患者數據

**可能原因**:
- 服務器需要認證（即使是公開端點）
- 網絡連接問題
- 患者 ID 不存在

**解決方案**:
- 檢查服務器是否可訪問
- 確認患者 ID 正確
- 查看應用日誌獲取詳細錯誤信息

## 📚 相關文檔

- [STANDALONE_LAUNCH_GUIDE.md](STANDALONE_LAUNCH_GUIDE.md) - Standalone Launch 完整指南
- [QUICK_START_STANDALONE.md](QUICK_START_STANDALONE.md) - 快速啟動指南
- [FHIR_SERVER_GUIDE.md](FHIR_SERVER_GUIDE.md) - FHIR 服務器配置指南

---

**最後更新**: 2025-01-XX

