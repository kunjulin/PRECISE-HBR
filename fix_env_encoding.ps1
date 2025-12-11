# Fix .env file encoding to UTF-8
Write-Host "Fixing .env file encoding..." -ForegroundColor Yellow

if (Test-Path .env) {
    try {
        # Read the file with default encoding (which might be ANSI/GBK on Windows)
        $content = Get-Content .env -Raw -Encoding Default
        
        # Write back as UTF-8
        [System.IO.File]::WriteAllText((Resolve-Path .env).Path, $content, [System.Text.Encoding]::UTF8)
        
        Write-Host "SUCCESS: .env file converted to UTF-8" -ForegroundColor Green
        Write-Host "You can now restart the app: python start_app.py --network" -ForegroundColor Cyan
    } catch {
        Write-Host "ERROR: Failed to convert file: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "ERROR: .env file not found" -ForegroundColor Red
    Write-Host "Copy from template: copy local.env.template .env" -ForegroundColor Yellow
    exit 1
}


