"""Catalog graph and analytics automation for the Shizuku app repository.

Analyzes the app catalog, generates dynamic SVG distribution graphs, and
embeds interactive statistics and charts into README.md.
"""

from __future__ import annotations

import argparse
import html
import logging
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
ASSETS_DIR = ROOT / "assets"
SVG_PATH = ASSETS_DIR / "category-distribution.svg"

START_MARKER = "<!-- STATS-GRAPH-START -->"
END_MARKER = "<!-- STATS-GRAPH-END -->"

ROW = re.compile(r"^\| ([^|]+) \| ([^|]+) \| ([^|]+) \| (.+) \|\s*$")
HEADING = re.compile(r"^(#{2,3})\s+(.+)$")

logger = logging.getLogger("graph-automation")

BAR_COLORS = [
    ("#6366f1", "#4f46e5"),  # Indigo
    ("#3b82f6", "#2563eb"),  # Blue
    ("#06b6d4", "#0891b2"),  # Cyan
    ("#10b981", "#059669"),  # Emerald
    ("#f59e0b", "#d97706"),  # Amber
    ("#ef4444", "#dc2626"),  # Red
    ("#8b5cf6", "#7c3aed"),  # Purple
    ("#ec4899", "#db2777"),  # Pink
    ("#14b8a6", "#0d9488"),  # Teal
    ("#64748b", "#475569"),  # Slate / Others
]


def parse_catalog_stats(readme_path: Path = README_PATH) -> dict[str, Any]:
    """Parse category counts, license counts, and total apps from README.md."""
    content = readme_path.read_text(encoding="utf-8")
    categories = Counter()
    licenses = Counter()
    current_cat = "General"
    in_apps = False

    for line in content.splitlines():
        if line.startswith("## Apps"):
            in_apps = True
            continue
        if in_apps and line.startswith("## ") and not line.startswith("## Apps"):
            in_apps = False

        hm = HEADING.match(line)
        if in_apps and hm:
            current_cat = re.sub(r"^[^\w\s]+", "", hm.group(2)).strip()
            continue

        rm = ROW.match(line)
        if in_apps and rm:
            name = rm.group(1).strip()
            desc = rm.group(2).strip()
            lic = rm.group(3).strip()
            if name in {"App", "---", ":---", "Library"} or desc == "Description":
                continue
            categories[current_cat] += 1
            if lic:
                licenses[lic] += 1

    total_apps = sum(categories.values())
    foss_count = sum(count for lic, count in licenses.items() if "Proprietary" not in lic)
    foss_pct = round((foss_count / total_apps * 100), 1) if total_apps else 100.0

    return {
        "categories": categories,
        "licenses": licenses,
        "total_apps": total_apps,
        "total_categories": len(categories),
        "foss_pct": foss_pct,
    }


def generate_svg_chart(stats: dict[str, Any], output_path: Path = SVG_PATH) -> str:
    """Generate a modern dark-themed SVG horizontal bar chart."""
    categories: Counter = stats["categories"]
    total_apps = stats["total_apps"]
    total_cats = stats["total_categories"]
    foss_pct = stats["foss_pct"]

    top_n = 8
    most_common = categories.most_common(top_n)
    other_count = total_apps - sum(c for _, c in most_common)

    items = list(most_common)
    if other_count > 0:
        items.append((f"Other Categories ({total_cats - top_n})", other_count))

    width = 860
    item_height = 36
    header_height = 85
    footer_height = 65
    height = header_height + (len(items) * item_height) + footer_height

    label_x = 240
    bar_x = 250
    bar_max_width = 460
    max_val = max(c for _, c in items) if items else 1

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" style="background: transparent; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif;">',
        "  <defs>",
        '    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#0d1117" />',
        '      <stop offset="100%" stop-color="#161b22" />',
        "    </linearGradient>",
    ]

    for i, (c1, c2) in enumerate(BAR_COLORS):
        svg_lines.append(
            f'    <linearGradient id="barGrad{i}" x1="0%" y1="0%" x2="100%" y2="0%">'
            f'<stop offset="0%" stop-color="{c1}" />'
            f'<stop offset="100%" stop-color="{c2}" />'
            f"</linearGradient>"
        )

    svg_lines.extend([
        "  </defs>",
        f'  <rect width="{width}" height="{height}" rx="12" fill="url(#bgGrad)" stroke="#30363d" stroke-width="1.5" />',
        '  <text x="30" y="42" fill="#58a6ff" font-size="20" font-weight="700">📊 Shizuku Catalog Analytics</text>',
        f'  <text x="30" y="66" fill="#8b949e" font-size="13">Curated App Category Distribution · {total_apps} Apps across {total_cats} Categories</text>',
        f'  <rect x="{width - 150}" y="26" width="120" height="26" rx="13" fill="#238636" fill-opacity="0.25" stroke="#2ea043" stroke-width="1" />',
        f'  <text x="{width - 90}" y="43" fill="#3fb950" font-size="12" font-weight="600" text-anchor="middle">🔓 {foss_pct}% FOSS</text>',
    ])

    # Draw bars
    y_start = header_height + 15
    for i, (name, count) in enumerate(items):
        y = y_start + (i * item_height)
        pct = (count / total_apps * 100) if total_apps else 0
        bar_w = max(10, int((count / max_val) * bar_max_width))
        color_id = f"barGrad{i % len(BAR_COLORS)}"

        # Category label
        svg_lines.append(
            f'  <text x="{label_x}" y="{y + 16}" fill="#c9d1d9" font-size="13" font-weight="500" text-anchor="end">{html.escape(name)}</text>'
        )
        # Background track
        svg_lines.append(
            f'  <rect x="{bar_x}" y="{y}" width="{bar_max_width}" height="22" rx="6" fill="#21262d" />'
        )
        # Filled bar
        svg_lines.append(
            f'  <rect x="{bar_x}" y="{y}" width="{bar_w}" height="22" rx="6" fill="url(#{color_id})" />'
        )
        # Count & percentage text
        svg_lines.append(
            f'  <text x="{bar_x + bar_max_width + 12}" y="{y + 16}" fill="#8b949e" font-size="12" font-weight="600">{count} <tspan fill="#6e7681" font-weight="400">({pct:.1f}%)</tspan></text>'
        )

    # Footer metrics
    footer_y = height - 25
    svg_lines.extend([
        f'  <line x1="30" y1="{height - 50}" x2="{width - 30}" y2="{height - 50}" stroke="#30363d" stroke-width="1" stroke-dasharray="4" />',
        f'  <text x="30" y="{footer_y}" fill="#8b949e" font-size="12">⚡ <tspan fill="#f0883e" font-weight="600">No-Root Required</tspan> via Wireless ADB</text>',
        f'  <text x="{width // 2}" y="{footer_y}" fill="#8b949e" font-size="12" text-anchor="middle">📦 <tspan fill="#58a6ff" font-weight="600">Automated APK Sync</tspan> Every 6 Hours</text>',
        f'  <text x="{width - 30}" y="{footer_y}" fill="#8b949e" font-size="12" text-anchor="end">🔄 <tspan fill="#3fb950" font-weight="600">Daily Discovery</tspan></text>',
        "</svg>",
    ])

    svg_content = "\n".join(svg_lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg_content, encoding="utf-8")
    return svg_content


def generate_mermaid_diagram(stats: dict[str, Any]) -> str:
    """Generate Mermaid pie diagram markup."""
    categories: Counter = stats["categories"]
    total = stats["total_apps"]
    top_n = 7
    items = categories.most_common(top_n)
    other = total - sum(c for _, c in items)

    lines = ["```mermaid", "pie title App Category Breakdown"]
    for name, count in items:
        clean_name = name.replace('"', '\\"')
        lines.append(f'    "{clean_name}" : {count}')
    if other > 0:
        lines.append(f'    "Other Categories" : {other}')
    lines.append("```")
    return "\n".join(lines)


def generate_stats_markdown(stats: dict[str, Any]) -> str:
    """Generate the full Markdown block for catalog analytics."""
    mermaid = generate_mermaid_diagram(stats)
    lines = [
        "",
        '<details id="catalog-analytics">',
        "<summary><h2>📊 Catalog Analytics & Distribution</h2></summary>",
        "",
        f"> Visual overview of the {stats['total_apps']} apps across {stats['total_categories']} categories in this repository.",
        "",
        '<p align="center">',
        '  <img src="assets/category-distribution.svg" alt="Category Distribution" width="100%" />',
        "</p>",
        "",
        "<details>",
        "<summary><b>📈 Interactive Mermaid Chart</b></summary>",
        "",
        mermaid,
        "",
        "</details>",
        "",
        "</details>",
        "",
    ]
    return "\n".join(lines)


def update_readme_stats() -> bool:
    """Update README.md between the stats graph markers."""
    if not README_PATH.exists():
        logger.warning("README.md not found at %s", README_PATH)
        return False

    stats = parse_catalog_stats(README_PATH)
    generate_svg_chart(stats, SVG_PATH)

    content = README_PATH.read_text(encoding="utf-8")
    if START_MARKER not in content or END_MARKER not in content:
        logger.warning("Stats graph markers not found in README.md")
        return False

    start_idx = content.index(START_MARKER) + len(START_MARKER)
    end_idx = content.index(END_MARKER)

    block = generate_stats_markdown(stats)
    new_content = content[:start_idx] + "\n" + block + content[end_idx:]

    if new_content == content:
        logger.info("README.md stats graph section is already up-to-date.")
        return False

    README_PATH.write_text(new_content, encoding="utf-8")
    logger.info("README.md updated with catalog graph and analytics.")
    return True


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Generate catalog graphs and update README")
    parser.add_argument("--check", action="store_true", help="Check if SVG and README are up-to-date")
    args = parser.parse_args()

    stats = parse_catalog_stats(README_PATH)
    if args.check:
        if not SVG_PATH.exists():
            print("ERROR: assets/category-distribution.svg missing")
            return 1
        content = README_PATH.read_text(encoding="utf-8")
        if START_MARKER not in content or END_MARKER not in content:
            print("ERROR: Markers missing in README.md")
            return 1
        start_idx = content.index(START_MARKER) + len(START_MARKER)
        end_idx = content.index(END_MARKER)
        expected = "\n" + generate_stats_markdown(stats)
        actual = content[start_idx:end_idx]
        if expected != actual:
            print("README.md stats graph block is outdated.")
            return 1
        print("Graph and stats are up to date.")
        return 0

    update_readme_stats()
    return 0


if __name__ == "__main__":
    sys.exit(main())
