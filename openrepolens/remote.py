"""Minimal GitHub REST client used for public remote scans."""

from __future__ import annotations

import base64
import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .snapshot import RepositorySnapshot


IMPORTANT_FILES = (
    "README.md",
    "README.rst",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "pyproject.toml",
    "package.json",
    "docs/community.md",
)


class GitHubAPIError(RuntimeError):
    pass


def parse_repository_url(url: str) -> tuple[str, str]:
    match = re.search(
        r"github\.com[/:]([^/\s]+)/([^/\s#?]+?)(?:\.git)?(?:[/?#].*)?$",
        url.strip(),
    )
    if not match:
        raise ValueError("请输入形如 https://github.com/owner/repo 的公开仓库地址")
    return match.group(1), match.group(2)


class GitHubClient:
    def __init__(self, token: str | None = None, timeout: int = 20) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.timeout = timeout

    def get_json(self, path: str) -> dict[str, Any] | list[Any]:
        url = path if path.startswith("https://") else f"https://api.github.com{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "OpenRepoLens/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise GitHubAPIError("仓库不存在或不是公开仓库") from exc
            if exc.code == 403:
                raise GitHubAPIError("GitHub API 访问受限，请稍后重试或设置 GITHUB_TOKEN") from exc
            raise GitHubAPIError(f"GitHub API 返回错误：HTTP {exc.code}") from exc
        except URLError as exc:
            raise GitHubAPIError(f"无法连接 GitHub：{exc.reason}") from exc


def snapshot_from_github(url: str, token: str | None = None) -> RepositorySnapshot:
    owner, repository = parse_repository_url(url)
    client = GitHubClient(token=token)
    repo = client.get_json(f"/repos/{owner}/{repository}")
    if not isinstance(repo, dict):
        raise GitHubAPIError("GitHub 返回了无法识别的仓库信息")

    branch = repo.get("default_branch") or "main"
    tree = client.get_json(
        f"/repos/{owner}/{repository}/git/trees/{quote(str(branch), safe='')}?recursive=1"
    )
    if not isinstance(tree, dict):
        raise GitHubAPIError("GitHub 返回了无法识别的文件树")

    files = [
        item["path"]
        for item in tree.get("tree", [])
        if isinstance(item, dict) and item.get("type") == "blob" and item.get("path")
    ]
    files_lower = {path.lower(): path for path in files}

    texts: dict[str, str] = {}
    for candidate in IMPORTANT_FILES:
        actual = files_lower.get(candidate.lower())
        if not actual:
            continue
        content = client.get_json(
            f"/repos/{owner}/{repository}/contents/{quote(actual, safe='/')}?ref={quote(str(branch), safe='')}"
        )
        if not isinstance(content, dict) or content.get("encoding") != "base64":
            continue
        try:
            texts[actual] = base64.b64decode(content.get("content", "")).decode(
                "utf-8", errors="replace"
            )
        except (ValueError, TypeError):
            continue

    license_info = repo.get("license") or {}
    metadata = {
        "full_name": repo.get("full_name", f"{owner}/{repository}"),
        "html_url": repo.get("html_url", url),
        "description": repo.get("description") or "",
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "watchers": repo.get("subscribers_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "topics": repo.get("topics", []),
        "license": license_info.get("spdx_id") or "NOASSERTION",
        "default_branch": branch,
        "updated_at": repo.get("updated_at", ""),
    }
    return RepositorySnapshot.from_remote(
        name=repo.get("name", repository),
        source=repo.get("html_url", url),
        files=files,
        texts=texts,
        metadata=metadata,
    )

