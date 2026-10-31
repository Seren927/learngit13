"""Terminal and Markdown renderers."""

from __future__ import annotations

from .models import ScanResult


STATUS_MARK = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}


def render_text(result: ScanResult) -> str:
    lines = [
        f"OpenRepoLens  |  {result.repository}",
        f"健康度：{result.score}/100  等级：{result.grade}",
        result.summary,
        "",
        "分类得分",
    ]
    for category in result.categories:
        lines.append(
            f"  {category.label:<8} {category.points:>2}/{category.max_points:<2}  {category.percent:>3}%"
        )
    lines.extend(["", "检查明细"])
    for check in result.checks:
        lines.append(
            f"  [{STATUS_MARK[check.status]}] {check.title:<10} {check.points}/{check.max_points}  {check.evidence}"
        )
    if result.recommendations:
        lines.extend(["", "改进建议"])
        lines.extend(f"  {index}. {item}" for index, item in enumerate(result.recommendations, 1))
    return "\n".join(lines)


def render_markdown(result: ScanResult) -> str:
    lines = [
        f"# {result.repository} 健康度报告",
        "",
        f"**综合得分：{result.score}/100（{result.grade}）**",
        "",
        result.summary,
        "",
        "## 分类得分",
        "",
        "| 分类 | 得分 | 完成度 |",
        "| --- | ---: | ---: |",
    ]
    for category in result.categories:
        lines.append(
            f"| {category.label} | {category.points}/{category.max_points} | {category.percent}% |"
        )
    lines.extend(["", "## 检查明细", "", "| 状态 | 检查项 | 得分 | 证据 |", "| --- | --- | ---: | --- |"])
    for check in result.checks:
        lines.append(
            f"| {STATUS_MARK[check.status]} | {check.title} | {check.points}/{check.max_points} | {check.evidence} |"
        )
    if result.recommendations:
        lines.extend(["", "## 改进建议", ""])
        lines.extend(f"- {item}" for item in result.recommendations)
    return "\n".join(lines)

