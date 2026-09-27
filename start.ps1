Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  CCTV Intelligence - Windows Launch Script" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "Virtual environment .venv\Scripts\python.exe not found."
    exit 1
}

if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

Write-Host "Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Yellow
$backend = Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000" -PassThru

Write-Host "Starting Vite Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
$frontend = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev --prefix frontend" -PassThru

Write-Host "`nServers running!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "Swagger:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "Health:   http://localhost:8000/api/system/health`n" -ForegroundColor White

Write-Host "Press Ctrl+C to terminate both servers.`n" -ForegroundColor Gray

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -ErrorAction SilentlyContinue
}
