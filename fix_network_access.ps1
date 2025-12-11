# Fix Network Access for Port 8081
Write-Host "=== Port 8081 Network Access Fix ===" -ForegroundColor Cyan
Write-Host ""

# Check current binding
Write-Host "Current Status:" -ForegroundColor Yellow
$conn = Get-NetTCPConnection -LocalPort 8081 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Write-Host "  Port 8081 is listening on: $($conn.LocalAddress)" -ForegroundColor $(if ($conn.LocalAddress -eq "0.0.0.0") { "Green" } else { "Red" })
    if ($conn.LocalAddress -eq "127.0.0.1") {
        Write-Host "  PROBLEM: Only accessible from localhost!" -ForegroundColor Red
    }
} else {
    Write-Host "  Port 8081 is not in use" -ForegroundColor Yellow
}
Write-Host ""

# Check firewall
Write-Host "Firewall Status:" -ForegroundColor Yellow
$fwRule = Get-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -ErrorAction SilentlyContinue
if ($fwRule) {
    Write-Host "  Firewall rule exists: $($fwRule.Enabled)" -ForegroundColor $(if ($fwRule.Enabled) { "Green" } else { "Red" })
} else {
    Write-Host "  PROBLEM: Firewall rule does not exist!" -ForegroundColor Red
}
Write-Host ""

# Solutions
Write-Host "=== SOLUTION ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Step 1: Stop the current app (Ctrl+C in the app window)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Step 2: Create firewall rule (Run as Administrator):" -ForegroundColor Yellow
Write-Host "  New-NetFirewallRule -DisplayName 'PRECISE-HBR Port 8081' -Description 'Allow PRECISE-HBR App Network Access' -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow -Enabled True" -ForegroundColor Cyan
Write-Host ""
Write-Host "Step 3: Restart app with network access:" -ForegroundColor Yellow
Write-Host "  python start_app.py --network" -ForegroundColor Cyan
Write-Host ""
Write-Host "After restart, verify:" -ForegroundColor Yellow
Write-Host "  Get-NetTCPConnection -LocalPort 8081 | Select-Object LocalAddress" -ForegroundColor Cyan
Write-Host "  Should show: 0.0.0.0 (not 127.0.0.1)" -ForegroundColor Green
Write-Host ""


