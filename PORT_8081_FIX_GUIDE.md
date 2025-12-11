# Port 8081 配置修復指南

## 發現的問題

1. ✅ `.env` 檔案已更新為 port 8081
2. ❌ 應用程式只綁定到 `127.0.0.1`（僅本地訪問）
3. ❌ 防火牆規則不存在

## 解決步驟

### 步驟 1: 停止當前運行的應用程式

如果應用程式正在運行，請按 `Ctrl+C` 停止它。

### 步驟 2: 開啟防火牆 Port 8081

**以管理員身份打開 PowerShell**，然後執行：

```powershell
New-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -Description "Allow PRECISE-HBR App Network Access" -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow -Enabled True
```

或者執行腳本：
```powershell
.\open_port_8081_simple.ps1
```

### 步驟 3: 重新啟動應用程式（啟用網絡訪問）

**重要：** 必須使用 `--network` 參數啟動，才能從其他電腦訪問：

```powershell
python start_app.py --network
```

或者設置環境變數：
```powershell
$env:ALLOW_NETWORK_ACCESS="true"
python start_app.py
```

### 步驟 4: 驗證配置

執行檢查腳本：
```powershell
.\check_port_8081.ps1
```

應該看到：
- Port 8081 綁定到 `0.0.0.0`（不是 `127.0.0.1`）
- 防火牆規則已啟用

### 步驟 5: 測試訪問

從其他電腦訪問：
```
http://YOUR_IP_ADDRESS:8081/
```

查找您的 IP 地址：
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" }
```

## 常見問題

### Q: 為什麼應用程式只綁定到 127.0.0.1？

A: 這是安全原因，預設只允許本地訪問。要允許網絡訪問，必須使用 `--network` 參數啟動。

### Q: 防火牆規則已創建但仍無法訪問？

A: 確保：
1. 應用程式綁定到 `0.0.0.0`（使用 `--network` 啟動）
2. 防火牆規則已啟用
3. 兩台電腦在同一網絡
4. 沒有其他防火牆軟件阻擋

### Q: 如何確認應用程式正確綁定？

A: 執行：
```powershell
Get-NetTCPConnection -LocalPort 8081 | Select-Object LocalAddress, LocalPort, State
```

應該看到 `LocalAddress` 為 `0.0.0.0`，而不是 `127.0.0.1`。


