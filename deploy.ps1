# -*- coding: utf-8 -*-
# PowerShell deployment script to handle encoding issues

# Set encoding to UTF-8
$env:PYTHONIOENCODING = 'utf-8'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

# Change to a temporary English path
$tempPath = "C:\temp\smart_fhir_deploy"
Write-Host "Creating temporary deployment directory..."

# Create temp directory if it doesn't exist
if (-not (Test-Path $tempPath)) {
    New-Item -ItemType Directory -Path $tempPath -Force
}

# Copy necessary files to temp directory
Write-Host "Copying files to temporary directory..."
Copy-Item "APP.py" -Destination $tempPath -Force
Copy-Item "app_clean.yaml" -Destination $tempPath -Force
Copy-Item "requirements.txt" -Destination $tempPath -Force
Copy-Item "cdss_config.json" -Destination $tempPath -Force
Copy-Item "templates" -Destination $tempPath -Recurse -Force

# Change to temp directory
Set-Location $tempPath

# Rename app_clean.yaml to app.yaml
Move-Item "app_clean.yaml" "app.yaml" -Force

Write-Host "Deploying from: $tempPath"
Write-Host "Running: gcloud app deploy app.yaml"

# Deploy using gcloud
try {
    gcloud app deploy app.yaml
    Write-Host "Deployment completed successfully!"
} catch {
    Write-Error "Deployment failed: $_"
} finally {
    # Return to original directory
    Set-Location $PSScriptRoot
    Write-Host "Returned to original directory"
    
    # Optionally clean up temp directory
    # Remove-Item $tempPath -Recurse -Force
} 