# 贡献指南

感谢你愿意参与 OpenRepoLens。我们欢迎缺陷修复、检查规则完善、文档改进和界面优化。为了让协作过程清晰、可审查，请遵循以下流程。

## 开始之前

1. 先搜索现有 Issue，避免重复提交。
2. 小型文档修正可以直接提交 Pull Request；新检查规则或较大功能请先创建 Issue 讨论。
3. 请确保 Issue 和 Pull Request 的描述真实、简洁，并提供可以复现问题的信息。

## 开发环境

```bash
git clone https://github.com/learngit13/OpenRepoLens_13.git
cd OpenRepoLens_13
python -m unittest discover -s tests -v
```

项目使用 Python 标准库，不需要安装运行依赖。若本地安装了 Ruff，可额外执行 `ruff check .`。

## 分支与提交

从 `main` 创建短生命周期分支：

```bash
git switch -c feature/add-html-export
```

建议的分支前缀：

- `feature/`：新增功能或检查规则
- `fix/`：修复缺陷
- `docs/`：只修改文档
- `refactor/`：不改变外部行为的重构

提交信息使用祈使句，并说明变更目的：

```text
feat: add HTML export command
fix: handle missing README on remote repositories
docs: explain conflict resolution workflow
```

## Pull Request 流程

1. 同步 `main` 后创建分支，避免在主干直接开发。
2. 完成变更并补充或更新测试。
3. 在本地运行 `python -m unittest discover -s tests -v`。
4. 推送分支，并在 Pull Request 中填写变更内容、测试方式和关联 Issue。
5. 等待维护者审查；根据讨论提交后续修改。
6. 合并后删除功能分支，保持仓库历史清晰。

## 解决合并冲突

当 `main` 与功能分支修改了同一位置时，可以按以下方式处理：

```bash
git switch feature/your-branch
git fetch origin
git merge origin/main
```

在编辑器中逐个处理冲突标记，保留双方都需要的语义，删除 `<<<<<<<`、`=======`、`>>>>>>>` 标记，并重新运行测试。确认无误后：

```bash
git add <resolved-files>
git commit
git push
```

如果冲突复杂，应在 Pull Request 中说明取舍依据，避免只保留某一方而丢失有效修改。

## 代码与文档规范

- Python 代码使用 4 个空格缩进，目标版本为 Python 3.10。
- 新增检查必须同时更新 `docs/scoring.md` 和对应测试。
- 用户可见文案优先使用简洁、明确的中文；代码标识保持英文。
- 不提交缓存、虚拟环境、令牌、个人路径或其他敏感信息。

## 社区行为

参与本项目即表示同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。请围绕问题本身讨论，尊重不同经验水平的贡献者。

