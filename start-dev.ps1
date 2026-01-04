# NotificationAgent - Development Startup
# This script starts services in separate terminal windows for easier debugging

Write-Host "=== Starting Notification Agent (Development Mode) ===" -ForegroundColor Green
Write-Host ""

# Start dependencies
Write-Host "Starting dependencies (Redis, PostgreSQL)..." -ForegroundColor Cyan
& .\start-services.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start dependencies. Exiting." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Starting Application Services in Separate Windows ===" -ForegroundColor Green

# Start Celery Worker in new window
Write-Host ""
Write-Host "Starting Celery Worker in new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Set-Location '$PWD'; .\.venv\Scripts\Activate.ps1; Write-Host 'Starting Celery Worker...' -ForegroundColor Green; celery -A app.celery_app worker --loglevel=info --pool=solo }"

# Wait a moment
Start-Sleep -Seconds 2

# Start FastAPI Server in new window
Write-Host "Starting FastAPI Server in new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Set-Location '$PWD'; .\.venv\Scripts\Activate.ps1; Write-Host 'Starting FastAPI Server...' -ForegroundColor Green; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 }"

Write-Host ""
Write-Host "=== All Services Started ===" -ForegroundColor Green
Write-Host ""
Write-Host "Services running in separate windows:" -ForegroundColor Cyan
Write-Host "  - Redis:         localhost:6379" -ForegroundColor White
Write-Host "  - PostgreSQL:    localhost:5432" -ForegroundColor White
Write-Host "  - Celery Worker: Separate terminal window" -ForegroundColor White
Write-Host "  - FastAPI:       http://localhost:8000 (Separate terminal window)" -ForegroundColor White
Write-Host ""
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Cyan
Write-Host "  1. Close the Celery and FastAPI terminal windows" -ForegroundColor White
Write-Host "  2. Run: .\stop-all.ps1" -ForegroundColor White
Write-Host ""
