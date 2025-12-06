# Standalone Launch 快速啟動指南

## ⚡ 快速開始（3 步驟）

### 步驟 1: 更新 .env 文件

打開 `.env` 文件，確保以下配置正確：

```env
FLASK_SECRET_KEY=dev-local-secret-key-for-docker-testing-only-change-in-production
SMART_CLIENT_ID=your-client-id-here  # ⚠️ 需要更新為真實的 Client ID
SMART_REDIRECT_URI=http://localhost:8080/callback
FLASK_ENV=development
FLASK_DEBUG=true
PORT=8080
```

**重要**: `SMART_CLIENT_ID` 必須是真實的 Client ID，不能是 `your-test-client-id`。

### 步驟 2: 獲取 SMART Client ID（首次使用）

#### 使用 SMART Health IT Launcher（最簡單）

1. 訪問: https://launch.smarthealthit.org/
2. 點擊右上角 **"Register"** 或 **"Manage Apps"**
3. 填寫應用信息：
   ```
   App Name: PRECISE-HBR
   Redirect URI: http://localhost:8080/callback
   Launch Type: Standalone Launch
   Scopes: patient/Patient.read patient/Observation.read patient/Condition.read
   ```
4. 複製 **Client ID**
5. 更新 `.env` 文件中的 `SMART_CLIENT_ID`

### 步驟 3: 啟動應用

**Windows:**
```bash
start_app.bat
```

**或直接運行:**
```bash
python start_app.py
```

應用將在 `http://localhost:8080` 啟動。

## 🎯 使用 Standalone Launch

1. **打開瀏覽器訪問:**
   ```
   http://localhost:8080/standalone
   ```

2. **選擇 FHIR 服務器:**
   - 點擊預設的 "SMART Health IT R4 Launcher" 按鈕，或
   - 手動輸入: `https://launch.smarthealthit.org/v/r4/fhir`

3. **點擊 "Launch" 按鈕**

4. **完成 OAuth 授權:**
   - 登錄測試帳號
   - 選擇患者
   - 授予權限

5. **開始使用應用**

## ✅ 驗證檢查清單

- [ ] `.env` 文件存在且已配置
- [ ] `SMART_CLIENT_ID` 已更新為真實值（不是 `your-test-client-id`）
- [ ] `SMART_REDIRECT_URI` 設置為 `http://localhost:8080/callback`
- [ ] Python 3.11+ 已安裝
- [ ] 依賴已安裝 (`pip install -r requirements.txt`)
- [ ] 端口 8080 未被佔用

## 🐛 常見問題

### "SMART_CLIENT_ID and SMART_REDIRECT_URI must be set"
- ✅ 檢查 `.env` 文件是否存在
- ✅ 確認變量名稱正確（無空格）
- ✅ 確認值不為空

### "redirect_uri_mismatch"
- ✅ 確認 `.env` 中的 `SMART_REDIRECT_URI` 與註冊時完全一致
- ✅ 檢查是否有尾隨斜線
- ✅ 確認使用 `http://`（本地開發）而非 `https://`

### "Configuration Discovery Error"
- ✅ 確認 FHIR 服務器 URL 正確
- ✅ 嘗試訪問: `https://launch.smarthealthit.org/v/r4/fhir/.well-known/smart-configuration`
- ✅ 檢查網絡連接

## 📚 更多信息

詳細指南請參考: [STANDALONE_LAUNCH_GUIDE.md](STANDALONE_LAUNCH_GUIDE.md)

---

**提示**: 如果只是想快速測試功能而不進行 OAuth，可以使用測試模式：
```
http://localhost:8080/test-mode
```


