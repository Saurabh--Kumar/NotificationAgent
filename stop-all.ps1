# NotificationAgent - Stop All Services
# This script stops all running services

Write-Host "=== Stopping All Notification Agent Services ===" -ForegroundColor Yellow
Write-Host ""

# Stop PowerShell background jobs
Write-Host "Stopping background jobs..." -ForegroundColor Cyan
Get-Job | Where-Object { $_.State -eq "Running" } | ForEach-Object {
    Write-Host "  Stopping Job $($_.Id): $($_.Command)" -ForegroundColor Gray
    Stop-Job -Id $_.Id
    Remove-Job -Id $_.Id
}
Write-Host "Background jobs stopped" -ForegroundColor Green

# Stop Docker containers
Write-Host ""
Write-Host "Stopping Docker containers..." -ForegroundColor Cyan

# Stop Redis
if (docker ps --filter "name=notification-agent-redis" --format "{{.Names}}" | Select-String "notification-agent-redis") {
    Write-Host "  Stopping Redis..." -ForegroundColor Gray
    docker stop notification-agent-redis | Out-Null
    docker rm notification-agent-redis | Out-Null
    Write-Host "  Redis stopped" -ForegroundColor Green
}

# Stop PostgreSQL
if (docker ps --filter "name=notification-agent-postgres" --format "{{.Names}}" | Select-String "notification-agent-postgres") {
    Write-Host "  Stopping PostgreSQL..." -ForegroundColor Gray
    docker stop notification-agent-postgres | Out-Null
    docker rm notification-agent-postgres | Out-Null
    Write-Host "  PostgreSQL stopped" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== All Services Stopped ===" -ForegroundColor Green
Write-Host ""
