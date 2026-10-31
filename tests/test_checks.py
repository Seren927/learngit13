from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openrepolens.checks import evaluate
from openrepolens.scanner import scan_local
from openrepolens.snapshot import RepositorySnapshot


def write_files(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class ChecksTest(unittest.TestCase):
    def test_healthy_repository_scores_full_marks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "healthy_repo"
            root.mkdir()
            write_files(
                root,
                {
                    "README.md": (
                        "# Demo\n\n"
                        "## 功能\n\n这是一个用于测试的示例。\n\n"
                        "## 快速开始\n\n```bash\npython demo.py\n```\n\n"
                        "![demo](docs/demo.png)\n\n"
                        "## 维护者\n\n提交 Issue 前请阅读 CONTRIBUTING 与 LICENSE。\n"
                    )
                    + ("Detailed documentation line. " * 40),
                    "LICENSE": "MIT License\n\nPermission is hereby granted, free of charge.",
                    "CONTRIBUTING.md": "# Contributing\n\nCreate a branch and open a pull request.",
                    "CODE_OF_CONDUCT.md": "# Code of Conduct",
                    "SECURITY.md": "# Security",
                    "CHANGELOG.md": "# Changelog",
                    "ROADMAP.md": "# Roadmap",
                    "pyproject.toml": "[tool.ruff]\nline-length = 100\n",
                    ".gitignore": "__pycache__/\n",
                    "docs/architecture.md": "# Architecture",
                    "docs/community.md": "# Community",
                    "tests/test_demo.py": "def test_demo():\n    assert True\n",
                    ".github/ISSUE_TEMPLATE/bug.yml": "name: Bug\n",
                    ".github/PULL_REQUEST_TEMPLATE.md": "# Pull request\n",
                    ".github/workflows/tests.yml": "name: Tests\n",
                    "openrepolens/__main__.py": "print('demo')\n",
                },
            )
            snapshot = RepositorySnapshot.from_local(root)
            checks, categories = evaluate(snapshot)

            self.assertEqual(sum(category.points for category in categories), 100)
            self.assertTrue(all(check.status == "pass" for check in checks))

    def test_missing_documents_lower_the_score(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "empty_repo"
            root.mkdir()
            write_files(root, {"main.py": "print('hello')\n"})
            result = scan_local(root)

            self.assertLess(result.score, 30)
            self.assertEqual(len(result.recommendations), 5)
            self.assertTrue(any("LICENSE" in item for item in result.recommendations))

    def test_readme_checks_are_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            write_files(root, {"README.md": "# Demo\n\n## Usage\n\nRun it.\n"})
            result = scan_local(root)
            readme_check = next(
                check for check in result.checks if check.check_id == "readme-present"
            )
            self.assertEqual(readme_check.status, "pass")


if __name__ == "__main__":
    unittest.main()

