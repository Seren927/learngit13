"""Build a small, read-only view of a repository for the checks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable


IGNORED_DIRS = {
    ".git",
    ".idea",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}

TEXT_SUFFIXES = {
    ".c", ".cc", ".cfg", ".cpp", ".css", ".go", ".h", ".html", ".ini",
    ".java", ".js", ".json", ".jsx", ".md", ".mjs", ".py", ".rst", ".sh",
    ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml",
}

TEXT_BASENAMES = {
    "changelog", "code_of_conduct", "contributing", "license", "readme", "security",
}

MAX_TEXT_BYTES = 256_000


class RepositorySnapshot:
    """Repository paths and selected text files with case-insensitive lookup."""

    def __init__(
        self,
        name: str,
        source: str,
        files: Iterable[str],
        texts: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.source = source
        self.files = tuple(sorted(str(item).replace("\\", "/") for item in files))
        self.texts = {
            str(path).replace("\\", "/"): text
            for path, text in (texts or {}).items()
        }
        self.metadata = metadata or {}
        self._files_lower = {path.lower(): path for path in self.files}
        self._texts_lower = {path.lower(): text for path, text in self.texts.items()}

    @classmethod
    def from_local(cls, root: Path) -> "RepositorySnapshot":
        root = root.expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"目录不存在：{root}")

        files: list[str] = []
        for current_root, dirs, names in os.walk(root):
            dirs[:] = sorted(name for name in dirs if name not in IGNORED_DIRS)
            current = Path(current_root)
            for name in sorted(names):
                path = current / name
                if path.is_symlink():
                    continue
                files.append(path.relative_to(root).as_posix())

        texts: dict[str, str] = {}
        for relative_path in files:
            path = root / relative_path
            if not _looks_textual(relative_path):
                continue
            try:
                if path.stat().st_size > MAX_TEXT_BYTES:
                    continue
                texts[relative_path] = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

        return cls(root.name, str(root), files, texts)

    @classmethod
    def from_remote(
        cls,
        name: str,
        source: str,
        files: Iterable[str],
        texts: dict[str, str],
        metadata: dict[str, Any],
    ) -> "RepositorySnapshot":
        return cls(name, source, files, texts, metadata)

    def has(self, path: str) -> bool:
        return path.lower() in self._files_lower

    def find(self, candidates: Iterable[str]) -> str | None:
        for candidate in candidates:
            match = self._files_lower.get(candidate.lower())
            if match:
                return match
        return None

    def find_by_basename(self, basenames: Iterable[str]) -> str | None:
        wanted = {name.lower() for name in basenames}
        for path in self.files:
            if path.rsplit("/", 1)[-1].lower() in wanted:
                return path
        return None

    def read_any(self, candidates: Iterable[str]) -> str:
        for candidate in candidates:
            match = self._texts_lower.get(candidate.lower())
            if match is not None:
                return match
        return ""

    def read_path(self, path: str) -> str:
        return self._texts_lower.get(path.lower(), "")

    def read_first(self, basenames: Iterable[str]) -> str:
        path = self.find_by_basename(basenames)
        return self.read_path(path) if path else ""

    def has_dir(self, directory: str) -> bool:
        prefix = directory.rstrip("/").lower() + "/"
        return any(path.lower().startswith(prefix) for path in self.files)

    def count_dir(self, directory: str, suffix: str = "") -> int:
        prefix = directory.rstrip("/").lower() + "/"
        return sum(
            path.lower().startswith(prefix)
            and (not suffix or path.lower().endswith(suffix.lower()))
            for path in self.files
        )

    def any_path(self, pattern: str) -> bool:
        from fnmatch import fnmatchcase

        needle = pattern.lower()
        return any(fnmatchcase(path.lower(), needle) for path in self.files)


def _looks_textual(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    suffix = Path(name).suffix.lower()
    stem = Path(name).stem.lower()
    return suffix in TEXT_SUFFIXES or stem in TEXT_BASENAMES or not suffix

