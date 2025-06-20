@echo off
echo Starting Frontend Development Server...
echo Make sure you are running this from the project root directory,
echo and that Node.js and npm/yarn are installed.
echo.

REM Navigate to the frontend directory
cd interactive-poster-ui
IF NOT EXIST package.json (
    echo ERROR: Could not find interactive-poster-ui/package.json
    echo Please run this script from the main project root directory.
    pause
    exit /b 1
)
echo.

echo Running 'npm run dev' (or 'yarn dev')...
REM Check for yarn.lock to prefer yarn if available, otherwise use npm
IF EXIST yarn.lock (
    echo Found yarn.lock, using 'yarn dev'
    yarn dev
) ELSE (
    echo Using 'npm run dev'
    npm run dev
)

echo.
echo Frontend server process has finished or was interrupted.
pause
