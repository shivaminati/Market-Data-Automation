@echo off
REM Setup script for Market Data Automation Tool (Windows)

echo ==========================================
echo Market Data Automation Tool - Setup
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.

REM Create .env from example if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo [32m✓ .env file created. Please edit it with your configuration.[0m
) else (
    echo [32m✓ .env file already exists[0m
)
echo.

REM Create data and logs directories
echo Creating data and logs directories...
if not exist data mkdir data
if not exist logs mkdir logs
echo.

echo ==========================================
echo [32m✅ Setup Complete![0m
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Activate virtual environment: venv\Scripts\activate
echo 3. Run the tool: cd src ^&^& python main.py
echo.

pause
