@echo off
echo Starting Backend Server...
echo Make sure you are running this from the project root directory.
echo.

REM Navigate to the backend directory
cd interactive_poster_backend
IF NOT EXIST main.py (
    echo ERROR: Could not find interactive_poster_backend/main.py
    echo Please run this script from the main project root directory.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
IF EXIST venv\Scripts\activate (
    echo Activating Python virtual environment...
    call venv\Scripts\activate.bat
) ELSE (
    echo Python virtual environment (venv) not found.
    echo Attempting to run with system Python. Ensure FastAPI and uvicorn are installed globally or accessible.
)
echo.

echo Starting FastAPI server on port 8000 (uvicorn main:app --port 8000)...
uvicorn main:app --port 8000

echo.
echo Backend server process has finished or was interrupted.
pause
