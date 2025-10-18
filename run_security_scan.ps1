# ============================================================================
# PRECISE-HBR Security Scan with Bandit (PowerShell Version)
# Scans Python code for security vulnerabilities
# ============================================================================

Write-Host "========================================"
Write-Host "PRECISE-HBR Security Scan"
Write-Host "========================================"
Write-Host ""

# Check if bandit is installed
try {
    python -c "import bandit" 2>$null
} catch {
    Write-Host "ERROR: Bandit is not installed!" -ForegroundColor Red
    Write-Host "Installing Bandit..." -ForegroundColor Yellow
    pip install bandit
    Write-Host ""
}

# Create security_reports directory
if (-not (Test-Path "security_reports")) {
    New-Item -ItemType Directory -Path "security_reports" | Out-Null
}

# Get timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "Running Bandit security scan..." -ForegroundColor Cyan
Write-Host "Target files: *.py"
Write-Host ""

# Run Bandit scan with different output formats
Write-Host "[1/4] Generating detailed HTML report..." -ForegroundColor Green
bandit -r . -f html -o "security_reports/bandit_report_$timestamp.html" --exclude .venv,venv,env,__pycache__,.git -ll

Write-Host "[2/4] Generating JSON report..." -ForegroundColor Green
bandit -r . -f json -o "security_reports/bandit_report_$timestamp.json" --exclude .venv,venv,env,__pycache__,.git -ll

Write-Host "[3/4] Generating CSV report..." -ForegroundColor Green
bandit -r . -f csv -o "security_reports/bandit_report_$timestamp.csv" --exclude .venv,venv,env,__pycache__,.git -ll

Write-Host "[4/4] Generating text summary..." -ForegroundColor Green
bandit -r . -f txt -o "security_reports/bandit_summary_$timestamp.txt" --exclude .venv,venv,env,__pycache__,.git -ll

Write-Host ""
Write-Host "========================================"
Write-Host "Security scan completed!"
Write-Host "========================================"
Write-Host ""
Write-Host "Reports saved in: security_reports\" -ForegroundColor Green
Write-Host "  - bandit_report_$timestamp.html (detailed HTML)"
Write-Host "  - bandit_report_$timestamp.json (machine-readable)"
Write-Host "  - bandit_report_$timestamp.csv (spreadsheet format)"
Write-Host "  - bandit_summary_$timestamp.txt (text summary)"
Write-Host ""
Write-Host "Opening HTML report..." -ForegroundColor Cyan
Start-Process "security_reports\bandit_report_$timestamp.html"

Write-Host ""
Read-Host "Press Enter to exit"

