"""Comprehensive test suite for the 15 repository automations."""

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from virustotal import generate_vt_badge, generate_vt_summary
from archive_detector import extract_github_repos_from_text, generate_markdown_report
from verify_shizuku_api import SHIZUKU_SIGNATURES, verify_apk_file
from link_checker_issue import format_issue_body
from apk_inspector import ANDROID_API_MAP, compute_privacy_grade, extract_manifest_metadata
from feed_generator import build_atom_feed, build_obtainium_export
from fdroid_repo import generate_fdroid_index, generate_fdroid_portal_html
from notify_webhook import send_discord_webhook, send_telegram_message
from issue_to_pr import parse_issue_form
from format_tables import clean_app_sort_key, format_table_block, process_readme
from contributors_wall import generate_svg
from changelog_summarizer import clean_markdown_changelog, format_changelog_section
from i18n_sync import translate_content


class TestAutomations(unittest.TestCase):

    # 1. VirusTotal
    def test_virustotal_badge_and_summary(self):
        sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        badge_clean = generate_vt_badge(sha, {"malicious": 0, "harmless": 65, "undetected": 5})
        self.assertIn("0%2F70%20Clean", badge_clean)
        self.assertIn(sha, badge_clean)

        badge_warn = generate_vt_badge(sha, {"malicious": 3, "harmless": 60})
        self.assertIn("3%2F63%20Warning", badge_warn)

        summary = generate_vt_summary(sha, {"malicious": 0, "harmless": 70})
        self.assertIn("Safety Inspection", summary)
        self.assertIn("Clean", summary)

    # 2. Archive Detector
    def test_archive_detector_extraction_and_report(self):
        text = "Check out https://github.com/RikkaApps/Shizuku and https://github.com/Kin69/Athena for apps."
        repos = extract_github_repos_from_text(text)
        self.assertIn("RikkaApps/Shizuku", repos)
        self.assertIn("Kin69/Athena", repos)

        report = {
            "scanned_at": "2026-09-29T12:00:00Z",
            "total_scanned": 2,
            "archived_count": 1,
            "stale_count": 0,
            "deleted_count": 0,
            "archived": [{"repo": "test/archived", "stars": 10, "pushed_at": "2021-01-01"}],
            "stale": [],
            "deleted": [],
        }
        md = generate_markdown_report(report)
        self.assertIn("Repository Health", md)
        self.assertIn("test/archived", md)

    # 3. Shizuku API Verifier
    def test_shizuku_signatures(self):
        self.assertTrue(any("shizuku" in sig.lower() for sig in SHIZUKU_SIGNATURES))
        res = verify_apk_file("non_existent.apk")
        self.assertFalse(res["verified"])

    # 4. Link Checker Issue Formatter
    def test_link_checker_issue_formatting(self):
        broken = [{"url": "https://example.com/dead", "line": 42, "error": "HTTP 404 Not Found"}]
        body = format_issue_body(broken)
        self.assertIn("Broken Link & 404 Report", body)
        self.assertIn("https://example.com/dead", body)
        self.assertIn("`L42`", body)

    # 5. Android Target & Min SDK Inspector
    def test_apk_inspector_api_map_and_privacy(self):
        self.assertEqual(ANDROID_API_MAP[26], "Android 8.0 (Oreo)")
        self.assertEqual(ANDROID_API_MAP[34], "Android 14 (Upside Down Cake)")

        grade_a_plus, _ = compute_privacy_grade(0, True)
        self.assertEqual(grade_a_plus, "A+")

        grade_c, _ = compute_privacy_grade(6, False)
        self.assertEqual(grade_c, "C")

    # 8. Obtainium & RSS / Atom Feed Generator
    def test_feed_generator(self):
        apps = [{"slug": "canta", "name": "Canta", "source_repo": "samolego/Canta"}]
        obtainium = build_obtainium_export(apps)
        self.assertEqual(obtainium["formatVersion"], 1)
        self.assertEqual(len(obtainium["apps"]), 1)
        self.assertEqual(obtainium["apps"][0]["id"], "canta")

        atom = build_atom_feed(apps)
        self.assertIn("<title>Best Shizuku Apps for Android - Releases Feed</title>", atom)
        self.assertIn("<title>Canta latest</title>", atom)

    # 9. F-Droid Repository Auto-Builder
    def test_fdroid_repo(self):
        apps = [{"slug": "canta", "name": "Canta", "package_name": "org.samolego.canta", "source_repo": "samolego/Canta"}]
        idx = generate_fdroid_index(apps)
        self.assertIn("repo", idx)
        self.assertEqual(idx["repo"]["name"], "Best Shizuku Apps Mirror")
        self.assertIn("org.samolego.canta", idx["packages"])

        portal = generate_fdroid_portal_html("https://example.com/fdroid/repo")
        self.assertIn("fdroidrepo://example.com/fdroid/repo", portal)

    # 10. Notification Bot
    def test_notifications_dry_run(self):
        # With empty tokens, functions should gracefully return False without raising exceptions
        self.assertFalse(send_telegram_message("", "", "Hello"))
        self.assertFalse(send_discord_webhook("", "Title", "Desc", []))

    # 11. Issue to PR Parser
    def test_issue_to_pr_parser(self):
        sample_issue = (
            "### App name\n\nAthena Firewall\n\n"
            "### Official project or app link\n\nhttps://github.com/Kin69/Athena\n\n"
            "### License\n\nGNU v3\n\n"
            "### Description and Shizuku use case\n\nFirewall without VPN using Shizuku."
        )
        parsed = parse_issue_form(sample_issue)
        self.assertEqual(parsed["name"], "Athena Firewall")
        self.assertEqual(parsed["link"], "https://github.com/Kin69/Athena")
        self.assertEqual(parsed["license"], "GNU v3")
        self.assertIn("Firewall without VPN", parsed["description"])

    # 12. Markdown Table Formatter & Alphabetizer
    def test_format_tables(self):
        raw = (
            "| App | Description | License | Links |\n"
            "|:---|:---|:---|:---|\n"
            "| **[Zeta](https://z.com)** | Z app | MIT | [Link](https://z.com) |\n"
            "| **[Alpha](https://a.com)** | A app | Apache | [Link](https://a.com) |\n"
        )
        formatted = process_readme(raw)
        lines = [line.strip() for line in formatted.strip().splitlines()]
        self.assertIn("Alpha", lines[2])
        self.assertIn("Zeta", lines[3])

    # 13. Contributors Wall
    def test_contributors_wall_svg(self):
        svg = generate_svg([{"login": "krishna3163", "avatar_url": "https://example.com/k.png", "contributions": 10}])
        self.assertIn("<svg", svg)
        self.assertIn("krishna3163", svg)
        self.assertIn("</svg>", svg)

    # 14. Upstream Changelog Summarizer
    def test_changelog_cleaner(self):
        notes = "### Release v1.0.0\r\n\r\n- Fixed crash\r\n- Added dark mode\r\n"
        cleaned = clean_markdown_changelog(notes)
        self.assertNotIn("\r", cleaned)
        section = format_changelog_section("v1.0.0", notes)
        self.assertIn("What's New in v1.0.0", section)
        self.assertIn("<details open>", section)

    # 15. Multilingual README Sync
    def test_i18n_translation(self):
        en_snippet = "# 🚀 Best Shizuku Apps for Android (No Root)\n### What is Shizuku?"
        zh_res = translate_content(en_snippet, "zh-CN")
        self.assertIn("最优质的安卓免 Root Shizuku 应用合集", zh_res)
        self.assertIn("什么是 Shizuku？", zh_res)
        self.assertIn("Language / 语言 / Язык", zh_res)

        ru_res = translate_content(en_snippet, "ru")
        self.assertIn("Лучшие приложения Shizuku", ru_res)
        self.assertIn("Что такое Shizuku?", ru_res)


if __name__ == "__main__":
    unittest.main()
