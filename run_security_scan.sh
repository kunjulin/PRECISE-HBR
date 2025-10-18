#!/bin/bash
# ============================================================================
# PRECISE-HBR Security Scan with Bandit (Linux/Mac Version)
# Scans Python code for security vulnerabilities
# ============================================================================

echo "========================================"
echo "PRECISE-HBR Security Scan"
echo "========================================"
echo ""

# Check if bandit is installed
if ! python -c "import bandit" 2>/dev/null; then
    echo "ERROR: Bandit is not installed!"
    echo "Installing Bandit..."
    pip install bandit
    echo ""
fi

# Create security_reports directory
mkdir -p security_reports

# Get timestamp
timestamp=$(date +%Y%m%d_%H%M%S)

echo "Running Bandit security scan..."
echo "Target files: *.py"
echo ""

# Run Bandit scan with different output formats
echo "[1/4] Generating detailed HTML report..."
bandit -r . -f html -o "security_reports/bandit_report_${timestamp}.html" --exclude .venv,venv,env,__pycache__,.git -ll

echo "[2/4] Generating JSON report..."
bandit -r . -f json -o "security_reports/bandit_report_${timestamp}.json" --exclude .venv,venv,env,__pycache__,.git -ll

echo "[3/4] Generating CSV report..."
bandit -r . -f csv -o "security_reports/bandit_report_${timestamp}.csv" --exclude .venv,venv,env,__pycache__,.git -ll

echo "[4/4] Generating text summary..."
bandit -r . -f txt -o "security_reports/bandit_summary_${timestamp}.txt" --exclude .venv,venv,env,__pycache__,.git -ll

echo ""
echo "========================================"
echo "Security scan completed!"
echo "========================================"
echo ""
echo "Reports saved in: security_reports/"
echo "  - bandit_report_${timestamp}.html (detailed HTML)"
echo "  - bandit_report_${timestamp}.json (machine-readable)"
echo "  - bandit_report_${timestamp}.csv (spreadsheet format)"
echo "  - bandit_summary_${timestamp}.txt (text summary)"
echo ""
echo "Opening HTML report..."
if command -v xdg-open &> /dev/null; then
    xdg-open "security_reports/bandit_report_${timestamp}.html"
elif command -v open &> /dev/null; then
    open "security_reports/bandit_report_${timestamp}.html"
else
    echo "Please manually open: security_reports/bandit_report_${timestamp}.html"
fi

echo ""

