@echo off
REM Start Agentic RAG Document Assistant - Windows Script
REM This script starts both backend and frontend servers

echo =========================================
echo Agentic RAG Document Assistant Startup
echo =========================================

REM Check if we're in the right directory
if not exist "backend" (
    echo ERROR: backend folder not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

if not exist "frontend" (
    echo ERROR: frontend folder not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

echo.
echo Step 1: Starting Backend Server (Port 4000)
echo =========================================
cd backend

REM Check if .env exists, if not copy from .env.example
if not exist ".env" (
    if exist "..\..env.example" (
        echo Copying .env configuration...
        copy ..\..env.example .env
    )
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

echo Installing/checking backend dependencies...
pip install -r requirements.txt >nul 2>&1

echo Starting backend server...
echo Backend will be available at: http://localhost:4000
start "Backend Server - Port 4000" cmd /k python run.py

timeout /t 3 /nobreak

REM Change back to root
cd ..

echo.
echo Step 2: Starting Frontend Server (Port 3000)
echo =========================================
cd frontend

REM Check if .env exists for API URL
if not exist ".env.local" (
    echo Creating .env.local with API URL...
    (
        echo NEXT_PUBLIC_API_BASE_URL=http://localhost:4000
    ) > .env.local
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH!
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

echo Starting frontend server...
echo Frontend will be available at: http://localhost:3000
start "Frontend Server - Port 3000" cmd /k npm run dev

echo.
echo =========================================
echo Servers Starting...
echo =========================================
echo.
echo Backend:  http://localhost:4000
echo Frontend: http://localhost:3000
echo API:      http://localhost:4000/api/upload
echo Health:   http://localhost:4000/api/health
echo.
echo Frontend will open automatically when ready.
echo.
echo IMPORTANT: 
echo - Keep both windows open while developing
echo - Backend errors will show in the backend window
echo - Frontend errors will show in the frontend window
echo.
echo To stop the servers: Close the command windows or press Ctrl+C
echo.

timeout /t 5 /nobreak

REM Try to open frontend in default browser
echo Opening frontend in browser...
start http://localhost:3000

echo.
echo If frontend doesn't load after 5 seconds, manually visit http://localhost:3000
pause
