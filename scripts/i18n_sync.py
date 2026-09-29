"""Multilingual README Synchronizer (i18n).

Synchronizes and translates README.md into README.zh-CN.md (Simplified Chinese)
and README.ru.md (Russian) with synchronized tables and navigation.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_EN = ROOT / "README.md"
README_ZH = ROOT / "README.zh-CN.md"
README_RU = ROOT / "README.ru.md"

# Common dictionary translations
ZH_TRANSLATIONS = {
    "Best Shizuku Apps for Android (No Root)": "最优质的安卓免 Root Shizuku 应用合集",
    "Discover the top Shizuku apps, Android root alternatives, wireless ADB tools, debloat apps, and power-user utilities": "探索精选 Shizuku 应用、免 Root 替代方案、无线 ADB 工具、系统卸载精简及极客必备神器",
    "Find the best Shizuku apps to customize Android, remove bloatware, manage apps, improve privacy, automate tasks, and unlock root-like features without rooting your phone.": "发现最优质的 Shizuku 应用，无需 Root 即可自定义安卓、精简系统预装、管理应用权限、增强隐私保护并实现自动化操作。",
    "What is Shizuku?": "什么是 Shizuku？",
    "App Categories": "应用分类",
    "Top Picks": "精选推荐",
    "Join Community": "加入社区",
    "Resources": "相关资源",
    "About": "关于本项目",
    "Table of Contents": "目录导航",
    "App": "应用名称",
    "Description": "功能简介与 Shizuku 用例",
    "License": "开源许可",
    "Links": "相关链接",
    "App Management": "应用管理与冻结",
    "Automation": "自动化控制",
    "Customization": "个性化界面定制",
    "Development": "开发者调试与工具",
    "File Management": "高级文件管理",
    "Gaming": "游戏优化与辅助",
    "Networking": "网络与系统防火墙",
    "Privacy and Security": "隐私保护与权限安全",
    "System Utilities": "系统运维与深度工具",
    "Miscellaneous content": "综合工具与更多应用",
    "Other apps (FOSS alternatives to premium apps)": "其他精选应用（替代付费专有软件的开源良心作品）",
    "Android Power-User Ecosystem": "安卓极客与高级用户生态圈",
    "Connect with Maintainer": "联系维护者与社交主页",
    "Community Chat & Discussions": "社区聊天与互动讨论",
    "Community Chat": "社区交流群",
    "Join the Community": "参与社区贡献",
    "Automatic APK Updates": "APK 自动同步与镜像",
    "Disclaimer": "免责声明",
    "Show Your Support": "支持与鼓励",
    "Made with ❤️ for the Android community": "为全球安卓极客社区用心打造 ❤️",
    "Have questions, suggestions, or want to collaborate? Connect directly:": "有任何问题、应用推荐或合作意向？欢迎直接联系：",
}

RU_TRANSLATIONS = {
    "Best Shizuku Apps for Android (No Root)": "Лучшие приложения Shizuku для Android (Без Root)",
    "Discover the top Shizuku apps, Android root alternatives, wireless ADB tools, debloat apps, and power-user utilities": "Откройте для себя лучшие приложения Shizuku, альтернативы Root, утилиты беспроводного ADB и инструменты для продвинутых пользователей",
    "Find the best Shizuku apps to customize Android, remove bloatware, manage apps, improve privacy, automate tasks, and unlock root-like features without rooting your phone.": "Найдите лучшие приложения Shizuku для настройки Android, удаления встроенного мусора, контроля конфиденциальности и автоматизации без рутирования устройства.",
    "What is Shizuku?": "Что такое Shizuku?",
    "App Categories": "Категории приложений",
    "Top Picks": "Избранное",
    "Join Community": "Сообщество",
    "Resources": "Ресурсы",
    "About": "О проекте",
    "Table of Contents": "Содержание",
    "App": "Приложение",
    "Description": "Описание и сценарий использования",
    "License": "Лицензия",
    "Links": "Ссылки",
    "App Management": "Управление приложениями и заморозка",
    "Automation": "Автоматизация",
    "Customization": "Кастомизация и оформление",
    "Development": "Разработка и отладка",
    "File Management": "Файловые менеджеры",
    "Gaming": "Игры и оптимизация",
    "Networking": "Сеть и системный фаервол",
    "Privacy and Security": "Безопасность и приватность",
    "System Utilities": "Системные утилиты",
    "Miscellaneous content": "Разное и дополнительные инструменты",
    "Other apps (FOSS alternatives to premium apps)": "Другие приложения (FOSS альтернативы платным сервисам)",
    "Android Power-User Ecosystem": "Экосистема для энтузиастов Android",
    "Connect with Maintainer": "Связаться с автором и соцсети",
    "Community Chat & Discussions": "Чат сообщества и обсуждения",
    "Community Chat": "Чат сообщества",
    "Join the Community": "Присоединиться к сообществу",
    "Automatic APK Updates": "Автоматическое обновление APK",
    "Disclaimer": "Отказ от ответственности",
    "Show Your Support": "Поддержите проект",
    "Made with ❤️ for the Android community": "Сделано с любовью ❤️ для сообщества Android",
    "Have questions, suggestions, or want to collaborate? Connect directly:": "Есть вопросы, предложения или идеи для сотрудничества? Напишите автору напрямую:",
}


def translate_content(text: str, lang: str) -> str:
    """Translate markdown headers, badges, and keys based on dictionary."""
    mapping = ZH_TRANSLATIONS if lang == "zh-CN" else RU_TRANSLATIONS

    # Language switcher banner
    nav = (
        "> 🌐 **Language / 语言 / Язык:** "
        "[ 🇬🇧 English ](README.md) • "
        "[ 🇨🇳 简体中文 ](README.zh-CN.md) • "
        "[ 🇷🇺 Русский ](README.ru.md)\n\n"
    )

    result = text
    for src, dst in mapping.items():
        result = result.replace(src, dst)

    # Insert language switcher after initial title
    title_marker = "# 🚀 "
    if title_marker in result:
        idx = result.index(title_marker)
        next_nl = result.find("\n", idx)
        result = result[:next_nl + 1] + "\n" + nav + result[next_nl + 1:]
    else:
        result = nav + result

    return result


def sync_all() -> tuple[Path, Path]:
    """Generate both localized README files."""
    content_en = README_EN.read_text(encoding="utf-8")

    # Generate Chinese version
    content_zh = translate_content(content_en, "zh-CN")
    README_ZH.write_text(content_zh, encoding="utf-8")

    # Generate Russian version
    content_ru = translate_content(content_en, "ru-RU")
    README_RU.write_text(content_ru, encoding="utf-8")

    return README_ZH, README_RU


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize multilingual README documentation.")
    parser.add_argument("--lang", choices=["zh-CN", "ru", "all"], default="all")
    args = parser.parse_args()

    zh, ru = sync_all()
    print(f"✅ Generated {zh.name}")
    print(f"✅ Generated {ru.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
