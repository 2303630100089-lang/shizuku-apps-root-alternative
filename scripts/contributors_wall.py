"""Dynamic Stargazers & Contributors Wall Generator.

Generates assets/contributors.svg with circular avatar grid and contributor statistics.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

logger = logging.getLogger("contributors-wall")
ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"
SVG_PATH = ASSETS_DIR / "contributors.svg"


def fetch_contributors(repo_slug: str, token: Optional[str] = None) -> list[dict[str, Any]]:
    """Fetch contributors list from GitHub API."""
    token = token or os.environ.get("GITHUB_TOKEN", "").strip()
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Shizuku-Contributors-Wall/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{repo_slug}/contributors?per_page=100"
    req = Request(url, headers=headers)

    try:
        with urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except Exception as exc:
        logger.warning("Could not fetch contributors from GitHub: %s", exc)
        return []


def generate_svg(contributors: list[dict[str, Any]]) -> str:
    """Generate SVG image featuring contributors."""
    if not contributors:
        # Default placeholder if API is offline
        contributors = [
            {"login": "krishna3163", "avatar_url": "https://github.com/krishna3163.png", "contributions": 100},
            {"login": "RikkaApps", "avatar_url": "https://github.com/RikkaApps.png", "contributions": 50},
            {"login": "timschneeb", "avatar_url": "https://github.com/timschneeb.png", "contributions": 30},
        ]

    card_width = 800
    avatar_size = 54
    padding = 18
    per_row = (card_width - padding * 2) // (avatar_size + padding)
    rows = (len(contributors) + per_row - 1) // per_row
    card_height = max(160, 90 + (rows * (avatar_size + padding)))

    svg_elements = [
        f'<svg xmlns="http://www.w3.org/2005/svg" width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}" fill="none">',
        '  <style>',
        '    .title { font: 700 18px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; fill: #0f172a; }',
        '    .subtitle { font: 400 13px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; fill: #64748b; }',
        '    .avatar-bg { fill: #f1f5f9; stroke: #e2e8f0; stroke-width: 2px; }',
        '    .avatar-border { stroke: #3b82f6; stroke-width: 2px; rx: 27px; }',
        '    .handle { font: 600 11px sans-serif; fill: #1e293b; text-anchor: middle; }',
        '    @media (prefers-color-scheme: dark) {',
        '      .title { fill: #f8fafc; }',
        '      .subtitle { fill: #94a3b8; }',
        '      .avatar-bg { fill: #1e293b; stroke: #334155; }',
        '      .handle { fill: #f1f5f9; }',
        '    }',
        '  </style>',
        f'  <rect width="{card_width}" height="{card_height}" rx="14" fill="#ffffff" fill-opacity="0.05" stroke="#cbd5e1" stroke-width="1"/>',
        '  <text x="24" y="38" class="title">👥 Project Contributors &amp; Community Heroes</text>',
        f'  <text x="24" y="58" class="subtitle">Thank you to everyone helping curate and build the Android Shizuku ecosystem! ({len(contributors)} active contributors)</text>',
    ]

    for idx, c in enumerate(contributors):
        row = idx // per_row
        col = idx % per_row
        x = padding + 10 + col * (avatar_size + padding + 15)
        y = 80 + row * (avatar_size + padding + 15)
        login = c.get("login", "")
        avatar = c.get("avatar_url", "")

        clip_id = f"clip-{idx}"
        svg_elements.extend([
            f'  <defs>',
            f'    <clipPath id="{clip_id}">',
            f'      <circle cx="{x + 27}" cy="{y + 27}" r="26"/>',
            f'    </clipPath>',
            f'  </defs>',
            f'  <a href="https://github.com/{login}" target="_blank">',
            f'    <circle cx="{x + 27}" cy="{y + 27}" r="27" class="avatar-bg"/>',
            f'    <image x="{x}" y="{y}" width="{avatar_size}" height="{avatar_size}" href="{avatar}" clip-path="url(#{clip_id})"/>',
            f'    <circle cx="{x + 27}" cy="{y + 27}" r="26" fill="none" stroke="#60a5fa" stroke-width="2"/>',
            f'    <text x="{x + 27}" y="{y + avatar_size + 14}" class="handle">{login[:10]}</text>',
            f'  </a>',
        ])

    svg_elements.append("</svg>")
    return "\n".join(svg_elements)


def update_contributors_wall(repo_slug: str, token: Optional[str] = None) -> Path:
    """Fetch contributors and save SVG."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    contributors = fetch_contributors(repo_slug, token=token)
    svg_content = generate_svg(contributors)
    SVG_PATH.write_text(svg_content, encoding="utf-8")
    return SVG_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate contributors wall SVG.")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "krishna3163/best_shizuku_apps_for_android_no_root"))
    parser.add_argument("--token", help="GitHub API Token")
    args = parser.parse_args()

    out = update_contributors_wall(args.repo, token=args.token)
    print(f"✅ Generated contributors wall at {out}")
    return 0


if __name__ == "__main__":
    main()
