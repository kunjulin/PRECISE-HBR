@echo off
REM ============================================================================
REM PRECISE-HBR Security Scan with Bandit
REM Scans Python code for security vulnerabilities
REM ============================================================================

echo ========================================
echo PRECISE-HBR Security Scan
echo ========================================
echo.

REM Check if bandit is installed
python -c "import bandit" 2>nul
if errorlevel 1 (
    echo ERROR: Bandit is not installed!
    echo Installing Bandit...
    pip install bandit
    echo.
)

REM Create security_reports directory
if not exist "security_reports" mkdir security_reports

REM Get timestamp
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set timestamp=%mydate%_%mytime%

echo Running Bandit security scan...
echo Target files: *.py
echo.

REM Run Bandit scan with different output formats
echo [1/4] Generating detailed HTML report...
bandit -r . -f html -o security_reports/bandit_report_%timestamp%.html --exclude .venv,venv,env,__pycache__,.git -ll

echo [2/4] Generating JSON report...
bandit -r . -f json -o security_reports/bandit_report_%timestamp%.json --exclude .venv,venv,env,__pycache__,.git -ll

echo [3/4] Generating CSV report...
bandit -r . -f csv -o security_reports/bandit_report_%timestamp%.csv --exclude .venv,venv,env,__pycache__,.git -ll

echo [4/4] Generating text summary...
bandit -r . -f txt -o security_reports/bandit_summary_%timestamp%.txt --exclude .venv,venv,env,__pycache__,.git -ll

echo.
echo ========================================
echo Security scan completed!
echo ========================================
echo.
echo Reports saved in: security_reports\
echo   - bandit_report_%timestamp%.html (detailed HTML)
echo   - bandit_report_%timestamp%.json (machine-readable)
echo   - bandit_report_%timestamp%.csv (spreadsheet format)
echo   - bandit_summary_%timestamp%.txt (text summary)
echo.
echo Opening HTML report...
start security_reports\bandit_report_%timestamp%.html

echo.
pause

