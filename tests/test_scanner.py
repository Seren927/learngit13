from __future__ import annotations

import unittest

from openrepolens.models import grade_for
from openrepolens.remote import parse_repository_url
from openrepolens.scanner import scan_local


class ScannerTest(unittest.TestCase):
    def test_grade_boundaries(self) -> None:
        self.assertEqual(grade_for(100), "A+")
        self.assertEqual(grade_for(95), "A+")
        self.assertEqual(grade_for(94), "A")
        self.assertEqual(grade_for(80), "B")
        self.assertEqual(grade_for(59), "E")

    def test_parse_repository_url(self) -> None:
        self.assertEqual(
            parse_repository_url("https://github.com/learngit13/OpenRepoLens_13"),
            ("learngit13", "OpenRepoLens_13"),
        )
        self.assertEqual(
            parse_repository_url("https://github.com/openai/openai-python.git"),
            ("openai", "openai-python"),
        )

    def test_invalid_repository_url(self) -> None:
        with self.assertRaises(ValueError):
            parse_repository_url("https://example.com/not-github")

    def test_scan_current_project(self) -> None:
        result = scan_local(".")
        self.assertGreaterEqual(result.score, 90)
        self.assertEqual(len(result.categories), 5)
        self.assertGreaterEqual(len(result.checks), 20)


if __name__ == "__main__":
    unittest.main()

