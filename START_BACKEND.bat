@echo off
REM Start Backend Server Only
REM Run this from the project root directory

echo =========================================
echo Starting Backend Server (Port 4000)
echo =========================================

if not exist "backend" (
    echo ERROR: backend folder not found!
    echo Run this script from the project root directory.
    pause
    exit /b 1
)

cd backend

REM Check if .env exists
if not exist ".env" (
    if exist "..\..env.example" (
        echo Copying .env configuration...
        copy ..\..env.example .env
    ) else (
        echo WARNING: .env file not found. Using defaults.
    )
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Install from https://www.python.org
    pause
    exit /b 1
)

echo Installing backend dependencies...
pip install -r requirements.txt

echo.
echo =========================================
echo Backend Server Starting
echo =========================================
echo Backend will be available at: http://localhost:4000
echo Health check: http://localhost:4000/api/health
echo Upload endpoint: http://localhost:4000/api/upload
echo.
echo If you see errors, check:
echo  - MongoDB connection (MONGO_URI in .env)
echo  - Port 4000 is not already in use
echo  - All dependencies installed
echo.

python run.py

pause
