# 防火牆設置指南

## 問題說明

如果從其他電腦無法訪問 SMART 應用（出現 `ERR_CONNECTION_REFUSED`），通常是因為 Windows 防火牆阻止了端口 8080 的入站連接。

## 解決方法

### 方法 1: 使用 PowerShell 腳本（推薦）

1. **以管理員身份打開 PowerShell**:
   - 按 `Win + X`
   - 選擇「Windows PowerShell (系統管理員)」或「終端機 (系統管理員)」

2. **導航到項目目錄**:
   ```powershell
   cd D:\repos\PRECISEHBR_test
   ```

3. **運行防火牆設置腳本**:
   ```powershell
   .\setup_firewall.ps1
   ```

### 方法 2: 手動添加防火牆規則

1. **打開 Windows Defender 防火牆**:
   - 按 `Win + R`
   - 輸入 `wf.msc` 並按 Enter

2. **創建新規則**:
   - 點擊左側「輸入規則」
   - 點擊右側「新增規則」
   - 選擇「連接埠」→ 下一步
   - 選擇「TCP」和「特定本機連接埠」
   - 輸入 `8080` → 下一步
   - 選擇「允許連線」→ 下一步
   - 勾選所有設定檔（網域、私人、公用）→ 下一步
   - 名稱輸入 `PRECISE-HBR Port 8080` → 完成

### 方法 3: 使用 PowerShell 命令（管理員權限）

在管理員 PowerShell 中執行：

```powershell
New-NetFirewallRule `
    -DisplayName "PRECISE-HBR Port 8080" `
    -Description "允許 PRECISE-HBR SMART on FHIR 應用的網絡訪問" `
    -Direction Inbound `
    -LocalPort 8080 `
    -Protocol TCP `
    -Action Allow `
    -Enabled True
```

## 驗證設置

### 檢查服務狀態

```powershell
# 檢查服務是否監聽 0.0.0.0:8080
Get-NetTCPConnection -LocalPort 8080 -State Listen
```

應該看到 `LocalAddress` 為 `0.0.0.0`。

### 檢查防火牆規則

```powershell
# 檢查防火牆規則是否存在並啟用
Get-NetFirewallRule -DisplayName "PRECISE-HBR Port 8080"
```

### 測試連接

從其他電腦的瀏覽器訪問：
```
http://10.30.68.163:8080/
```

或使用 PowerShell 測試：
```powershell
Invoke-WebRequest -Uri "http://10.30.68.163:8080/" -TimeoutSec 5
```

## 常見問題

### Q: 添加規則後仍然無法連接？

1. **檢查服務是否運行**:
   ```powershell
   Get-NetTCPConnection -LocalPort 8080 -State Listen
   ```

2. **確認服務綁定到 0.0.0.0**:
   - 使用 `python start_app.py --network` 啟動服務
   - 或設置環境變量 `$env:ALLOW_NETWORK_ACCESS="true"`

3. **檢查 IP 地址**:
   ```powershell
   Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" }
   ```

4. **確認兩台電腦在同一網絡**

5. **檢查其他防火牆軟件**（如第三方防毒軟件）

### Q: 如何查看當前 IP 地址？

```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.IPAddress -notlike "127.*" -and 
    $_.IPAddress -notlike "169.254.*" 
} | Select-Object IPAddress, InterfaceAlias
```

### Q: 如何禁用防火牆規則（臨時）？

```powershell
Disable-NetFirewallRule -DisplayName "PRECISE-HBR Port 8080"
```

### Q: 如何刪除防火牆規則？

```powershell
Remove-NetFirewallRule -DisplayName "PRECISE-HBR Port 8080"
```

## 安全建議

1. **僅在開發/測試環境啟用網絡訪問**
2. **生產環境應使用 HTTPS 和適當的身份驗證**
3. **考慮使用 VPN 而不是直接暴露端口**
4. **定期檢查和審計防火牆規則**

## 相關文件

- `start_app.py` - 應用啟動腳本
- `setup_firewall.ps1` - 防火牆設置腳本

