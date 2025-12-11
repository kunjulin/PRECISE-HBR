# Fix Port 8081 Configuration Script
# This script helps configure port 8081 for network access

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Port 8081 Configuration Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if port 8081 is in use
Write-Host "1. Checking port 8081 status..." -ForegroundColor Yellow
$connection = Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue
if ($connection) {
    Write-Host "   Port 8081 is in use" -ForegroundColor Green
    Write-Host "   Local Address: $($connection.LocalAddress)" -ForegroundColor Gray
    Write-Host "   State: $($connection.State)" -ForegroundColor Gray
    
    if ($connection.LocalAddress -eq "127.0.0.1") {
        Write-Host "   WARNING: App is only bound to localhost (127.0.0.1)" -ForegroundColor Red
        Write-Host "   This means it cannot be accessed from other computers!" -ForegroundColor Red
        Write-Host ""
        Write-Host "   Solution: Restart the app with network access enabled:" -ForegroundColor Yellow
        Write-Host "   python start_app.py --network" -ForegroundColor Cyan
        Write-Host "   OR set environment variable: `$env:ALLOW_NETWORK_ACCESS='true'" -ForegroundColor Cyan
    } elseif ($connection.LocalAddress -eq "0.0.0.0") {
        Write-Host "   OK: App is bound to 0.0.0.0 (network access enabled)" -ForegroundColor Green
    }
} else {
    Write-Host "   Port 8081 is not in use" -ForegroundColor Yellow
    Write-Host "   Start the app first: python start_app.py --network" -ForegroundColor Cyan
}
Write-Host ""

# Check firewall rule
Write-Host "2. Checking firewall rule..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -ErrorAction SilentlyContinue
if ($firewallRule) {
    Write-Host "   Firewall rule exists" -ForegroundColor Green
    Write-Host "   Enabled: $($firewallRule.Enabled)" -ForegroundColor Gray
    Write-Host "   Direction: $($firewallRule.Direction)" -ForegroundColor Gray
    Write-Host "   Action: $($firewallRule.Action)" -ForegroundColor Gray
    
    if (-not $firewallRule.Enabled) {
        Write-Host "   WARNING: Firewall rule is disabled!" -ForegroundColor Red
        Write-Host "   Enabling firewall rule..." -ForegroundColor Yellow
        Set-NetFirewallRule -DisplayName "PRECISE-HBR Port 8081" -Enabled True
        Write-Host "   Firewall rule enabled!" -ForegroundColor Green
    }
} else {
    Write-Host "   Firewall rule does not exist" -ForegroundColor Red
    Write-Host "   Creating firewall rule..." -ForegroundColor Yellow
    try {
        New-NetFirewallRule `
            -DisplayName "PRECISE-HBR Port 8081" `
            -Description "Allow PRECISE-HBR App Network Access" `
            -Direction Inbound `
            -LocalPort 8081 `
            -Protocol TCP `
            -Action Allow `
            -Enabled True | Out-Null
        Write-Host "   Firewall rule created successfully!" -ForegroundColor Green
    } catch {
        Write-Host "   ERROR: Failed to create firewall rule" -ForegroundColor Red
        Write-Host "   Run PowerShell as Administrator and execute:" -ForegroundColor Yellow
        Write-Host "   .\open_port_8081_simple.ps1" -ForegroundColor Cyan
    }
}
Write-Host ""

# Check .env file
Write-Host "3. Checking .env configuration..." -ForegroundColor Yellow
if (Test-Path .env) {
    $envContent = Get-Content .env
    $portLine = $envContent | Select-String -Pattern "^PORT="
    $redirectLine = $envContent | Select-String -Pattern "^SMART_REDIRECT_URI="
    $baseUrlLine = $envContent | Select-String -Pattern "^APP_BASE_URL="
    
    if ($portLine -match "PORT=8081") {
        Write-Host "   PORT=8081 ✓" -ForegroundColor Green
    } else {
        Write-Host "   PORT is not set to 8081" -ForegroundColor Red
        Write-Host "   Current: $portLine" -ForegroundColor Gray
    }
    
    if ($redirectLine -match "8081") {
        Write-Host "   SMART_REDIRECT_URI uses port 8081 ✓" -ForegroundColor Green
    } else {
        Write-Host "   SMART_REDIRECT_URI does not use port 8081" -ForegroundColor Red
        Write-Host "   Current: $redirectLine" -ForegroundColor Gray
    }
    
    if ($baseUrlLine -match "8081") {
        Write-Host "   APP_BASE_URL uses port 8081 ✓" -ForegroundColor Green
    } else {
        Write-Host "   APP_BASE_URL does not use port 8081" -ForegroundColor Red
        Write-Host "   Current: $baseUrlLine" -ForegroundColor Gray
    }
} else {
    Write-Host "   .env file does not exist" -ForegroundColor Yellow
    Write-Host "   Copy from template: copy local.env.template .env" -ForegroundColor Cyan
}
Write-Host ""

# Summary and recommendations
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary and Recommendations" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($connection -and $connection.LocalAddress -eq "127.0.0.1") {
    Write-Host "ACTION REQUIRED:" -ForegroundColor Red
    Write-Host "1. Stop the current app (Ctrl+C)" -ForegroundColor Yellow
    Write-Host "2. Restart with network access:" -ForegroundColor Yellow
    Write-Host "   python start_app.py --network" -ForegroundColor Cyan
    Write-Host ""
}

if (-not $firewallRule -or -not $firewallRule.Enabled) {
    Write-Host "ACTION REQUIRED:" -ForegroundColor Red
    Write-Host "Run as Administrator to create/enable firewall rule:" -ForegroundColor Yellow
    Write-Host "   .\open_port_8081_simple.ps1" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "After fixing the above, test from another computer:" -ForegroundColor Yellow
Write-Host "   http://YOUR_IP_ADDRESS:8081/" -ForegroundColor Cyan
Write-Host ""
Write-Host "To find your IP address:" -ForegroundColor Yellow
Write-Host "   Get-NetIPAddress -AddressFamily IPv4 | Where-Object { `$_.IPAddress -notlike '127.*' -and `$_.IPAddress -notlike '169.254.*' }" -ForegroundColor Cyan
Write-Host ""


