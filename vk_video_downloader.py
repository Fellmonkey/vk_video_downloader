#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для скачивания видео из VK
Требует установки библиотеки yt-dlp: pip install yt-dlp
"""

import sys
import subprocess
from urllib.parse import urlparse

def normalize_vk_url(url):
    """Нормализует URL или ID видео VK в стандартный формат"""
    if not url:
        return None
        
    # Для vkvideo.ru
    if "vkvideo.ru" in url:
        path = urlparse(url).path.strip('/')
        if path.startswith('video-'):
            video_id = path[6:]  # Убираем префикс 'video-'
            owner_id, video_id = video_id.split('_')
            return f"https://vk.com/video-{owner_id}_{video_id}"
        
    # Для vk.com и прямых ссылок
    if "vk.com" in url:
        path = urlparse(url).path.strip('/')
        if path.startswith('clip-'):
            return f"https://vk.com/{path}"
        elif 'video' in path:
            if not path.startswith('video'):
                return f"https://vk.com/video{path.split('video')[1]}"
            return f"https://vk.com/{path}"
            
    # Если передан просто ID
    if "clip-" in url:
        return f"https://vk.com/{url}"
    if not url.startswith('http'):
        return f"https://vk.com/video{url}"
        
    return url

def download_vk_video(video_url):
    """Скачивает видео из VK по его URL"""
    if not video_url:
        print("Ошибка: Не указана ссылка на видео")
        return False
    
    try:
        import yt_dlp
    except ImportError:
        print("yt-dlp не установлен. Устанавливаем...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
            import yt_dlp
        except Exception as e:
            print(f"Ошибка при установке yt-dlp: {e}")
            return False
    
    normalized_url = normalize_vk_url(video_url)
    if not normalized_url:
        print("Не удалось получить корректный URL видео")
        return False
    
    print(f"Начинаем скачивание видео: {normalized_url}")
    
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(normalized_url, download=True)
            print(f"Видео успешно скачано: {info['title']}.{info.get('ext', 'mp4')}")
            return True
    except Exception as e:
        print(f"Ошибка при скачивании видео: {e}")
        return False

if __name__ == "__main__":
    video_url = sys.argv[1] if len(sys.argv) > 1 else input("Пожалуйста, вставьте ссылку на видео VK или ID видео:\n").strip()
    
    if video_url:
        download_vk_video(video_url)
    else:
        print("Ссылка на видео не предоставлена. Программа завершает работу.")
    
    input("\nНажмите Enter для выхода...")