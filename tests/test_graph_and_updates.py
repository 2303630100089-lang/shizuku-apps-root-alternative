"""Unit tests for graph and recent updates automation."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from graph import (
    generate_mermaid_diagram,
    generate_svg_chart,
    parse_catalog_stats,
)
from recent_updates import generate_recent_updates_table


class TestGraphAutomation(unittest.TestCase):
    """Test catalog analytics and SVG graph generation."""

    def test_parse_catalog_stats(self):
        stats = parse_catalog_stats(ROOT / "README.md")
        self.assertIn("categories", stats)
        self.assertGreater(stats["total_apps"], 100)
        self.assertGreater(stats["total_categories"], 15)
        self.assertGreater(stats["foss_pct"], 80.0)

    def test_generate_svg_chart(self):
        stats = parse_catalog_stats(ROOT / "README.md")
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = Path(tmpdir) / "test.svg"
            svg_content = generate_svg_chart(stats, svg_path)
            self.assertTrue(svg_path.exists())
            self.assertIn("<svg", svg_content)
            self.assertIn("Shizuku Catalog Analytics", svg_content)
            self.assertIn("FOSS", svg_content)

    def test_generate_mermaid_diagram(self):
        stats = parse_catalog_stats(ROOT / "README.md")
        mermaid = generate_mermaid_diagram(stats)
        self.assertIn("```mermaid", mermaid)
        self.assertIn("pie title App Category Breakdown", mermaid)


class TestRecentUpdates(unittest.TestCase):
    """Test recent updates table generation."""

    def test_generate_recent_updates_table(self):
        releases_path = ROOT / "data" / "releases.json"
        config_path = ROOT / "config" / "apps.json"

        with open(releases_path, encoding="utf-8") as fh:
            releases = json.load(fh)
        with open(config_path, encoding="utf-8") as fh:
            apps = json.load(fh).get("apps", [])

        table = generate_recent_updates_table(releases, apps, limit=5)
        self.assertIn('<details id="recent-updates">', table)
        self.assertIn("🔥 Recently Updated Apps", table)
        self.assertIn("| App | Developer | Version | Released | APK | Upstream |", table)
        self.assertIn("⚡", table)


if __name__ == "__main__":
    unittest.main()
