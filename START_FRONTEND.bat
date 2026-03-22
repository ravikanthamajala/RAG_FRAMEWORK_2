@echo off
REM Start Frontend Server Only
REM Run this from the project root directory

echo =========================================
echo Starting Frontend Server (Port 3000)
echo =========================================

if not exist "frontend" (
    echo ERROR: frontend folder not found!
    echo Run this script from the project root directory.
    pause
    exit /b 1
)

cd frontend

REM Create .env.local if it doesn't exist
if not exist ".env.local" (
    echo Creating .env.local...
    (
        echo NEXT_PUBLIC_API_BASE_URL=http://localhost:4000
    ) > .env.local
    echo Created .env.local with API_BASE_URL=http://localhost:4000
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Install from https://nodejs.org
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

echo.
echo =========================================
echo Frontend Server Starting
echo =========================================
echo Frontend will be available at: http://localhost:3000
echo Backend API: http://localhost:4000
echo.
echo Make sure backend is running first!
echo Run START_BACKEND.bat in another window.
echo.

npm run dev

pause
