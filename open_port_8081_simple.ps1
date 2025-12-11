# Simple script to open firewall port 8081
# Run as Administrator

$rule = Get-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -ErrorAction SilentlyContinue

if ($rule) {
    Set-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -Enabled True
    Write-Host "Firewall rule enabled for port 8081" -ForegroundColor Green
} else {
    New-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -Description "Allow PRECISE-HBR App Network Access" -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow -Enabled True
    Write-Host "Firewall rule created for port 8081" -ForegroundColor Green
}

Write-Host "Port 8081 is now open!" -ForegroundColor Green


