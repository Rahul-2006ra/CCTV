@echo off
setlocal
echo =======================================================
echo   CCTV Intelligence - Starting Local Production Servers
echo =======================================================

if not exist .venv\Scripts\python.exe (
    echo Error: .venv not found. Please create virtual environment first.
    exit /b 1
)

if not exist logs mkdir logs

echo Starting FastAPI Backend on http://localhost:8000 ...
start "CCTV Backend" .venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

echo Starting React/Vite Frontend on http://localhost:5173 ...
start "CCTV Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo =======================================================
echo CCTV Intelligence Workstation is launching!
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo Swagger:  http://localhost:8000/docs
echo Health:   http://localhost:8000/api/system/health
echo =======================================================
