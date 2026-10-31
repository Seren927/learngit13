"""Scan orchestration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .checks import evaluate
from .models import ScanResult, grade_for
from .remote import snapshot_from_github
from .snapshot import RepositorySnapshot


def scan_local(path: str | Path = ".") -> ScanResult:
    snapshot = RepositorySnapshot.from_local(Path(path))
    return _build_result(snapshot)


def scan_remote(url: str, token: str | None = None) -> ScanResult:
    snapshot = snapshot_from_github(url, token=token)
    return _build_result(snapshot)


def _build_result(snapshot: RepositorySnapshot) -> ScanResult:
    checks, categories = evaluate(snapshot)
    score = sum(category.points for category in categories)
    grade = grade_for(score)
    recommendations = [
        check.suggestion
        for check in sorted(checks, key=lambda item: item.points / item.max_points)
        if check.status != "pass" and check.suggestion
    ]
    if not recommendations:
        recommendations = [
            "保持当前文档与协作规范，发布新版本时同步更新 CHANGELOG。",
            "定期检查依赖和漏洞报告，持续维护 Issue 与 Pull Request。",
        ]

    metadata: dict[str, Any] = dict(snapshot.metadata)
    metadata.setdefault("name", snapshot.name)
    metadata.setdefault("html_url", snapshot.source if snapshot.source.startswith("http") else "")

    return ScanResult(
        repository=snapshot.name,
        source=snapshot.source,
        score=score,
        grade=grade,
        summary=_summary_for(score),
        categories=categories,
        checks=checks,
        recommendations=recommendations[:5],
        stats={
            "files": len(snapshot.files),
            "text_files": len(snapshot.texts),
            "mode": "GitHub 远程扫描" if snapshot.metadata else "本地目录扫描",
        },
        metadata=metadata,
        generated_at=datetime.now().astimezone().isoformat(timespec="seconds"),
    )


def _summary_for(score: int) -> str:
    if score >= 95:
        return "仓库治理结构完整，开源协作与文档基础设施处于优秀水平。"
    if score >= 90:
        return "仓库整体健康，关键文档与协作入口齐全，仍有少量细节可以继续完善。"
    if score >= 80:
        return "仓库具备基本开源条件，建议优先补齐协作规范和自动化检查。"
    if score >= 60:
        return "仓库可被他人理解，但文档、测试或协作流程存在明显缺口。"
    return "仓库尚未形成稳定的开源协作基础，建议从 README 和许可证开始补齐。"

