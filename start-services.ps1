# NotificationAgent Startup Script
# This script starts all required services for the Notification Agent application

Write-Host "=== Notification Agent Startup ===" -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path ".\.venv")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Virtual environment created." -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# Install/update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet

# Check if .env file exists
if (-Not (Test-Path ".\.env")) {
    Write-Host "WARNING: .env file not found. Please create one based on .env.example" -ForegroundColor Yellow
    Write-Host "Press any key to continue or Ctrl+C to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Function to check if a port is in use
function Test-Port {
    param($Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
    return $connection.TcpTestSucceeded
}

# Start Redis (using Docker)
Write-Host ""
Write-Host "=== Starting Redis ===" -ForegroundColor Green
if (Test-Port 6379) {
    Write-Host "Redis is already running on port 6379" -ForegroundColor Yellow
} else {
    Write-Host "Starting Redis container..." -ForegroundColor Cyan
    docker run -d --name notification-agent-redis -p 6379:6379 redis:latest
    Start-Sleep -Seconds 2
    if (Test-Port 6379) {
        Write-Host "Redis started successfully" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to start Redis" -ForegroundColor Red
        exit 1
    }
}

# Start PostgreSQL (using Docker)
Write-Host ""
Write-Host "=== Starting PostgreSQL ===" -ForegroundColor Green
if (Test-Port 5432) {
    Write-Host "PostgreSQL is already running on port 5432" -ForegroundColor Yellow
} else {
    Write-Host "Starting PostgreSQL container..." -ForegroundColor Cyan
    docker run -d --name notification-agent-postgres `
        -e POSTGRES_USER=postgres `
        -e POSTGRES_PASSWORD=postgres `
        -e POSTGRES_DB=notification_agent `
        -p 5432:5432 `
        postgres:15
    
    Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Cyan
    Start-Sleep -Seconds 5
    
    if (Test-Port 5432) {
        Write-Host "PostgreSQL started successfully" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to start PostgreSQL" -ForegroundColor Red
        exit 1
    }
}

# Run database migrations (if using Alembic)
# Uncomment when migrations are set up
# Write-Host ""
# Write-Host "=== Running Database Migrations ===" -ForegroundColor Green
# alembic upgrade head

Write-Host ""
Write-Host "=== All services started successfully ===" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application, run the following commands in separate terminals:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Celery Worker:" -ForegroundColor Yellow
Write-Host "   celery -A app.celery_app worker --loglevel=info --pool=solo" -ForegroundColor White
Write-Host ""
Write-Host "2. FastAPI Server:" -ForegroundColor Yellow
Write-Host "   uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "Or use the start-all.ps1 script to start everything in the background." -ForegroundColor Cyan
Write-Host ""
