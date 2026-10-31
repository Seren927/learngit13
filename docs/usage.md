# 使用指南

## 本地扫描

进入任意仓库目录后执行：

```bash
python -m openrepolens scan --path .
```

也可以从其他目录指定绝对路径：

```bash
python -m openrepolens scan --path C:\projects\my-repository
```

扫描过程只读取文件，不会修改目标仓库，也不会执行其中的代码。

## 启动可视化面板

```bash
python -m openrepolens serve --port 8765 --open
```

在页面中选择“本地项目”，输入路径后点击“开始检测”。页面默认自动扫描 OpenRepoLens 自身，可直接观察完整评分结果。

## 远程扫描

选择“GitHub 仓库”，输入公开仓库地址，例如：

```text
https://github.com/Seren927/learngit13
```

远程模式读取仓库元数据、默认分支文件树及关键文档。GitHub 匿名 API 有访问频率限制；如遇 403，可设置 `GITHUB_TOKEN` 后重新启动服务。

## JSON 输出

JSON 结果包含 `repository`、`score`、`categories`、`checks`、`recommendations` 和 `metadata` 字段，可用于构建自己的报告页面或自动化任务。

```bash
python -m openrepolens scan --path . --json > audit.json
```

