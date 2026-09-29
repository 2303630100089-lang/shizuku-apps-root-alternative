"""Telegram and Discord Release Announcer Bot.

Sends rich notification webhooks when new APKs are mirrored or new Shizuku apps are discovered.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

logger = logging.getLogger("release-announcer")


def send_telegram_message(
    bot_token: str,
    chat_id: str,
    text: str,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = False,
) -> bool:
    """Send a notification message via Telegram Bot API."""
    if not bot_token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
    }

    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=15) as resp:
            data = json.load(resp)
            return bool(data.get("ok"))
    except Exception as exc:
        logger.warning("Telegram notification failed: %s", exc)
        return False


def send_discord_webhook(webhook_url: str, title: str, description: str, fields: list[dict[str, Any]], color: int = 0x2563EB) -> bool:
    """Send an embed notification via Discord Webhook."""
    if not webhook_url:
        return False

    payload = {
        "username": "Shizuku APK Bot",
        "avatar_url": "https://raw.githubusercontent.com/krishna3163/best_shizuku_apps_for_android_no_root/main/assets/icon.png",
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color,
                "fields": fields,
                "footer": {"text": "Best Shizuku Apps Mirror • Automated CI"},
            }
        ],
    }

    req = Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Shizuku-Discord-Bot/1.0"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=15) as resp:
            return resp.status in {200, 204}
    except Exception as exc:
        logger.warning("Discord webhook failed: %s", exc)
        return False


def notify_new_release(
    app_name: str,
    version: str,
    download_url: str,
    source_repo: str,
    sha256: str = "",
    architectures: str = "Universal",
) -> None:
    """Send release announcement across configured channels."""
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    discord_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

    # Telegram format (HTML)
    tg_text = (
        f"🚀 <b>New APK Mirrored: {app_name} {version}</b>\n\n"
        f"📱 <b>Architectures:</b> <code>{architectures}</code>\n"
        f"📦 <b>Upstream:</b> <a href='https://github.com/{source_repo}'>{source_repo}</a>\n"
        f"⬇️ <b>Direct Download:</b> <a href='{download_url}'>Get APK</a>\n"
    )
    if sha256:
        tg_text += f"🔐 <b>SHA-256:</b> <code>{sha256[:16]}...</code>\n"

    tg_text += "\n🌐 <a href='https://github.com/krishna3163/best_shizuku_apps_for_android_no_root'>View Best Shizuku Apps Catalog</a>"

    if tg_token and tg_chat:
        send_telegram_message(tg_token, tg_chat, tg_text)
        logger.info("Sent Telegram release announcement for %s %s", app_name, version)

    # Discord format (Embed)
    if discord_url:
        discord_fields = [
            {"name": "Version", "value": f"`{version}`", "inline": True},
            {"name": "Architectures", "value": f"`{architectures}`", "inline": True},
            {"name": "Upstream Repo", "value": f"[{source_repo}](https://github.com/{source_repo})", "inline": False},
            {"name": "Download Link", "value": f"[Download Mirrored APK]({download_url})", "inline": False},
        ]
        if sha256:
            discord_fields.append({"name": "SHA-256", "value": f"`{sha256}`", "inline": False})

        send_discord_webhook(
            discord_url,
            title=f"📦 {app_name} {version} Released",
            description="A new verified APK has been mirrored and is ready for non-rooted Android devices.",
            fields=discord_fields,
            color=0x10B981,
        )
        logger.info("Sent Discord webhook announcement for %s %s", app_name, version)


def main() -> int:
    parser = argparse.ArgumentParser(description="Send release announcements to Telegram/Discord.")
    parser.add_argument("--app", required=True, help="App name")
    parser.add_argument("--version", required=True, help="Release version")
    parser.add_argument("--url", required=True, help="Download URL")
    parser.add_argument("--repo", default="upstream/repo", help="Source repository slug")
    parser.add_argument("--sha256", default="", help="APK SHA-256 hash")
    parser.add_argument("--arch", default="Universal", help="Architectures")
    args = parser.parse_args()

    notify_new_release(
        app_name=args.app,
        version=args.version,
        download_url=args.url,
        source_repo=args.repo,
        sha256=args.sha256,
        architectures=args.arch,
    )
    print("Notification process complete.")
    return 0


if __name__ == "__main__":
    main()
