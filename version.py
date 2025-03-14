#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Файл управления версией проекта VK Video Downloader
Следует принципам семантического версионирования (SemVer)
"""

VERSION = {
    'major': 1,
    'minor': 0,
    'patch': 5,
}

__version__ = f"{VERSION['major']}.{VERSION['minor']}.{VERSION['patch']}"

if __name__ == "__main__":
    print(__version__)