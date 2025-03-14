#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для сборки VK Video Downloader в исполняемый файл (EXE)
"""

import os
import sys
import subprocess
import shutil

def get_version():
    """Получает версию из файла version.py"""
    try:
        from version import __version__
        return __version__
    except ImportError:
        return "1.0.0"

def build_exe():
    """Собрать приложение в EXE файл"""
    print("Starting application build to EXE...")
        
    # Очистка предыдущих сборок
    for folder in ["dist", "build"]:
        if os.path.exists(folder):
            print(f"Cleaning {folder} folder...")
            shutil.rmtree(folder, ignore_errors=True)
    
    # Убедимся, что PyInstaller установлен
    try:
        subprocess.run(['pyinstaller', '--version'], check=True, stdout=subprocess.PIPE)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    # Явное указание пути к иконке относительно текущей директории скрипта
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    
    if not os.path.exists(icon_path):
        print(f"ERROR: Icon file not found at path: {icon_path}")
        sys.exit(1)
    
    # Команда для PyInstaller (создание нового билда)
    exe_name = f"VK_Video_Downloader"
    
    cmd = [
        'pyinstaller',
        '--name', exe_name,
        '--onefile',
        '--noconsole',
        '--clean',
        f'--icon={icon_path}',  # Указываем путь к иконке напрямую
        '--add-data', f'version.py{os.pathsep}.',
        '--add-data', f'icon.ico{os.pathsep}.',  # Добавляем иконку в ресурсы приложения
        'vk_video_downloader_gui.py'
    ]
    
    print("Running PyInstaller with parameters:")
    print(" ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        
        print("\nBuild completed!")
        print(f"Executable file is located in folder: {os.path.abspath('dist')}")
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nBuild error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print(f" Building VK Video Downloader v{get_version()}")
    print("=" * 50)
    print("")
    
    success = build_exe()
    
    if success:
        print("Build completed successfully!")
    else:
        print("Build completed with errors.")
        sys.exit(1)