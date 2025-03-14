@echo off
echo Starting VK video download script...
echo.

python vk_video_downloader.py %*

if errorlevel 1 (
    echo.
    echo An error occurred while executing the script.
    echo.
    pause
    exit /b 1
)

echo.
echo Script completed successfully!
pause