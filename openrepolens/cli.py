"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .remote import GitHubAPIError
from .reporting import render_markdown, render_text
from .scanner import scan_local, scan_remote
from .server import serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openrepolens",
        description="检查开源仓库的文档、许可证、协作流程与工程质量。",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="扫描本地目录或公开 GitHub 仓库")
    scan_parser.add_argument("--path", default=".", help="本地仓库目录，默认当前目录")
    scan_parser.add_argument("--url", default="", help="公开 GitHub 仓库地址")
    scan_parser.add_argument("--json", action="store_true", help="输出 JSON")
    scan_parser.add_argument("--markdown", action="store_true", help="输出 Markdown 报告")

    serve_parser = subparsers.add_parser("serve", help="启动本地可视化面板")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", default=8765, type=int)
    serve_parser.add_argument("--open", action="store_true", help="启动后打开浏览器")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "serve":
        serve(host=args.host, port=args.port, open_browser=args.open)
        return 0
    if args.command != "scan":
        parser.print_help()
        return 0

    try:
        result = scan_remote(args.url) if args.url else scan_local(Path(args.path))
    except (ValueError, OSError, GitHubAPIError) as exc:
        parser.error(str(exc))
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif args.markdown:
        print(render_markdown(result))
    else:
        print(render_text(result))
    return 0

