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
import json
import urllib.request
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QPushButton, QProgressBar, 
                            QTextEdit, QFileDialog, QMessageBox, QStatusBar,
                            QMenuBar, QMenu, QAction)
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition, Qt
from PyQt5.QtGui import QIcon

# Импортируем функциональность из оригинального скрипта
from vk_video_downloader import normalize_vk_url
from version import __version__

# URL для проверки обновлений (API GitHub)
UPDATE_URL = "https://api.github.com/repos/Fellmonkey/vk_video_downloader/releases/latest"

class UpdateCheckerThread(QThread):
    """Поток для проверки наличия обновлений"""
    update_available = pyqtSignal(str, str)
    no_update = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
        
    def run(self):
        try:
            # Делаем запрос к GitHub API
            with urllib.request.urlopen(UPDATE_URL) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode())
                    latest_version = data.get('tag_name', '').strip('v')
                    
                    if latest_version and self._compare_versions(latest_version, self.current_version):
                        download_url = data.get('assets', [{}])[0].get('browser_download_url', '')
                        self.update_available.emit(latest_version, download_url)
                    else:
                        self.no_update.emit()
                else:
                    self.error.emit(f"Ошибка запроса: {response.getcode()}")
        except Exception as e:
            self.error.emit(f"Ошибка проверки обновлений: {str(e)}")
            
    def _compare_versions(self, latest, current):
        """Сравнивает версии в формате x.y.z"""
        try:
            latest_parts = list(map(int, latest.split('.')))
            current_parts = list(map(int, current.split('.')))
            
            # Дополняем нулями, если одна версия короче другой
            while len(latest_parts) < len(current_parts):
                latest_parts.append(0)
            while len(current_parts) < len(latest_parts):
                current_parts.append(0)
                
            # Сравниваем поэлементно
            for i in range(len(latest_parts)):
                if latest_parts[i] > current_parts[i]:
                    return True
                elif latest_parts[i] < current_parts[i]:
                    return False
            
            return False  # Версии равны
        except:
            # Если что-то не так с форматом версий, считаем, что обновление не требуется
            return False

class DownloadThread(QThread):
    """Отдельный поток для скачивания видео"""
    progress_update = pyqtSignal(str)
    download_finished = pyqtSignal(bool, str)
    
    def __init__(self, video_url, output_dir=None):
        super().__init__()
        self.video_url = video_url
        self.output_dir = output_dir
        self.mutex = QMutex()
        self.pause_condition = QWaitCondition()
        self.is_paused = False
        self.is_cancelled = False
        self.ydl = None
        
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
            
            video_url = normalize_vk_url(self.video_url)
            
            if not video_url:
                self.progress_update.emit("Неверный формат ID или URL видео")
                self.download_finished.emit(False, "Неверный формат URL")
                return
            
            self.progress_update.emit(f"Начинаем скачивание видео: {video_url}")
            
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
                self.ydl = ydl
                
                # Проверка на отмену перед началом скачивания
                if self.is_cancelled:
                    self.progress_update.emit("Скачивание отменено")
                    self.download_finished.emit(False, "Отменено пользователем")
                    return
                    
                info = ydl.extract_info(video_url, download=True)
                
                # Если скачивание было отменено во время загрузки
                if self.is_cancelled:
                    self.progress_update.emit("Скачивание отменено")
                    self.download_finished.emit(False, "Отменено пользователем")
                    return
                
                filename = f"{info['title']}.{info.get('ext', 'mp4')}"
                if self.output_dir:
                    full_path = os.path.join(self.output_dir, filename)
                else:
                    full_path = os.path.abspath(filename)
                    
                self.progress_update.emit(f"Видео успешно скачано: {filename}")
                self.download_finished.emit(True, full_path)
                
        except Exception as e:
            if self.is_cancelled:
                self.progress_update.emit("Скачивание отменено")
                self.download_finished.emit(False, "Отменено пользователем")
            else:
                self.progress_update.emit(f"Ошибка при скачивании видео: {e}")
                self.download_finished.emit(False, str(e))

    def progress_hook(self, d):
        # Проверяем на паузу и отмену
        self.mutex.lock()
        if self.is_paused:
            self.pause_condition.wait(self.mutex)
        is_cancelled_now = self.is_cancelled
        self.mutex.unlock()
        
        if is_cancelled_now:
            raise Exception("Downloading cancelled by user")
            
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'Неизвестно')
            speed = d.get('_speed_str', 'Неизвестно')
            eta = d.get('_eta_str', 'Неизвестно')
            self.progress_update.emit(f"Загрузка: {percent} | Скорость: {speed} | Осталось: {eta}")
    
    def pause_download(self):
        """Поставить скачивание на паузу"""
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()
        self.progress_update.emit("Скачивание приостановлено")
        
    def resume_download(self):
        """Возобновить скачивание"""
        self.mutex.lock()
        self.is_paused = False
        self.mutex.unlock()
        self.pause_condition.wakeAll()
        self.progress_update.emit("Скачивание возобновлено")
        
    def cancel_download(self):
        """Отменить скачивание"""
        self.mutex.lock()
        self.is_cancelled = True
        self.is_paused = False
        self.mutex.unlock()
        self.pause_condition.wakeAll()
        
        # Пытаемся остановить yt-dlp, если он запущен
        if self.ydl and hasattr(self.ydl, 'params') and hasattr(self.ydl.params, 'get'):
            # Отменяем через флаг, который проверяется в progress_hook
            self.progress_update.emit("Отменяем скачивание...")


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
        self.is_downloading = False
        self.is_paused = False
        
    def initUI(self):
        # Настройка окна
        self.setWindowTitle(f"VK Video Downloader v{__version__}")
        self.setMinimumSize(600, 400)
        
        # Создаем меню
        self.create_menu_bar()
        
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
        
        # Кнопка скачивания (которая будет меняться на "Пауза/Возобновить" и "Остановить")
        self.action_button = QPushButton("Скачать видео")
        self.action_button.setMinimumHeight(40)  # Больше высота
        self.action_button.setStyleSheet(self.get_download_button_style())
        self.action_button.clicked.connect(self.action_button_clicked)
        
        # Кнопка остановки, изначально скрыта
        self.stop_button = QPushButton("Остановить")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; 
                color: white; 
                font-weight: bold; 
                font-size: 14px;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.stop_button.clicked.connect(self.stop_download)
        self.stop_button.hide()  # Изначально скрыта
        
        buttons_layout.addWidget(self.select_dir_button)
        buttons_layout.addWidget(self.action_button)
        buttons_layout.addWidget(self.stop_button)
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
    
    def create_menu_bar(self):
        """Создание верхнего меню"""
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        
        # Меню Файл
        file_menu = QMenu("Файл", self)
        menu_bar.addMenu(file_menu)
        
        # Действие "Выбрать папку"
        select_dir_action = QAction("Выбрать папку...", self)
        select_dir_action.triggered.connect(self.select_output_directory)
        file_menu.addAction(select_dir_action)
        
        # Разделитель
        file_menu.addSeparator()
        
        # Действие "Выход"
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Справка
        help_menu = QMenu("Справка", self)
        menu_bar.addMenu(help_menu)
        
        # Действие "Проверить обновления"
        self.check_updates_action = QAction("Проверить обновления", self)
        self.check_updates_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(self.check_updates_action)
        
        # Действие "О программе"
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def get_download_button_style(self):
        """Стиль кнопки скачивания (зелёный)"""
        return """
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
        """
    
    def get_pause_resume_button_style(self):
        """Стиль кнопки паузы/возобновления (оранжевый)"""
        return """
            QPushButton {
                background-color: #f39c12; 
                color: white; 
                font-weight: bold; 
                font-size: 14px;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
    
    def check_for_updates(self):
        """Проверка наличия обновлений"""
        self.statusbar.showMessage("Проверка обновлений...")
        self.check_updates_action.setEnabled(False)
        
        # Запускаем поток проверки обновлений
        self.update_checker = UpdateCheckerThread(__version__)
        self.update_checker.update_available.connect(self.handle_update_available)
        self.update_checker.no_update.connect(self.handle_no_update)
        self.update_checker.error.connect(self.handle_update_error)
        self.update_checker.start()
    
    def handle_update_available(self, version, download_url):
        """Обработка наличия новой версии"""
        self.statusbar.showMessage(f"Доступна новая версия: {version}")
        self.check_updates_action.setEnabled(True)
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Доступно обновление")
        msg.setText(f"Доступна новая версия {version}!")
        msg.setInformativeText("Хотите загрузить обновление?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        if msg.exec_() == QMessageBox.Yes:
            # Открываем ссылку на скачивание в браузере
            import webbrowser
            webbrowser.open(download_url)
    
    def handle_no_update(self):
        """Обработка отсутствия обновлений"""
        self.statusbar.showMessage("У вас установлена последняя версия программы")
        self.check_updates_action.setEnabled(True)
        
        QMessageBox.information(self, "Обновление не требуется", 
                               "У вас установлена последняя версия программы")
    
    def handle_update_error(self, error_message):
        """Обработка ошибки при проверке обновлений"""
        self.statusbar.showMessage("Ошибка при проверке обновлений")
        self.check_updates_action.setEnabled(True)
        
        QMessageBox.warning(self, "Ошибка", 
                           f"Не удалось проверить обновления:\n{error_message}")
    
    def show_about_dialog(self):
        """Показать информацию о программе"""
        QMessageBox.about(self, "О программе", 
                         f"""<b>VK Video Downloader</b> v{__version__}
                         <p>Программа для скачивания видео из ВКонтакте</p>
                         <p>Создана с использованием Python, PyQt5 и yt-dlp</p>""")
    
    def select_output_directory(self):
        """Выбор директории для сохранения видео"""
        dir_path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if dir_path:
            self.output_directory = dir_path
            self.dir_info_label.setText(f"Папка для сохранения: {dir_path}")
            self.statusbar.showMessage(f"Выбрана папка: {dir_path}")
    
    def action_button_clicked(self):
        """Обработчик нажатия основной кнопки действия"""
        if not self.is_downloading:
            # Если не скачиваем - начать скачивание
            self.start_download()
        elif self.is_paused:
            # Если на паузе - возобновить
            self.resume_download()
        else:
            # Если скачиваем - поставить на паузу
            self.pause_download()
    
    def start_download(self):
        """Начать процесс скачивания"""
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите URL видео")
            return
            
        # Деактивируем элементы управления
        self.url_input.setEnabled(False)
        self.select_dir_button.setEnabled(False)
        
        # Меняем кнопку на "Пауза"
        self.action_button.setText("Пауза")
        self.action_button.setStyleSheet(self.get_pause_resume_button_style())
        
        # Показываем кнопку остановки
        self.stop_button.show()
        
        self.is_downloading = True
        self.is_paused = False
        
        # Показываем индикатор прогресса
        self.progress_bar.show()
        self.statusbar.showMessage("Скачивание...")
        
        # Начинаем скачивание в отдельном потоке
        self.download_thread = DownloadThread(url, self.output_directory)
        self.download_thread.progress_update.connect(self.update_log)
        self.download_thread.download_finished.connect(self.download_complete)
        self.download_thread.start()
    
    def pause_download(self):
        """Поставить скачивание на паузу"""
        if self.download_thread:
            self.download_thread.pause_download()
            self.action_button.setText("Возобновить")
            self.statusbar.showMessage("Загрузка приостановлена")
            self.is_paused = True
    
    def resume_download(self):
        """Возобновить скачивание после паузы"""
        if self.download_thread:
            self.download_thread.resume_download()
            self.action_button.setText("Пауза")
            self.statusbar.showMessage("Загрузка возобновлена")
            self.is_paused = False
    
    def stop_download(self):
        """Остановить скачивание"""
        if self.download_thread:
            # Запрашиваем подтверждение через QMessageBox.question
            reply = QMessageBox.question(self, "Остановка загрузки", 
                                         "Вы уверены, что хотите отменить загрузку?",
                                         QMessageBox.Yes | QMessageBox.No, 
                                         QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.download_thread.cancel_download()
                self.statusbar.showMessage("Отмена загрузки...")
    
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
        
        # Восстанавливаем кнопки
        self.action_button.setText("Скачать видео")
        self.action_button.setStyleSheet(self.get_download_button_style())
        self.stop_button.hide()
        
        # Активируем элементы управления
        self.url_input.setEnabled(True)
        self.select_dir_button.setEnabled(True)
        self.is_downloading = False
        self.is_paused = False
        
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
            if "Отменено пользователем" in message:
                self.statusbar.showMessage("Скачивание отменено пользователем")
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