"""Scoring rules for repository health checks."""

from __future__ import annotations

import re
from collections import OrderedDict

from .models import CategoryScore, Check
from .snapshot import RepositorySnapshot


CATEGORY_LABELS = OrderedDict(
    [
        ("license", "许可证"),
        ("readme", "README"),
        ("documentation", "项目文档"),
        ("collaboration", "开放协作"),
        ("quality", "工程质量"),
    ]
)


def evaluate(snapshot: RepositorySnapshot) -> tuple[list[Check], list[CategoryScore]]:
    checks: list[Check] = []
    checks.extend(_license_checks(snapshot))
    checks.extend(_readme_checks(snapshot))
    checks.extend(_documentation_checks(snapshot))
    checks.extend(_collaboration_checks(snapshot))
    checks.extend(_quality_checks(snapshot))

    categories: list[CategoryScore] = []
    for key, label in CATEGORY_LABELS.items():
        subset = [check for check in checks if check.category == key]
        categories.append(
            CategoryScore(
                key=key,
                label=label,
                points=sum(check.points for check in subset),
                max_points=sum(check.max_points for check in subset),
            )
        )
    return checks, categories


def _check(
    *,
    check_id: str,
    category: str,
    title: str,
    description: str,
    points: int,
    max_points: int,
    evidence: str,
    suggestion: str = "",
) -> Check:
    ratio = points / max_points if max_points else 0
    if points == max_points:
        status = "pass"
    elif ratio >= 0.6:
        status = "warn"
    else:
        status = "fail"
    return Check(
        check_id=check_id,
        category=category,
        title=title,
        description=description,
        status=status,
        points=points,
        max_points=max_points,
        evidence=evidence,
        suggestion=suggestion,
    )


def _license_checks(snapshot: RepositorySnapshot) -> list[Check]:
    license_path = snapshot.find(
        ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md"]
    )
    license_text = snapshot.read_path(license_path) if license_path else ""
    recognized = ""
    patterns = {
        "MIT": r"\bMIT License\b|Permission is hereby granted, free of charge",
        "Apache-2.0": r"Apache License\s*,?\s*Version 2\.0",
        "GPL-3.0": r"GNU GENERAL PUBLIC LICENSE\s+Version 3",
        "BSD-3-Clause": r"BSD 3-Clause",
        "MPL-2.0": r"Mozilla Public License Version 2\.0",
    }
    for name, pattern in patterns.items():
        if re.search(pattern, license_text, flags=re.IGNORECASE):
            recognized = name
            break

    return [
        _check(
            check_id="license-file",
            category="license",
            title="许可证文件",
            description="仓库根目录存在许可证原文",
            points=10 if license_path else 0,
            max_points=10,
            evidence=f"检测到 {license_path}" if license_path else "未检测到 LICENSE 或 COPYING 文件",
            suggestion="在根目录添加 LICENSE，写明适用许可证及版权年份。",
        ),
        _check(
            check_id="license-spdx",
            category="license",
            title="许可证可识别",
            description="许可证正文可被识别为常见 SPDX 许可证",
            points=5 if recognized else 0,
            max_points=5,
            evidence=f"识别为 {recognized}" if recognized else "未能识别许可证类型",
            suggestion="使用标准许可证全文，并在 README 中注明 SPDX 标识。",
        ),
    ]


def _readme_checks(snapshot: RepositorySnapshot) -> list[Check]:
    readme_path = snapshot.find_by_basename(["README.md", "README.rst", "README"])
    readme = snapshot.read_path(readme_path) if readme_path else ""
    lower = readme.lower()
    has_quickstart = bool(
        re.search(r"快速开始|安装|使用方法|usage|install|getting started", readme, re.IGNORECASE)
    )
    has_features = bool(
        re.search(r"功能|特性|features|what it does|capabilities", readme, re.IGNORECASE)
    )
    has_visual = "![" in readme or "<img" in lower or "shields.io" in lower
    has_community = bool(
        re.search(r"contributing|贡献|license|许可证|code of conduct|行为准则", readme, re.IGNORECASE)
    )
    has_contact = bool(
        re.search(r"github.com/|issues|discussions|联系|maintainer|维护者", readme, re.IGNORECASE)
    )

    return [
        _check(
            check_id="readme-present",
            category="readme",
            title="README 存在",
            description="仓库提供默认展示文档",
            points=5 if readme_path else 0,
            max_points=5,
            evidence=f"检测到 {readme_path}" if readme_path else "未检测到 README",
            suggestion="添加 README.md，说明项目定位、安装方式和示例。",
        ),
        _check(
            check_id="readme-depth",
            category="readme",
            title="内容完整度",
            description="README 至少包含 800 个字符的有效说明",
            points=5 if len(readme) >= 800 else 0,
            max_points=5,
            evidence=f"当前约 {len(readme)} 个字符",
            suggestion="补充项目背景、适用场景、目录结构和常见问题。",
        ),
        _check(
            check_id="readme-quickstart",
            category="readme",
            title="安装与使用",
            description="包含可执行的安装、启动或使用步骤",
            points=4 if has_quickstart else 0,
            max_points=4,
            evidence="已找到安装或使用章节" if has_quickstart else "缺少安装或使用说明",
            suggestion="增加“快速开始”章节，给出完整命令和示例输入。",
        ),
        _check(
            check_id="readme-features",
            category="readme",
            title="功能说明",
            description="清晰说明项目能解决的问题与主要能力",
            points=3 if has_features else 0,
            max_points=3,
            evidence="已找到功能章节" if has_features else "未找到功能说明",
            suggestion="用简短列表说明核心能力及适用边界。",
        ),
        _check(
            check_id="readme-visual",
            category="readme",
            title="可视化材料",
            description="包含截图、演示图或状态徽章",
            points=3 if has_visual else 0,
            max_points=3,
            evidence="已找到图片或徽章" if has_visual else "未找到图片或徽章",
            suggestion="加入产品截图、状态徽章或简短演示动图。",
        ),
        _check(
            check_id="readme-community",
            category="readme",
            title="社区入口",
            description="README 链接贡献指南、许可证或行为准则",
            points=3 if has_community else 0,
            max_points=3,
            evidence="已找到社区或许可证链接" if has_community else "缺少社区入口",
            suggestion="在 README 中链接 CONTRIBUTING、LICENSE 和 CODE_OF_CONDUCT。",
        ),
        _check(
            check_id="readme-contact",
            category="readme",
            title="反馈渠道",
            description="提供 Issue、Discussions 或维护者联系方式",
            points=2 if has_contact else 0,
            max_points=2,
            evidence="已找到反馈渠道" if has_contact else "未找到明确反馈渠道",
            suggestion="增加问题反馈入口和维护者联系说明。",
        ),
    ]


def _documentation_checks(snapshot: RepositorySnapshot) -> list[Check]:
    contributing = snapshot.find_by_basename(["CONTRIBUTING.md", "CONTRIBUTING"])
    conduct = snapshot.find_by_basename(["CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT"])
    security = snapshot.find_by_basename(["SECURITY.md", "SECURITY"])
    changelog = snapshot.find_by_basename(["CHANGELOG.md", "CHANGELOG"])
    docs_count = snapshot.count_dir("docs", ".md")

    return [
        _check(
            check_id="docs-contributing",
            category="documentation",
            title="贡献指南",
            description="说明如何提交 Issue、分支和 Pull Request",
            points=5 if contributing else 0,
            max_points=5,
            evidence=f"检测到 {contributing}" if contributing else "未检测到贡献指南",
            suggestion="补充 CONTRIBUTING.md，明确开发环境和提交规范。",
        ),
        _check(
            check_id="docs-conduct",
            category="documentation",
            title="行为准则",
            description="建立社区交流与协作边界",
            points=4 if conduct else 0,
            max_points=4,
            evidence=f"检测到 {conduct}" if conduct else "未检测到行为准则",
            suggestion="采用 Contributor Covenant 并写明违规处理方式。",
        ),
        _check(
            check_id="docs-security",
            category="documentation",
            title="安全策略",
            description="提供漏洞报告方式和安全支持范围",
            points=4 if security else 0,
            max_points=4,
            evidence=f"检测到 {security}" if security else "未检测到安全策略",
            suggestion="添加 SECURITY.md，说明私下报告漏洞的流程。",
        ),
        _check(
            check_id="docs-directory",
            category="documentation",
            title="文档目录",
            description="docs/ 至少包含两篇 Markdown 文档",
            points=4 if docs_count >= 2 else 0,
            max_points=4,
            evidence=f"docs/ 中有 {docs_count} 篇 Markdown 文档",
            suggestion="补充架构、评分规则或使用指南等长期文档。",
        ),
        _check(
            check_id="docs-changelog",
            category="documentation",
            title="版本记录",
            description="记录已发布版本与重要变更",
            points=3 if changelog else 0,
            max_points=3,
            evidence=f"检测到 {changelog}" if changelog else "未检测到 CHANGELOG",
            suggestion="添加 CHANGELOG.md，使用清晰的版本号和日期。",
        ),
    ]


def _collaboration_checks(snapshot: RepositorySnapshot) -> list[Check]:
    issue_templates = [
        path
        for path in snapshot.files
        if path.lower().startswith(".github/issue_template/")
    ]
    pr_template = snapshot.any_path(".github/PULL_REQUEST_TEMPLATE.md") or snapshot.any_path(
        "PULL_REQUEST_TEMPLATE.md"
    )
    roadmap = snapshot.find_by_basename(["ROADMAP.md", "ROADMAP"])
    community_doc = snapshot.find(
        ["docs/community.md", "docs/COMMUNITY.md", "COMMUNITY.md"]
    )
    readme = snapshot.read_first(["README.md", "README.rst", "README"])

    return [
        _check(
            check_id="collab-issues",
            category="collaboration",
            title="Issue 模板",
            description="为缺陷和功能建议提供结构化反馈入口",
            points=6 if issue_templates else 0,
            max_points=6,
            evidence=f"检测到 {len(issue_templates)} 个 Issue 模板" if issue_templates else "未检测到 Issue 模板",
            suggestion="在 .github/ISSUE_TEMPLATE/ 中添加 bug 和 feature 模板。",
        ),
        _check(
            check_id="collab-pr",
            category="collaboration",
            title="Pull Request 模板",
            description="统一变更说明、测试与审查清单",
            points=5 if pr_template else 0,
            max_points=5,
            evidence="检测到 Pull Request 模板" if pr_template else "未检测到 Pull Request 模板",
            suggestion="添加 PR 模板，要求说明变更、测试和关联 Issue。",
        ),
        _check(
            check_id="collab-roadmap",
            category="collaboration",
            title="公开路线图",
            description="公开下一阶段目标与优先级",
            points=3 if roadmap else 0,
            max_points=3,
            evidence=f"检测到 {roadmap}" if roadmap else "未检测到 ROADMAP",
            suggestion="公开短期路线图，便于贡献者选择合适的任务。",
        ),
        _check(
            check_id="collab-community",
            category="collaboration",
            title="社区说明",
            description="说明讨论、角色和协作方式",
            points=3 if community_doc else 0,
            max_points=3,
            evidence=f"检测到 {community_doc}" if community_doc else "未检测到社区说明",
            suggestion="补充社区文档，说明讨论渠道、审查与发布节奏。",
        ),
        _check(
            check_id="collab-maintainers",
            category="collaboration",
            title="维护者信息",
            description="README 中说明维护者或贡献方式",
            points=3
            if re.search(r"maintainer|维护者|contributor|贡献者|贡献指南", readme, re.IGNORECASE)
            else 0,
            max_points=3,
            evidence="README 已包含维护或贡献信息",
            suggestion="在 README 尾部增加维护者和贡献方式。",
        ),
    ]


def _quality_checks(snapshot: RepositorySnapshot) -> list[Check]:
    tests = snapshot.has_dir("tests") and any(
        path.lower().startswith("tests/test") for path in snapshot.files
    )
    ci = snapshot.any_path(".github/workflows/*.yml") or snapshot.any_path(
        ".github/workflows/*.yaml"
    )
    pyproject = snapshot.has("pyproject.toml")
    gitignore = snapshot.has(".gitignore")
    lint_config = any(
        snapshot.has(path)
        for path in ("ruff.toml", "pyrightconfig.json", "mypy.ini", ".eslintrc", "eslint.config.js")
    ) or "[tool.ruff]" in snapshot.read_path("pyproject.toml")
    source = snapshot.has("openrepolens/__main__.py") or snapshot.has("src/__main__.py")

    return [
        _check(
            check_id="quality-tests",
            category="quality",
            title="自动化测试",
            description="tests/ 中存在可执行测试",
            points=5 if tests else 0,
            max_points=5,
            evidence="检测到测试目录与测试文件" if tests else "未检测到自动化测试",
            suggestion="为评分规则和扫描器增加单元测试。",
        ),
        _check(
            check_id="quality-ci",
            category="quality",
            title="持续集成",
            description="通过 GitHub Actions 自动验证变更",
            points=5 if ci else 0,
            max_points=5,
            evidence="检测到 GitHub Actions 工作流" if ci else "未检测到 CI 工作流",
            suggestion="添加测试工作流，在 push 和 pull_request 时执行。",
        ),
        _check(
            check_id="quality-packaging",
            category="quality",
            title="项目元数据",
            description="提供标准化的构建与依赖声明",
            points=3 if pyproject else 0,
            max_points=3,
            evidence="检测到 pyproject.toml" if pyproject else "未检测到 pyproject.toml",
            suggestion="添加 pyproject.toml，声明版本、入口和 Python 版本要求。",
        ),
        _check(
            check_id="quality-gitignore",
            category="quality",
            title="忽略规则",
            description="避免提交缓存、密钥与本地环境文件",
            points=3 if gitignore else 0,
            max_points=3,
            evidence="检测到 .gitignore" if gitignore else "未检测到 .gitignore",
            suggestion="添加 .gitignore，覆盖虚拟环境、缓存和本地配置。",
        ),
        _check(
            check_id="quality-lint",
            category="quality",
            title="代码质量配置",
            description="配置静态检查或类型检查工具",
            points=2 if lint_config else 0,
            max_points=2,
            evidence="检测到代码质量配置" if lint_config else "未检测到代码质量配置",
            suggestion="增加 Ruff 或类型检查配置，并在 CI 中执行。",
        ),
        _check(
            check_id="quality-source",
            category="quality",
            title="可执行入口",
            description="项目包含明确的命令行或服务入口",
            points=2 if source else 0,
            max_points=2,
            evidence="检测到 openrepolens/__main__.py" if source else "未检测到可执行入口",
            suggestion="提供 __main__.py 或 console script 入口。",
        ),
    ]

