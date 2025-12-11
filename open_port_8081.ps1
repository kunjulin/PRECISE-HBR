# 開啟防火牆 Port 8081
# 需要管理員權限

# 檢查管理員權限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "需要管理員權限！" -ForegroundColor Red
    Write-Host "請以管理員身份運行 PowerShell，然後執行此腳本" -ForegroundColor Yellow
    exit 1
}

Write-Host "正在檢查防火牆規則..." -ForegroundColor Yellow

# 檢查現有規則
$existingRule = Get-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "找到現有規則，正在啟用..." -ForegroundColor Yellow
    Set-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -Enabled True
    Write-Host "防火牆規則已啟用 (port 8081)" -ForegroundColor Green
} else {
    Write-Host "正在創建新的防火牆規則..." -ForegroundColor Yellow
    try {
        $rule = New-NetFirewallRule `
            -DisplayName "PRECISE-HBR Port 8081" `
            -Description "Allow PRECISE-HBR SMART on FHIR App Network Access" `
            -Direction Inbound `
            -LocalPort 8081 `
            -Protocol TCP `
            -Action Allow `
            -Enabled True
        
        Write-Host "防火牆規則已成功創建 (port 8081)" -ForegroundColor Green
        Write-Host ""
        Write-Host "規則詳情:" -ForegroundColor Cyan
        Write-Host "  規則名稱: $($rule.DisplayName)"
        Write-Host "  端口: 8081"
        Write-Host "  協議: TCP"
        Write-Host "  操作: Allow"
        Write-Host "  狀態: Enabled"
    } catch {
        Write-Host "創建防火牆規則失敗: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Port 8081 已開啟！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 驗證規則
$rule = Get-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -ErrorAction SilentlyContinue
if ($rule) {
    Write-Host "驗證: 防火牆規則已啟用" -ForegroundColor Green
    Write-Host "  顯示名稱: $($rule.DisplayName)"
    Write-Host "  啟用狀態: $($rule.Enabled)"
    Write-Host "  方向: $($rule.Direction)"
    Write-Host "  操作: $($rule.Action)"
}
