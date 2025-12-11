# Check Port 8081 Configuration
Write-Host "Checking Port 8081 Configuration..." -ForegroundColor Cyan
Write-Host ""

# Check port status
Write-Host "1. Port Status:" -ForegroundColor Yellow
$conn = Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue
if ($conn) {
    Write-Host "   Port 8081 is in use" -ForegroundColor Green
    Write-Host "   Bound to: $($conn.LocalAddress)" -ForegroundColor Gray
    if ($conn.LocalAddress -eq "127.0.0.1") {
        Write-Host "   WARNING: Only accessible from localhost!" -ForegroundColor Red
        Write-Host "   Solution: Restart with: python start_app.py --network" -ForegroundColor Cyan
    } elseif ($conn.LocalAddress -eq "0.0.0.0") {
        Write-Host "   OK: Network access enabled" -ForegroundColor Green
    }
} else {
    Write-Host "   Port 8081 is not in use" -ForegroundColor Yellow
}
Write-Host ""

# Check firewall
Write-Host "2. Firewall Rule:" -ForegroundColor Yellow
$rule = Get-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -ErrorAction SilentlyContinue
if ($rule) {
    Write-Host "   Rule exists: $($rule.Enabled)" -ForegroundColor Green
    if (-not $rule.Enabled) {
        Write-Host "   Enabling rule..." -ForegroundColor Yellow
        Set-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -Enabled True
    }
} else {
    Write-Host "   Rule not found - need to create it" -ForegroundColor Red
    Write-Host "   Run as Admin: .\open_port_8081_simple.ps1" -ForegroundColor Cyan
}
Write-Host ""

Write-Host "Done!" -ForegroundColor Green


