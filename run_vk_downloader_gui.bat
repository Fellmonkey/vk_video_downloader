@echo off
echo Starting VK Video Downloader...
python vk_video_downloader_gui.py
if errorlevel 1 (
    echo Error running application. 
    echo Please ensure that Python and PyQt5 are installed.
    echo Install PyQt5 with: pip install PyQt5
    pause
)