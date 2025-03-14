#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для автоматического обновления версии
Используется в GitHub Actions для инкрементирования версии пакета
"""

import re
import sys
import os

def update_version(version_type='patch'):
    """
    Обновляет версию в файле version.py
    
    version_type: тип изменения версии ('major', 'minor', 'patch')
    """
    with open('version.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим текущие значения версии
    major_match = re.search(r"'major': (\d+)", content)
    minor_match = re.search(r"'minor': (\d+)", content)
    patch_match = re.search(r"'patch': (\d+)", content)
    
    if not all([major_match, minor_match, patch_match]):
        print("Error: Could not find all version components in version.py")
        return False
    
    major = int(major_match.group(1))
    minor = int(minor_match.group(1))
    patch = int(patch_match.group(1))
    
    # Обновляем версию в зависимости от типа изменения
    if version_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif version_type == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    # Заменяем значения версии в файле
    content = re.sub(r"'major': \d+", f"'major': {major}", content)
    content = re.sub(r"'minor': \d+", f"'minor': {minor}", content)
    content = re.sub(r"'patch': \d+", f"'patch': {patch}", content)
    
    with open('version.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Version updated to {major}.{minor}.{patch}")
    
    return f"{major}.{minor}.{patch}"

if __name__ == "__main__":
    version_type = 'patch'  # По умолчанию
    
    # Если передан аргумент, используем его как тип обновления версии
    if len(sys.argv) > 1:
        if sys.argv[1] in ['major', 'minor', 'patch']:
            version_type = sys.argv[1]
        else:
            print(f"Invalid version update type: {sys.argv[1]}")
            print("Use one of: 'major', 'minor', 'patch'")
            sys.exit(1)
    
    new_version = update_version(version_type)
    if new_version:
        # Используем новый формат вывода для GitHub Actions
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ.get('GITHUB_OUTPUT'), 'a') as f:
                f.write(f"new_version={new_version}\n")
        else:
            # Для обратной совместимости с старым форматом
            print(f"::set-output name=new_version::{new_version}")
    else:
        sys.exit(1)