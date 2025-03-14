@echo off
echo ========================================
echo   Building VK Video Downloader to EXE
echo ========================================
echo.

python build_exe.py

if errorlevel 1 (
    echo.
    echo An error occurred during the build process.
    echo.
    pause
    exit /b 1
)

echo.
echo Build completed!
pause