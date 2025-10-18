# Deployment Readiness Verification Script
# Run this before deploying to Google Cloud App Engine

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Google Cloud Deployment Readiness Check  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check 1: Critical JSON files
Write-Host "1. Checking critical JSON files..." -ForegroundColor Yellow
$requiredFiles = @(
    "arc-hbr-model.json",
    "cdss_config.json",
    "bleeding_diathesis_valueset.json",
    "cancer_snomed_valueset.json",
    "portal_hypertension_valueset.json",
    "prior_bleeding_valueset.json",
    "ischemic_stroke_mod_severe_valueset.json",
    "cds-services.json"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        Write-Host "   ✓ $file ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $file MISSING!" -ForegroundColor Red
        $allGood = $false
    }
}

# Check 2: Python dependencies
Write-Host ""
Write-Host "2. Checking requirements.txt..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    Write-Host "   ✓ requirements.txt exists" -ForegroundColor Green
    $reqContent = Get-Content "requirements.txt"
    $criticalPackages = @("Flask", "fhirclient", "gunicorn", "google-cloud-secret-manager")
    foreach ($pkg in $criticalPackages) {
        $found = $reqContent | Select-String -Pattern "^$pkg"
        if ($found) {
            Write-Host "   ✓ $pkg found" -ForegroundColor Green
        } else {
            Write-Host "   ✗ $pkg missing!" -ForegroundColor Red
            $allGood = $false
        }
    }
} else {
    Write-Host "   ✗ requirements.txt MISSING!" -ForegroundColor Red
    $allGood = $false
}

# Check 3: app.yaml configuration
Write-Host ""
Write-Host "3. Checking app.yaml configuration..." -ForegroundColor Yellow
if (Test-Path "app.yaml") {
    Write-Host "   ✓ app.yaml exists" -ForegroundColor Green
    $appYaml = Get-Content "app.yaml" -Raw
    
    # Check for Secret Manager configuration
    if ($appYaml -match 'FLASK_SECRET_KEY.*projects/.*secrets') {
        Write-Host "   ✓ FLASK_SECRET_KEY configured for Secret Manager" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ FLASK_SECRET_KEY not using Secret Manager" -ForegroundColor Yellow
    }
    
    # Check for SMART configuration
    if ($appYaml -match 'SMART_CLIENT_ID') {
        Write-Host "   ✓ SMART_CLIENT_ID configured" -ForegroundColor Green
    } else {
        Write-Host "   ✗ SMART_CLIENT_ID missing!" -ForegroundColor Red
        $allGood = $false
    }
    
    if ($appYaml -match 'SMART_REDIRECT_URI.*smart-lu\.uc\.r\.appspot\.com') {
        Write-Host "   ✓ SMART_REDIRECT_URI configured" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ SMART_REDIRECT_URI may need updating" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✗ app.yaml MISSING!" -ForegroundColor Red
    $allGood = $false
}

# Check 4: .gcloudignore configuration
Write-Host ""
Write-Host "4. Checking .gcloudignore configuration..." -ForegroundColor Yellow
if (Test-Path ".gcloudignore") {
    Write-Host "   ✓ .gcloudignore exists" -ForegroundColor Green
    $gcloudIgnore = Get-Content ".gcloudignore" -Raw
    
    # Check that valuesets are NOT being excluded
    if ($gcloudIgnore -match '^\s*\*_valueset\.json\s*$' -and $gcloudIgnore -notmatch '^\s*#.*\*_valueset\.json') {
        Write-Host "   ✗ .gcloudignore is excluding *_valueset.json files!" -ForegroundColor Red
        $allGood = $false
    } else {
        Write-Host "   ✓ valueset files will be included" -ForegroundColor Green
    }
    
    # Check that .env is being excluded
    if ($gcloudIgnore -match '\.env') {
        Write-Host "   ✓ .env file will be excluded (correct)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ .env file may be included (security risk)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠ .gcloudignore not found (using defaults)" -ForegroundColor Yellow
}

# Check 5: Core Python files
Write-Host ""
Write-Host "5. Checking core application files..." -ForegroundColor Yellow
$coreFiles = @("APP.py", "fhir_data_service.py", "tradeoff_analysis_routes.py", "config.py")
foreach ($file in $coreFiles) {
    if (Test-Path $file) {
        Write-Host "   ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $file MISSING!" -ForegroundColor Red
        $allGood = $false
    }
}

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "  ✓ ALL CHECKS PASSED - READY TO DEPLOY!  " -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Create the FLASK_SECRET_KEY in Secret Manager:" -ForegroundColor White
    Write-Host "   python -c `"import secrets; print(secrets.token_urlsafe(32))`" | gcloud secrets versions add FLASK_SECRET_KEY --data-file=-" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Grant Secret Manager access to App Engine:" -ForegroundColor White
    Write-Host "   See DEPLOYMENT_CHECKLIST.md for full IAM commands" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "3. Deploy to App Engine:" -ForegroundColor White
    Write-Host "   gcloud app deploy app.yaml" -ForegroundColor Cyan
} else {
    Write-Host "  ✗ ISSUES FOUND - FIX BEFORE DEPLOYING!  " -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please fix the issues marked with ✗ above before deploying." -ForegroundColor Yellow
}
Write-Host ""

