# Oracle Health (Cerner) SMART on FHIR 部署指南

## 概述
本指南專門針對 Oracle Health (原 Cerner) Millennium Platform 的 SMART on FHIR 應用程式部署要求。

## 📋 前置需求

### 1. Oracle Health Developer Program 會員資格
- 必須成為 [Oracle Health Developer Program](https://code.cerner.com) 會員
- 訪問 PowerChart 測試環境需要會員資格

### 2. 應用程式註冊要求
- Oracle Health 必須驗證並註冊每個 SMART 應用程式
- 需要驗證 FHIR 資源使用和操作（READ/WRITE）
- 客戶域級別的授權控制

## 🔧 技術要求

### 瀏覽器支援
- **Internet Explorer**: IE10 最低版本支持
- **Microsoft Edge**: 基於 Chromium 的版本（推薦）
- **嵌入式瀏覽器控制**: IWebBrowser2 (IE) 和 WebView2 (Edge)

### HTML 要求
```html
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <!-- 其他 meta 標籤 -->
</head>
```

### Cookie 和 iframe 兼容性
#### Internet Explorer
```http
P3P: CP="NOI ADM DEV PSAi COM NAV OUR OTRo STP IND DEM"
```

#### Microsoft Edge
```http
Set-Cookie: session=value; SameSite=None; Secure
```

## 🌐 SSL 和網路要求

### SSL 證書要求
- 必須使用有效的 SSL 證書
- 建議使用 [Qualys SSL Labs](https://www.ssllabs.com/ssltest/) 測試，需達到 A 級或更高
- 在沙盒環境中必須使用標準 HTTPS 端口 443

### 網路存取
- **沙盒測試**: 應用程式 URL 必須公開可訪問
- **生產環境**: URL 需從客戶的 Citrix 服務器可訪問
- **端口限制**: 沙盒環境禁用自定義 TCP 端口

## 📱 用戶介面要求

### 響應式設計
- 不針對特定解析度，設計響應式應用程式
- 根據可用螢幕大小調整

### 載入指示器
- 必須包含載入覆蓋層或進度指示器
- 提供良好的用戶體驗

### PowerChart 嵌入式環境
- 檢測嵌入式環境並相應調整行為
- 避免在嵌入模式下打開新視窗
- 使用相同的嵌入式瀏覽器進行授權流程

## 🔐 授權模型

### SMART Scopes
最小要求範圍之一：
- `launch`
- `launch/patient`
- `openid fhirUser`
- `openid profile` (已棄用)

### 無 FHIR 的 SMART
如果不需要 FHIR 數據，仍需要：
- FHIR 服務器用於確定授權服務器位置
- 上述最小範圍之一

## 🚀 部署流程

### 第一階段：code Console 測試
1. 在 [code Console](https://code.cerner.com) 註冊應用程式
2. 在沙盒環境中測試
3. 配置更新有 15 分鐘等待期

### 第二階段：PowerChart 測試
1. 通過 [Code.cerner.com/submit](https://code.cerner.com/submit) 申請 PowerChart 訪問
2. 在生產環境中測試提供者面向的應用程式
3. 驗證嵌入式行為

### 第三階段：患者門戶測試
1. 在 Oracle Health Patient Portal (原 HealtheLife) 中測試
2. 驗證直接面向消費者的應用程式功能

## 📊 MPages 集成

### iframe 嵌入
- 使用 [Cerner SMART Embeddable Library](https://github.com/cerner/smart-embeddable-lib)
- 正確處理 iframe 中的 cookie

### Workflow 和 Summary 視圖
- MPages 9.0+ 必須支持 Edge 瀏覻器
- 對於依賴 IE 的應用程式，建議使用 Edge IE 模式

## 🔍 Well-Known SMART Configuration

檢查 Oracle Health 的 Well-Known SMART 配置：
```
https://[fhir-server]/.well-known/smart_configuration
```

## 📝 開發最佳實踐

### 避免的技術問題
1. **sessionStorage 限制**: 在 PowerChart 中可能不隔離
2. **跨窗口 Cookie**: 嵌入式瀏覽器不共享 cookie
3. **新窗口授權**: 在嵌入模式下避免

### 推薦的技術棧
- HTML5 DOCTYPE
- 支持 IE10+ 和 Edge 的 JavaScript
- 避免使用僅現代瀏覽器支持的功能

## 🛠️ 故障排除

### 常見問題
1. **15 分鐘配置延遲**: 新的或更新的配置需要等待
2. **SSL 等級不足**: 使用 Qualys SSL Labs 驗證
3. **端口問題**: 確保使用標準 HTTPS 端口 443
4. **iframe Cookie**: 確保正確設置 P3P 頭部（IE）或 SameSite（Edge）

### 調試工具
- Oracle Health 沙盒環境
- 瀏覽器開發者工具
- SSL 測試工具

## 📞 支持資源

- [Oracle Health FHIR 文檔](https://docs.oracle.com/en/industries/health/millennium-platform-apis/)
- [Open Developer Experience 論壇](https://forums.oracle.com/ords/apexds/domain/dev-community)
- [SMART on FHIR 規範](https://www.hl7.org/fhir/smart-app-launch/)

## ✅ 部署檢查清單

### 技術檢查
- [ ] HTML5 DOCTYPE 聲明
- [ ] X-UA-Compatible meta 標籤
- [ ] P3P 頭部（IE 兼容性)
- [ ] SameSite=None; Secure cookies（Edge 兼容性）
- [ ] 響應式設計
- [ ] 載入指示器
- [ ] PowerChart 嵌入檢測

### 網路和安全
- [ ] 有效的 SSL 證書（A 級或更高）
- [ ] HTTPS 端口 443
- [ ] 公開可訪問的 URL（沙盒）
- [ ] 適當的 CORS 設置

### 測試階段
- [ ] code Console 沙盒測試
- [ ] PowerChart 環境測試
- [ ] 患者門戶測試（如適用）
- [ ] MPages 集成測試（如適用）

### 註冊和合規性
- [ ] Oracle Health Developer Program 會員
- [ ] 應用程式在 Oracle Health 註冊
- [ ] FHIR 資源使用驗證
- [ ] 客戶授權配置

---

*此指南基於 Oracle Health SMART Developer Overview 文檔創建，定期更新以反映最新要求。* 