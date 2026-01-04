# Podman Startup Script for Notification Agent
# This script uses podman-compose to start the application

Write-Host "=== Notification Agent Podman Startup ===" -ForegroundColor Green
Write-Host ""

# Check if podman is installed
if (-not (Get-Command "podman" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Podman is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Podman Desktop or Podman CLI." -ForegroundColor Yellow
    exit 1
}

# Check if podman-compose is installed
# Note: podman-compose is often a separate install, sometimes aliased.
# Depending on setup, users might use 'docker-compose' with podman backend.
$composeCmd = "podman-compose"
if (-not (Get-Command "podman-compose" -ErrorAction SilentlyContinue)) {
     if (Get-Command "docker-compose" -ErrorAction SilentlyContinue) {
        Write-Host "podman-compose not found, trying docker-compose..." -ForegroundColor Yellow
        $composeCmd = "docker-compose"
     } else {
        Write-Host "ERROR: Neither podman-compose nor docker-compose found." -ForegroundColor Red
        Write-Host "Please install podman-compose (pip install podman-compose)." -ForegroundColor Yellow
        exit 1
     }
}

Write-Host "Using compose command: $composeCmd" -ForegroundColor Cyan

# Check if .env file exists
if (-Not (Test-Path ".\.env")) {
    Write-Host "WARNING: .env file not found. Creating from example." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env file. Please review settings." -ForegroundColor Green
}

# Build and Start Services
Write-Host "Building and starting services..." -ForegroundColor Cyan
Invoke-Expression "& $composeCmd up --build -d"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Services Started Successfully ===" -ForegroundColor Green
    Write-Host "Web App: http://localhost:8000" -ForegroundColor White
    Write-Host "To view logs: $composeCmd logs -f" -ForegroundColor Gray
    Write-Host "To stop: $composeCmd down" -ForegroundColor Gray
} else {
    Write-Host "ERROR: Failed to start services." -ForegroundColor Red
    exit 1
}
