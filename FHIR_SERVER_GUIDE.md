# FHIR 測試服務器指南

## 🌐 推薦的公開測試服務器

### 1. SMART Health IT (最推薦) ⭐⭐⭐⭐⭐
```
https://launch.smarthealthit.org/v/r4/fhir
```
**特點**:
- ✅ 快速穩定
- ✅ 專為 SMART on FHIR 測試設計
- ✅ 支持 standalone launch
- ✅ 不需要預先註冊
- ✅ 豐富的測試患者數據

**用途**: 適合 standalone launch 和測試模式

---

### 2. Logica Sandbox ⭐⭐⭐⭐
```
https://r4.smarthealthit.org
```
**特點**:
- ✅ 穩定可靠
- ✅ 標準 FHIR R4 實現
- ✅ 公開訪問
- ✅ 良好的測試數據

**用途**: 適合測試 FHIR 資源獲取

---

### 3. HAPI FHIR Test Server ⭐⭐⭐
```
https://hapi.fhir.org/baseR4
```
**特點**:
- ✅ 開源 HAPI FHIR 參考實現
- ✅ 公開訪問
- ⚠️ 有時響應較慢
- ⚠️ 數據可能被其他用戶修改

**用途**: 適合測試基本 FHIR 功能

---

### ❌ 不推薦的服務器

#### Inferno Reference Server
```
https://inferno.healthit.gov/reference-server/r4
```
**問題**:
- ❌ 響應非常慢（經常超時）
- ❌ 不適合開發測試
- ℹ️ 主要用於 ONC 認證測試

**替代方案**: 使用 SMART Health IT 或 Logica

---

## 🔧 已應用的修復

### 增加超時時間
所有 FHIR 服務器請求的超時時間已從 **10 秒** 增加到 **30 秒**。

**修改的文件**:
- `smart_auth.py` - SMART 配置發現超時
- `views.py` - 患者列表獲取超時
- `fhir_data_service.py` - FHIR 數據獲取超時（90秒）

---

## 🚀 快速開始

### 方法 1: 使用快速按鈕
1. 訪問 `http://localhost:8080/test-patients`
2. 點擊預設服務器按鈕：
   - **SMART Health IT** (推薦)
   - **Logica Sandbox**
   - **HAPI FHIR**
3. 系統會自動載入該服務器的患者列表

### 方法 2: 手動輸入
1. 訪問 `http://localhost:8080/test-patients`
2. 在輸入框中輸入服務器 URL
3. 點擊「載入患者」

---

## 🐛 常見錯誤和解決方案

### 錯誤 1: Read Timeout
```
HTTPSConnectionPool: Read timed out
```

**原因**: 服務器響應太慢

**解決方案**:
1. ✅ 切換到更快的服務器（SMART Health IT）
2. ✅ 等待更長時間（已增加超時）
3. ✅ 檢查網絡連接

---

### 錯誤 2: Configuration Discovery Error
```
Failed to fetch from .well-known: ...
```

**原因**: 
- 服務器不支持 SMART on FHIR
- 服務器不可用

**解決方案**:
- ✅ 用於測試模式時，這個錯誤可以忽略
- ✅ 用於 standalone launch 時，切換到支持 SMART 的服務器

---

### 錯誤 3: 401 Unauthorized / 403 Forbidden
```
Authentication failed / Permission denied
```

**原因**: 服務器需要認證

**解決方案**:
- ✅ 使用完整的 standalone launch (`/standalone`)
- ✅ 使用不需要認證的公開服務器
- ✅ 確保使用測試模式訪問公開端點

---

### 錯誤 4: 404 Not Found
```
Patient not found / Resource not found
```

**原因**: 
- 患者 ID 不存在
- 服務器 URL 錯誤

**解決方案**:
- ✅ 從 `/test-patients` 選擇有效的患者
- ✅ 檢查服務器 URL 是否正確（包含 `/r4` 或 `/fhir`）

---

## 📊 服務器比較表

| 服務器 | 速度 | 穩定性 | SMART支持 | 推薦度 | 用途 |
|--------|------|--------|-----------|--------|------|
| **SMART Health IT** | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐⭐ | Standalone Launch & 測試 |
| **Logica Sandbox** | ⚡⚡ | ⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐ | FHIR 資源測試 |
| **HAPI FHIR** | ⚡ | ⭐⭐⭐ | ⚠️ | ⭐⭐⭐ | 基本功能測試 |
| **Inferno** | 🐌 | ⭐ | ✅ | ❌ | 不推薦日常使用 |

---

## 🔍 檢查服務器狀態

### 測試 SMART 配置
```bash
curl -H "Accept: application/json" \
  https://launch.smarthealthit.org/v/r4/fhir/.well-known/smart-configuration
```

**預期輸出**:
```json
{
  "authorization_endpoint": "https://...",
  "token_endpoint": "https://...",
  "capabilities": [...]
}
```

### 測試患者端點
```bash
curl -H "Accept: application/fhir+json" \
  "https://launch.smarthealthit.org/v/r4/fhir/Patient?_count=5"
```

**預期輸出**:
```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "entry": [...]
}
```

---

## 💡 最佳實踐

### 開發測試
1. **首選**: SMART Health IT (`launch.smarthealthit.org`)
2. **備選**: Logica Sandbox (`r4.smarthealthit.org`)

### Standalone Launch 測試
1. **首選**: SMART Health IT
2. 確保 redirect_uri 正確配置
3. 使用公共客戶端模式（無需 client_secret）

### 性能測試
1. 使用本地 HAPI FHIR 服務器
2. 或使用專用的測試環境

---

## 📝 設置自己的測試服務器

### 使用 Docker 運行 HAPI FHIR
```bash
docker run -p 8081:8080 hapiproject/hapi:latest
```

訪問: `http://localhost:8081/fhir`

### 優點
- ✅ 完全控制
- ✅ 快速響應
- ✅ 不受網絡影響
- ✅ 可以自定義測試數據

---

## 🔗 相關資源

- [SMART Health IT Launcher](https://launch.smarthealthit.org/)
- [SMART App Gallery](https://apps.smarthealthit.org/)
- [FHIR R4 Specification](http://hl7.org/fhir/R4/)
- [HAPI FHIR Documentation](https://hapifhir.io/)
- [Logica Sandbox](https://www.logicahealth.org/solutions/fhir-sandbox/)

---

## 🆘 獲取幫助

如果仍然遇到問題：

1. **檢查日誌**: `docker logs -f smart_fhir_app`
2. **查看網絡**: 確保可以訪問 HTTPS 網站
3. **測試連接**: 使用 curl 測試服務器
4. **提交 Issue**: 在 GitHub 上報告問題

---

**最後更新**: 2025-11-11  
**修復版本**: v1.1 (增加超時時間)

