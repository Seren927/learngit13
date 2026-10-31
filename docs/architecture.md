# 系统架构

## 设计目标

OpenRepoLens 的目标不是替代 GitHub Insights、OpenSSF Scorecard 等成熟项目，而是提供一个规模可控、规则可读、适合课程实践与个人项目自检的轻量实现。系统将“读取仓库事实”和“解释评分结果”分开，便于测试与后续扩展。

## 模块划分

```text
浏览器 / CLI
     │
     ├── server.py ── HTTP API ── scanner.py
     │                              │
     └── cli.py ─── reporting.py ───┤
                                    ├── snapshot.py
                                    ├── remote.py
                                    └── checks.py
```

- `snapshot.py` 构建仓库文件与文本快照，忽略 `.git`、缓存和虚拟环境。
- `remote.py` 使用 GitHub REST API 获取仓库元数据、文件树和关键文档。
- `checks.py` 执行五类检查，返回每项证据、得分与建议。
- `scanner.py` 汇总分类得分、等级、推荐项和统计信息。
- `server.py` 提供静态页面和 `/api/scan` 接口。
- `web/` 使用原生 HTML、CSS、JavaScript 渲染结果，不依赖构建工具。

## 数据流

1. 用户输入本地路径或 GitHub URL。
2. 扫描器建立只读仓库快照。
3. 评分规则在快照上执行，不修改目标仓库。
4. 结果被序列化为统一 JSON 结构。
5. Web 面板或 CLI 渲染结果。

## 安全与隐私

- 本地扫描只读取文本文件，单文件上限为 256 KB。
- 不执行被扫描仓库中的任何代码。
- 不向外部服务上传本地文件内容。
- 远程扫描只访问仓库已公开的 GitHub API 数据。
- 令牌只从环境变量 `GITHUB_TOKEN` 读取，不写入日志或响应。

