# NotificationAgent - Start All Services
# This script starts all services in the background

Write-Host "=== Starting All Notification Agent Services ===" -ForegroundColor Green
Write-Host ""

# First, start dependencies
Write-Host "Starting dependencies (Redis, PostgreSQL)..." -ForegroundColor Cyan
& .\start-services.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start dependencies. Exiting." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "=== Starting Application Services ===" -ForegroundColor Green

# Start Celery Worker in background
Write-Host ""
Write-Host "Starting Celery Worker..." -ForegroundColor Cyan
$celeryJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & .\.venv\Scripts\Activate.ps1
    celery -A app.celery_app worker --loglevel=info --pool=solo
}
Write-Host "Celery Worker started (Job ID: $($celeryJob.Id))" -ForegroundColor Green

# Wait a moment for Celery to initialize
Start-Sleep -Seconds 3

# Start FastAPI Server in background
Write-Host ""
Write-Host "Starting FastAPI Server..." -ForegroundColor Cyan
$uvicornJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & .\.venv\Scripts\Activate.ps1
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}
Write-Host "FastAPI Server started (Job ID: $($uvicornJob.Id))" -ForegroundColor Green

# Wait for server to start
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "=== All Services Started ===" -ForegroundColor Green
Write-Host ""
Write-Host "Services running:" -ForegroundColor Cyan
Write-Host "  - Redis:         localhost:6379" -ForegroundColor White
Write-Host "  - PostgreSQL:    localhost:5432" -ForegroundColor White
Write-Host "  - Celery Worker: Background Job $($celeryJob.Id)" -ForegroundColor White
Write-Host "  - FastAPI:       http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  Celery:  Receive-Job -Id $($celeryJob.Id) -Keep" -ForegroundColor White
Write-Host "  FastAPI: Receive-Job -Id $($uvicornJob.Id) -Keep" -ForegroundColor White
Write-Host ""
Write-Host "To stop all services, run: .\stop-all.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop monitoring (services will continue running)" -ForegroundColor Gray
Write-Host ""

# Monitor the jobs
try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Check if jobs are still running
        $celeryState = (Get-Job -Id $celeryJob.Id).State
        $uvicornState = (Get-Job -Id $uvicornJob.Id).State
        
        if ($celeryState -ne "Running") {
            Write-Host "WARNING: Celery Worker stopped unexpectedly" -ForegroundColor Red
            Receive-Job -Id $celeryJob.Id
        }
        
        if ($uvicornState -ne "Running") {
            Write-Host "WARNING: FastAPI Server stopped unexpectedly" -ForegroundColor Red
            Receive-Job -Id $uvicornJob.Id
        }
    }
} finally {
    Write-Host ""
    Write-Host "Monitoring stopped. Services are still running in the background." -ForegroundColor Yellow
    Write-Host "Use .\stop-all.ps1 to stop all services." -ForegroundColor Yellow
}
