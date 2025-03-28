# VK Video Downloader

![GitHub release (latest by date)](https://img.shields.io/github/v/release/Fellmonkey/vk_video_downloader)
![Downloads](https://img.shields.io/github/downloads/Fellmonkey/vk_video_downloader/total)

Загрузок: 0

Программа для скачивания видео из ВКонтакте с графическим интерфейсом. Поддерживает скачивание обычных видео и клипов.

## Возможности

- 📥 Скачивание видео из ВКонтакте по ссылке или ID
- 🎬 Поддержка обычных видео и клипов
- 👀 Удобный графический интерфейс
- 📊 Отображение прогресса загрузки
- 💾 Выбор папки для сохранения
- 🔄 Автоматическое обновление зависимостей
- 📝 Подробный лог процесса загрузки

## Установка

1. Скачайте последнюю версию программы из раздела [Releases](https://github.com/Fellmonkey/vk_video_downloader/releases)
2. Распакуйте архив в удобное место
3. Запустите `VK_Video_Downloader.exe`

## Использование

1. Запустите программу
2. Вставьте ссылку на видео или его ID в поле "URL видео или ID"
3. При необходимости измените папку сохранения, нажав кнопку "Обзор..."
4. Нажмите кнопку "Скачать видео"
5. Дождитесь окончания загрузки

### Поддерживаемые форматы ссылок

- Полные ссылки на видео: `https://vk.com/video123456_123456`
- Ссылки на клипы: `https://vk.com/clip-123456_123456`
- ID видео: `123456_123456`
- ID клипа: `clip-123456_123456`

---

## Разработка

### Требования

- Python 3.9+
- PyQt5
- yt-dlp
- PyInstaller (для сборки)

### Сборка из исходного кода

```bash
python build_exe.py
```

## Версионирование

Проект использует семантическое версионирование (SemVer). Версия обновляется автоматически при каждом push в ветку main.

### Как работает версионирование:

1. Версия хранится в файле `version.py`
2. При push в main GitHub Actions автоматически:
   - Увеличивает patch-версию (например, 1.0.0 -> 1.0.1)
   - Обновляет версию в исходном коде
   - Создает новый релиз с обновленной версией

### Ручное управление версией:

Для ручного обновления версии используйте скрипт `update_version.py`:

```bash
# Обновить patch-версию (1.0.0 -> 1.0.1)
python update_version.py patch

# Обновить minor-версию (1.0.1 -> 1.1.0)
python update_version.py minor

# Обновить major-версию (1.1.0 -> 2.0.0)
python update_version.py major
```