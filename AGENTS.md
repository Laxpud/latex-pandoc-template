# AGENTS.md

## 项目目标

本仓库维护一个适合论文初稿写作的轻量 LaTeX 模板，并提供稳定的 Pandoc 转 Word 审阅稿流程。项目不是完整期刊投稿模板；最终投稿格式应在定稿阶段迁移到目标期刊模板。

核心目标：

- LaTeX 侧保留论文语义、公式、图表、交叉引用和 BibTeX 参考文献管理。
- Word 侧便于导师、合作者或内部审阅修改。
- 初稿阶段避免复杂期刊排版命令，减少 Pandoc 转换不稳定因素。

## 文档所有权

- 根目录 `README.md` 是英文公共入口，保持简洁，不放长实现细节。
- `docs/README.cn.md` 是根 README 的中文翻译，结构应与英文入口同步。
- `TODO.md` 记录当前活动工作，非简单任务应写明验收标准。
- `docs/index.md` 是技术文档索引。
- `docs/technical-stack.md` 保存文件职责、转换链路、脚本实现、Word 样式系统和排错说明。
- `docs/archive/` 保存已完成或历史性的计划草稿。

## 常用入口

- 写作主文件：`temp.tex`
- 参考文献数据库：`reference.bib`
- 图片目录：`fig/`
- Word 转换快捷入口：`.\convert-docx.ps1`
- Linux Word 转换快捷入口：`./convert-docx.sh`
- Word 转换包入口：`src/lpt_docx/cli.py`
- 旧 Word 转换脚本兼容入口：`scripts/tex-to-docx.py`
- Pandoc Lua filter：`filters/latex-crossref-cn.lua`
- 英文 README：`README.md`
- 中文 README：`docs/README.cn.md`
- 技术文档索引：`docs/index.md`
- 技术文档：`docs/technical-stack.md`
- VS Code 编译配方：`.vscode/settings.json`

## 文件边界

日常写作通常只改：

- `temp.tex`
- `reference.bib`
- `fig/` 中需要保留的论文图片

维护转换流程时才改：

- `src/lpt_docx/`
- `scripts/`
- `filters/`
- `reference.docx`
- `gbt7714.bst`
- `gbt7714.csl`
- `.vscode/settings.json`
- `docs/technical-stack.md`

以下内容是生成物或本地环境，通常不要提交：

- `*.pdf`
- `*.docx`，但 `reference.docx` 是样式模板，应保留
- LaTeX 辅助文件，例如 `*.aux`、`*.bbl`、`*.blg`、`*.log`、`*.synctex.gz`
- `.pandoc-cache/`
- `.venv/`
- `__pycache__/`

项目中已有 `refference/` 目录拼写；文档和脚本应沿用当前仓库实际路径，不要擅自改名为 `reference/`。

## 转换与验证

首次准备 Python 依赖：

```powershell
uv sync
```

完整 PDF 编译流程：

```powershell
xelatex -interaction=nonstopmode temp.tex
bibtex temp
xelatex -interaction=nonstopmode temp.tex
xelatex -interaction=nonstopmode temp.tex
```

推荐 Word 转换流程：

```powershell
.\convert-docx.ps1
```

Linux 下运行：

```bash
./convert-docx.sh
```

修改文档后至少运行：

```powershell
git diff --check
```

修改 Lua filter 后，建议用 Pandoc 做一次只读输出验证：

```powershell
pandoc temp.tex --lua-filter=filters\latex-crossref-cn.lua -t native -o C:\tmp\latex-pandoc-filter-check.native
```

修改 Word 转换脚本、图片预处理、兼容预处理、样式规范化或表格后处理后，建议运行当前平台的 `convert-docx.ps1` 或 `convert-docx.sh` 生成 `temp.docx` 做人工检查。生成的 `temp.docx` 是输出文件，通常不提交。

## Git 约定

- commit message 使用中文，并遵循 Conventional Commits：`<type>(<scope>): <subject>`。
- 常用 type：`docs`、`fix`、`feat`、`refactor`、`test`、`chore`。
- 文档改动优先使用 `docs(...)`。
- 非简单改动的 commit body 用独立换行 bullet 概括主要变化，注意使用与提交环境所匹配的换行符。
- 不要把无关生成文件、缓存或用户未要求的工作区改动一起提交。
