@echo off
title PixelCrypt - Auto Push
cd /d "%~dp0"

echo ========================================
echo   PixelCrypt - Auto Push to GitHub
echo ========================================
echo.

:: Check if git is initialized
if not exist ".git" (
    echo Initializing git repository...
    git init
    git remote add origin https://github.com/RiveraMaxwell/pixelcrypt.git
    git branch -M main
)

:: Stage all changes
git add .

:: Check if there are changes to commit
git diff --cached --quiet
if %errorlevel%==0 (
    echo No changes to push.
    echo.
    pause
    exit /b 0
)

:: Auto-generate commit message with timestamp
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set mydate=%%c-%%a-%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a:%%b

set msg=Update %mydate% %mytime%

:: Show what's being committed
echo Changes detected:
echo.
git status --short
echo.
echo Commit message: %msg%
echo.

:: Commit and push
git commit -m "%msg%"
echo.

echo Pushing to GitHub...
git push -u origin main

echo.
if %errorlevel%==0 (
    echo ========================================
    echo   Pushed successfully!
    echo ========================================
) else (
    echo ========================================
    echo   Push failed. Check errors above.
    echo ========================================
)

echo.
pause
