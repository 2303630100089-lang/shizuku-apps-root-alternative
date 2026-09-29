"""Recent updates automation for the Shizuku app catalog.

Tracks and highlights the latest upstream releases and synchronized APKs.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
RELEASES_PATH = ROOT / "data" / "releases.json"
CONFIG_PATH = ROOT / "config" / "apps.json"

START_MARKER = "<!-- RECENT-UPDATES-START -->"
END_MARKER = "<!-- RECENT-UPDATES-END -->"

logger = logging.getLogger("recent-updates")


def _get_mirror_repo() -> str:
    """Detect mirror repo from environment or git remote."""
    import os
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo:
        return repo
    try:
        import subprocess
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        url = result.stdout.strip()
        match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "krishna3163/best_shizuku_apps_for_android_no_root"


def generate_recent_updates_table(
    releases_db: dict[str, Any],
    apps_config: list[dict[str, Any]],
    limit: int = 10,
) -> str:
    """Generate the markdown table for recent upstream releases."""
    mirror_repo = _get_mirror_repo()
    apps_by_slug = {a.get("slug"): a for a in apps_config}

    items = []
    for slug, rel in releases_db.items():
        app_cfg = apps_by_slug.get(slug, {})
        if not app_cfg.get("enabled", True):
            continue
        date_str = rel.get("source_published_at") or rel.get("synced_at") or ""
        if not date_str:
            continue
        items.append({
            "slug": slug,
            "name": app_cfg.get("name", slug.title()),
            "repo": rel.get("source_repository") or app_cfg.get("repository", ""),
            "tag": rel.get("source_tag", "unknown"),
            "date": date_str[:10],
            "datetime": date_str,
            "mirror_tag": rel.get("mirror_release_tag", ""),
            "assets": rel.get("assets", []),
        })

    # Sort descending by date
    items.sort(key=lambda x: x["datetime"], reverse=True)
    recent = items[:limit]

    lines = [
        "",
        '<details id="recent-updates">',
        "<summary><h2>🔥 Recently Updated Apps</h2></summary>",
        "",
        "> Automatically synced from upstream releases. Shows the latest new versions.",
        "",
        "| App | Developer | Version | Released | APK | Upstream |",
        "|:---|:---|:---|:---|:---|:---|",
    ]

    for item in recent:
        name = item["name"]
        repo = item["repo"]
        owner = repo.split("/")[0] if "/" in repo else "Unknown"
        version = item["tag"]
        date = item["date"]
        mirror_tag = item["mirror_tag"]

        if mirror_repo and mirror_tag:
            download_url = f"https://github.com/{mirror_repo}/releases/tag/{mirror_tag}"
            download_link = f"[⬇️ Download]({download_url})"
        else:
            download_link = "—"

        release_url = f"https://github.com/{repo}/releases"
        release_link = f"[Upstream]({release_url})"

        lines.append(
            f"| ⚡ **{name}** | {owner} | `{version}` | {date} | {download_link} | {release_link} |"
        )

    if not recent:
        lines.append("| _No recent updates tracked yet._ | — | — | — | — | — |")

    lines.append("")
    lines.append("</details>")
    lines.append("")
    return "\n".join(lines)


def update_recent_updates(limit: int = 10) -> bool:
    """Update README.md between the recent update markers."""
    if not README_PATH.exists():
        logger.warning("README.md not found at %s", README_PATH)
        return False
    if not RELEASES_PATH.exists():
        logger.warning("data/releases.json not found at %s", RELEASES_PATH)
        return False

    with open(RELEASES_PATH, encoding="utf-8") as fh:
        releases_db = json.load(fh)

    apps_config = []
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
            apps_config = data.get("apps", [])

    content = README_PATH.read_text(encoding="utf-8")
    if START_MARKER not in content or END_MARKER not in content:
        logger.warning("Recent updates markers not found in README.md")
        return False

    start_idx = content.index(START_MARKER) + len(START_MARKER)
    end_idx = content.index(END_MARKER)

    table = generate_recent_updates_table(releases_db, apps_config, limit=limit)
    new_content = content[:start_idx] + "\n" + table + content[end_idx:]

    if new_content == content:
        logger.info("README.md recent updates section is already up-to-date.")
        return False

    README_PATH.write_text(new_content, encoding="utf-8")
    logger.info("README.md updated with recent updates section.")
    return True


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Update recent updates table")
    parser.add_argument("--limit", type=int, default=10, help="Number of recent apps to show")
    parser.add_argument("--check", action="store_true", help="Check if up to date without writing")
    args = parser.parse_args()

    if args.check:
        with open(RELEASES_PATH, encoding="utf-8") as fh:
            releases_db = json.load(fh)
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            apps_config = json.load(fh).get("apps", [])
        content = README_PATH.read_text(encoding="utf-8")
        if START_MARKER not in content or END_MARKER not in content:
            print("ERROR: Markers missing")
            return 1
        start_idx = content.index(START_MARKER) + len(START_MARKER)
        end_idx = content.index(END_MARKER)
        expected = "\n" + generate_recent_updates_table(releases_db, apps_config, limit=args.limit)
        actual = content[start_idx:end_idx]
        if expected != actual:
            print("README.md recent updates section is outdated.")
            return 1
        print("README.md recent updates section is up to date.")
        return 0

    update_recent_updates(limit=args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
