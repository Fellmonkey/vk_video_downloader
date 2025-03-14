#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Графическое приложение для скачивания видео из VK
Требует установки библиотек:
- yt-dlp: pip install yt-dlp
- PyQt5: pip install PyQt5
"""

import sys
import os
import subprocess
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QPushButton, QProgressBar, 
                            QTextEdit, QFileDialog, QMessageBox, QStatusBar)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon

# Импортируем функциональность из оригинального скрипта
from vk_video_downloader import get_vk_video_id
from version import __version__

class DownloadThread(QThread):
    """Отдельный поток для скачивания видео"""
    progress_update = pyqtSignal(str)
    download_finished = pyqtSignal(bool, str)
    
    def __init__(self, video_url, output_dir=None):
        super().__init__()
        self.video_url = video_url
        self.output_dir = output_dir
        
    def run(self):
        try:
            # Импортируем yt-dlp внутри потока
            try:
                import yt_dlp
            except ImportError:
                self.progress_update.emit("yt-dlp не установлен. Установка...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
                    self.progress_update.emit("yt-dlp успешно установлен")
                    import yt_dlp
                except Exception as e:
                    self.progress_update.emit(f"Ошибка при установке yt-dlp: {e}")
                    self.download_finished.emit(False, "Ошибка установки yt-dlp")
                    return
            
            video_id = get_vk_video_id(self.video_url)
            
            if not video_id:
                self.progress_update.emit("Неверный формат ID или URL видео")
                self.download_finished.emit(False, "Неверный формат URL")
                return
            
            # Формируем URL для скачивания
            if "clip-" in video_id:
                url = f"https://vk.com/{video_id}"
            else:
                url = f"https://vk.com/video{video_id}"
            
            self.progress_update.emit(f"Начинаем скачивание видео: {url}")
            
            # Настраиваем опции для yt-dlp
            ydl_opts = {
                'format': 'best',
                'noplaylist': True,
                'progress_hooks': [self.progress_hook],
                'logger': MyLogger(self.progress_update),
            }
            
            # Устанавливаем директорию для скачивания, если указана
            if self.output_dir:
                ydl_opts['outtmpl'] = os.path.join(self.output_dir, '%(title)s.%(ext)s')
            else:
                ydl_opts['outtmpl'] = '%(title)s.%(ext)s'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = f"{info['title']}.{info.get('ext', 'mp4')}"
                if self.output_dir:
                    full_path = os.path.join(self.output_dir, filename)
                else:
                    full_path = os.path.abspath(filename)
                    
                self.progress_update.emit(f"Видео успешно скачано: {filename}")
                self.download_finished.emit(True, full_path)
                
        except Exception as e:
            self.progress_update.emit(f"Ошибка при скачивании видео: {e}")
            self.download_finished.emit(False, str(e))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'Неизвестно')
            speed = d.get('_speed_str', 'Неизвестно')
            eta = d.get('_eta_str', 'Неизвестно')
            self.progress_update.emit(f"Загрузка: {percent} | Скорость: {speed} | Осталось: {eta}")


# Функция удаления ANSI-кодов цветов из строки
def strip_ansi_codes(s):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', s)


class MyLogger:
    """Кастомный логгер для yt-dlp, передающий сообщения в сигнал Qt"""
    def __init__(self, signal):
        self.signal = signal
        
    def debug(self, msg):
        if msg.startswith('[download]'):
            # Удаляем ANSI-коды из сообщения
            clean_msg = strip_ansi_codes(msg)
            self.signal.emit(clean_msg)
    
    def info(self, msg):
        # Удаляем ANSI-коды из сообщения
        clean_msg = strip_ansi_codes(msg)
        self.signal.emit(clean_msg)
    
    def warning(self, msg):
        # Удаляем ANSI-коды из сообщения
        clean_msg = strip_ansi_codes(msg)
        self.signal.emit(f"Предупреждение: {clean_msg}")
    
    def error(self, msg):
        # Удаляем ANSI-коды из сообщения
        clean_msg = strip_ansi_codes(msg)
        self.signal.emit(f"Ошибка: {clean_msg}")


class VKVideoDownloaderApp(QMainWindow):
    """Основной класс графического приложения"""
    def __init__(self):
        super().__init__()
        self.initUI()
        self.download_thread = None
        self.output_directory = None
        
    def initUI(self):
        # Настройка окна
        self.setWindowTitle(f"VK Video Downloader v{__version__}")
        self.setMinimumSize(600, 400)
        
        # Создаем центральный виджет и основное расположение
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
                
        # Поле ввода URL видео
        url_layout = QHBoxLayout()
        url_label = QLabel("URL видео:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Вставьте ссылку на видео ВКонтакте")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)
        
        # Кнопки действий
        buttons_layout = QHBoxLayout()
        
        self.select_dir_button = QPushButton("Выбрать папку")
        self.select_dir_button.setMinimumHeight(30)
        self.select_dir_button.clicked.connect(self.select_output_directory)
        
        self.download_button = QPushButton("Скачать видео")
        self.download_button.setMinimumHeight(40)  # Больше высота
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                font-size: 14px;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.download_button.clicked.connect(self.start_download)
        
        buttons_layout.addWidget(self.select_dir_button)
        buttons_layout.addWidget(self.download_button)
        main_layout.addLayout(buttons_layout)
        
        # Информация о выбранной директории
        self.dir_info_label = QLabel("Папка для сохранения: не выбрана")
        main_layout.addWidget(self.dir_info_label)
        
        # Индикатор прогресса
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)  # Бесконечный прогресс
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)
        
        # Область для логов
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #f0f0f0; font-family: monospace;")
        main_layout.addWidget(self.log_area)
        
        # Строка состояния
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Готово к работе")
    
    def select_output_directory(self):
        """Выбор директории для сохранения видео"""
        dir_path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if dir_path:
            self.output_directory = dir_path
            self.dir_info_label.setText(f"Папка для сохранения: {dir_path}")
            self.statusbar.showMessage(f"Выбрана папка: {dir_path}")
            
    def start_download(self):
        """Начать процесс скачивания"""
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите URL видео")
            return
            
        # Деактивируем элементы управления
        self.url_input.setEnabled(False)
        self.download_button.setEnabled(False)
        self.select_dir_button.setEnabled(False)
        
        # Показываем индикатор прогресса
        self.progress_bar.show()
        self.statusbar.showMessage("Скачивание...")
        
        # Начинаем скачивание в отдельном потоке
        self.download_thread = DownloadThread(url, self.output_directory)
        self.download_thread.progress_update.connect(self.update_log)
        self.download_thread.download_finished.connect(self.download_complete)
        self.download_thread.start()
        
    def update_log(self, message):
        """Обновление лога с информацией"""
        # Дополнительная обработка сообщения для удаления ANSI-кодов
        message = strip_ansi_codes(message)
        self.log_area.append(message)
        # Прокрутка к концу
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())
        
    def download_complete(self, success, message):
        """Обработка завершения скачивания"""
        # Скрываем прогресс-бар
        self.progress_bar.hide()
        
        # Активируем элементы управления
        self.url_input.setEnabled(True)
        self.download_button.setEnabled(True)
        self.select_dir_button.setEnabled(True)
        
        if success:
            self.statusbar.showMessage("Скачивание успешно завершено")
            # Спрашиваем пользователя, хочет ли он открыть папку с видео
            reply = QMessageBox.question(self, 'Скачивание завершено', 
                                          f'Видео успешно скачано.\nОткрыть папку с файлом?',
                                          QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                # Открываем папку с файлом
                file_path = message
                directory = os.path.dirname(file_path)
                if sys.platform == 'win32':
                    os.startfile(directory)
                else:
                    opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                    subprocess.call([opener, directory])
        else:
            self.statusbar.showMessage("Ошибка при скачивании")
            QMessageBox.critical(self, "Ошибка", f"Не удалось скачать видео: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Используем стиль Fusion для единообразия на разных платформах
    
    # Устанавливаем иконку приложения, если файл существует
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = VKVideoDownloaderApp()
    window.show()
    
    sys.exit(app.exec_())