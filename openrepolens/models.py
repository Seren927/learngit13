"""Data models used by the scanner and the web API."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Check:
    check_id: str
    category: str
    title: str
    description: str
    status: str
    points: int
    max_points: int
    evidence: str
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CategoryScore:
    key: str
    label: str
    points: int
    max_points: int

    @property
    def percent(self) -> int:
        if self.max_points == 0:
            return 0
        return round(self.points / self.max_points * 100)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["percent"] = self.percent
        return data


@dataclass
class ScanResult:
    repository: str
    source: str
    score: int
    grade: str
    summary: str
    categories: list[CategoryScore] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = ""

    @property
    def passed(self) -> int:
        return sum(check.status == "pass" for check in self.checks)

    @property
    def warnings(self) -> int:
        return sum(check.status == "warn" for check in self.checks)

    @property
    def failed(self) -> int:
        return sum(check.status == "fail" for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["categories"] = [category.to_dict() for category in self.categories]
        data["stats"].update(
            {
                "passed": self.passed,
                "warnings": self.warnings,
                "failed": self.failed,
                "total_checks": len(self.checks),
            }
        )
        return data


def grade_for(score: int) -> str:
    if score >= 95:
        return "A+"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "E"

