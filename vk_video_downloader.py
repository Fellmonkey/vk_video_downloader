#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для скачивания видео из VK
Требует установки библиотеки yt-dlp: pip install yt-dlp
"""

import sys
import subprocess
from urllib.parse import urlparse

def get_vk_video_id(url):
    """Извлекает ID видео VK из URL"""
    # Если это полный URL
    if "vk.com" in url:
        path = urlparse(url).path.strip('/')
        if path.startswith('clip-'):
            return path
        elif 'video' in path:
            return path.split('video')[1]
    # Если передан просто ID
    elif "clip-" in url:
        return url
    
    return url

def download_vk_video(video_id_or_url):
    """Скачивает видео из VK по его ID или URL"""
    # Проверяем, что передана ссылка или ID
    if not video_id_or_url:
        print("Ошибка: Не указана ссылка на видео")
        return False
    
    # Пробуем импортировать yt-dlp
    try:
        import yt_dlp
    except ImportError:
        print("yt-dlp не установлен. Устанавливаем...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
            print("yt-dlp успешно установлен")
            # После установки пытаемся снова импортировать
            import yt_dlp
        except Exception as e:
            print(f"Ошибка при установке yt-dlp: {e}")
            print("Пожалуйста, установите yt-dlp вручную: pip install yt-dlp")
            return False
    
    video_id = get_vk_video_id(video_id_or_url)
    
    if not video_id:
        print("Неверный формат ID или URL видео")
        return False
    
    # Формируем URL для скачивания
    if "clip-" in video_id:
        url = f"https://vk.com/{video_id}"
    else:
        url = f"https://vk.com/video{video_id}"
    
    print(f"Начинаем скачивание видео: {url}")
    
    # Используем yt-dlp напрямую
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'verbose': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            print(f"Видео успешно скачано: {info['title']}.{info.get('ext', 'mp4')}")
            return True
    except Exception as e:
        print(f"Ошибка при скачивании видео: {e}")
        return False

if __name__ == "__main__":
    video_id_or_url = None
    
    if len(sys.argv) > 1:
        video_id_or_url = sys.argv[1]
    
    # Если ссылка не передана через аргументы, запрашиваем у пользователя
    if not video_id_or_url:
        print("Пожалуйста, вставьте ссылку на видео VK или ID видео:")
        video_id_or_url = input().strip()
    
    # Если пользователь ничего не ввел, выводим ошибку
    if not video_id_or_url:
        print("Ссылка на видео не предоставлена. Программа завершает работу.")
    else:
        download_result = download_vk_video(video_id_or_url)
    
    # Подождем ввода пользователя, чтобы скрипт не закрывался сразу
    input("\nНажмите Enter для выхода...")