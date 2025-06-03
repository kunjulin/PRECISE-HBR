# FHIR 客戶端庫建議 - Oracle Health 兼容性

## 概述
根據 Oracle Health 文檔，建議使用以下 FHIR 客戶端庫來確保與 PowerChart 和 MPages 的兼容性。

## 🟢 推薦的 JavaScript 庫

### 1. fhir-client (官方推薦)
```javascript
// 版本要求：v0.1.10 或更高版本
// 修復了 sessionStorage 患者安全問題
import FHIR from 'fhir-client';

// 初始化客戶端
FHIR.oauth2.authorize({
    client_id: 'your-client-id',
    scope: 'launch/patient openid fhirUser patient/*.read',
    redirect_uri: 'your-redirect-uri',
    iss: 'https://fhir-server-url'
});
```

**Oracle Health 特別注意事項**:
- 必須使用 v0.1.10+ 版本
- 需要額外的補丁代碼（見下方）
- 避免使用 `sessionStorage` 在 PowerChart 環境中

### 2. 補丁代碼 (必需)
```javascript
// Oracle Health 要求的額外補丁代碼
// 解決已知的 sessionStorage 問題
(function() {
    if (window.SMART_EMBEDDED && window.sessionStorage) {
        // 為 PowerChart 環境創建替代存儲
        var embeddedStorage = {};
        
        var originalGetItem = window.sessionStorage.getItem;
        var originalSetItem = window.sessionStorage.setItem;
        var originalRemoveItem = window.sessionStorage.removeItem;
        
        window.sessionStorage.getItem = function(key) {
            if (window.SMART_EMBEDDED) {
                return embeddedStorage[key] || null;
            }
            return originalGetItem.call(this, key);
        };
        
        window.sessionStorage.setItem = function(key, value) {
            if (window.SMART_EMBEDDED) {
                embeddedStorage[key] = value;
                return;
            }
            return originalSetItem.call(this, key, value);
        };
        
        window.sessionStorage.removeItem = function(key) {
            if (window.SMART_EMBEDDED) {
                delete embeddedStorage[key];
                return;
            }
            return originalRemoveItem.call(this, key);
        };
    }
})();
```

## 🔧 其他語言的 FHIR 客戶端

### Java - HAPI FHIR
```xml
<dependency>
    <groupId>ca.uhn.hapi.fhir</groupId>
    <artifactId>hapi-fhir-client</artifactId>
    <version>6.0.0</version>
</dependency>
```

### .NET - Firely SDK
```xml
<PackageReference Include="Hl7.Fhir.R4" Version="3.0.0" />
<PackageReference Include="Hl7.FhirPath" Version="3.0.0" />
```

### Python - smart-on-fhir/client-py
```python
from fhirclient import client
from fhirclient.models import patient

# 配置客戶端
settings = {
    'app_id': 'your-app-id',
    'api_base': 'https://fhir-server-url/fhir',
    'redirect_uri': 'your-redirect-uri',
}

smart = client.FHIRClient(settings=settings)
```

### iOS - Swift-FHIR
```swift
import SMART

let smart = Client(
    baseURL: URL(string: "https://fhir-server-url/fhir")!,
    settings: [
        "client_id": "your-client-id",
        "redirect": "your-redirect-uri"
    ]
)
```

## ⚠️ Oracle Health 特殊考量

### sessionStorage 限制
```javascript
// 避免直接使用 sessionStorage
// ❌ 不要這樣做：
sessionStorage.setItem('patient-id', patientId);

// ✅ 使用替代方案：
if (window.SMART_EMBEDDED) {
    // 使用內存存儲或其他機制
    window.appStorage = window.appStorage || {};
    window.appStorage['patient-id'] = patientId;
} else {
    sessionStorage.setItem('patient-id', patientId);
}
```

### Cookie 處理
```javascript
// 為 Oracle Health iframe 環境設置 cookies
function setCookieForOracle(name, value, days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    
    // Oracle Health Edge 要求
    var sameSite = window.SMART_EMBEDDED ? "; SameSite=None; Secure" : "; SameSite=Lax";
    
    document.cookie = name + "=" + (value || "") + expires + "; path=/" + sameSite;
}
```

### 授權流程調整
```javascript
// 在 PowerChart 嵌入環境中避免新窗口
function handleAuthorization() {
    if (window.SMART_EMBEDDED) {
        // 在同一窗口中處理授權
        FHIR.oauth2.authorize({
            // ... 配置
        });
    } else {
        // 標準流程，可以使用新窗口
        window.open(authUrl, '_blank');
    }
}
```

## 🧪 測試建議

### 開發環境測試
1. 在標準瀏覽器中測試
2. 在 IE10+ 中測試
3. 在 Edge 中測試

### Oracle Health 環境測試
1. **code Console 沙盒**
   ```javascript
   // 測試用配置
   const testConfig = {
       iss: 'https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d',
       client_id: 'your-test-client-id'
   };
   ```

2. **PowerChart 測試**
   - 驗證嵌入式行為
   - 測試 cookie 功能
   - 確認 sessionStorage 替代方案

## 📚 相關資源

- [Oracle Health FHIR 文檔](https://docs.oracle.com/en/industries/health/millennium-platform-apis/)
- [SMART on FHIR JavaScript Client](https://github.com/smart-on-fhir/client-js)
- [Cerner SMART Embeddable Library](https://github.com/cerner/smart-embeddable-lib)
- [HAPI FHIR 文檔](https://hapifhir.io/)

## ✅ 檢查清單

### JavaScript 客戶端
- [ ] 使用 fhir-client v0.1.10+
- [ ] 添加 Oracle Health 補丁代碼
- [ ] 實現 sessionStorage 替代方案
- [ ] 配置適當的 cookie 設置
- [ ] 測試嵌入式環境行為

### 其他語言客戶端
- [ ] 選擇兼容的 FHIR 庫版本
- [ ] 實現適當的會話管理
- [ ] 配置 HTTP 客戶端設置
- [ ] 測試授權流程

---

*定期更新以反映 Oracle Health 和 FHIR 客戶端庫的最新要求。* 