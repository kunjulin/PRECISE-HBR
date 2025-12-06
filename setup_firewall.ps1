# 防火牆設置腳本 - 需要管理員權限
# 使用方法: 以管理員身份運行 PowerShell，然後執行: .\setup_firewall.ps1

Write-Host "========================================"
Write-Host "PRECISE-HBR 防火牆設置"
Write-Host "========================================"
Write-Host ""

# 檢查是否以管理員身份運行
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "✗ 錯誤: 此腳本需要管理員權限" -ForegroundColor Red
    Write-Host ""
    Write-Host "請以管理員身份運行 PowerShell:"
    Write-Host "  1. 右鍵點擊 PowerShell"
    Write-Host "  2. 選擇「以系統管理員身分執行」"
    Write-Host "  3. 然後運行: .\setup_firewall.ps1"
    Write-Host ""
    exit 1
}

Write-Host "✓ 檢測到管理員權限" -ForegroundColor Green
Write-Host ""

# 檢查現有規則
$existingRule = Get-NetFirewallRule -DisplayName "PRECISE-HBR Port 8080" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "找到現有規則，正在更新..."
    Set-NetFirewallRule -DisplayName "PRECISE-HBR Port 8080" -Enabled True
    Write-Host "✓ 防火牆規則已啟用" -ForegroundColor Green
} else {
    Write-Host "正在創建新的防火牆規則..."
    try {
        $rule = New-NetFirewallRule `
            -DisplayName "PRECISE-HBR Port 8080" `
            -Description "允許 PRECISE-HBR SMART on FHIR 應用的網絡訪問" `
            -Direction Inbound `
            -LocalPort 8080 `
            -Protocol TCP `
            -Action Allow `
            -Enabled True
        
        Write-Host "✓ 防火牆規則已成功創建" -ForegroundColor Green
        Write-Host "  規則名稱: $($rule.DisplayName)"
        Write-Host "  端口: 8080"
        Write-Host "  協議: TCP"
        Write-Host "  操作: Allow"
        Write-Host "  狀態: Enabled"
    } catch {
        Write-Host "✗ 創建防火牆規則失敗: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "設置完成！"
Write-Host "========================================"
Write-Host ""
Write-Host "現在其他電腦可以通過以下地址訪問:"
Write-Host "  http://10.30.68.163:8080/"
Write-Host ""
Write-Host "注意: 如果 IP 地址改變，請重新檢查網絡配置"
Write-Host ""

