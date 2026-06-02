# AGENTS.md

## 项目目标

本仓库以现有期刊 LaTeX 模板为基础，逐步简化为适合论文初稿写作、Pandoc 转 Word 审阅、以及后续按期刊格式整理的模板。

核心目标是保持一套轻量、稳定、可维护的中间模板：

- LaTeX 侧适合写作、公式、图表、交叉引用和 BibTeX 参考文献管理。
- Word 侧适合导师、合作者或审稿前内部修改。
- 初稿阶段避免复杂期刊排版命令，最终投稿前再迁移到目标期刊模板。

## 工作原则

- 优先阅读现有文档和脚本，再决定改动。README 面向第一次使用者，`doc/technical-stack.md` 面向维护者。
- 保持 README 简洁，不把实现细节、完整文件清单或脚本内部逻辑堆到 README。
- 技术细节、文件职责、转换链路、排错说明优先放入 `doc/technical-stack.md`。
- 改动应尽量小而集中。不要顺手重构无关脚本、改写示例论文内容或替换样式模板。
- 遇到已有未提交改动时，默认认为是用户改的；不要回退、覆盖或清理与当前任务无关的文件。
- 生成文件和缓存文件通常不需要提交，也不要为了“清理工作区”删除它们，除非用户明确要求。
- 项目中已有 `refference/` 目录拼写，文档和脚本应沿用当前仓库实际路径，不要擅自改名为 `reference/`。

## 常用入口

- 写作主文件：`temp.tex`
- 参考文献数据库：`reference.bib`
- 图片目录：`fig/`
- Word 转换快捷入口：`.\convert-docx.ps1`
- Word 转换主脚本：`.\scripts\tex-to-docx.ps1`
- Pandoc Lua filter：`filters/latex-crossref-cn.lua`
- 技术文档：`doc/technical-stack.md`
- VS Code 编译配方：`.vscode/settings.json`

## 文件约定

日常写作通常只改：

- `temp.tex`
- `reference.bib`
- `fig/` 中需要保留的论文图片

维护转换流程时才改：

- `scripts/`
- `filters/`
- `reference.docx`
- `gbt7714.bst`
- `gbt7714.csl`
- `.vscode/settings.json`

以下内容是生成物或本地环境，通常不要手动维护，也不要提交：

- `*.pdf`
- `*.docx`，但 `reference.docx` 是样式模板，应保留
- LaTeX 辅助文件，例如 `*.aux`、`*.bbl`、`*.blg`、`*.log`、`*.synctex.gz`
- `.pandoc-cache/`
- `.venv/`
- `__pycache__/`

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

修改文档或脚本后，至少运行：

```powershell
git diff --check
```

修改 Lua filter 后，建议用 Pandoc 做一次只读输出验证：

```powershell
pandoc temp.tex --lua-filter=filters\latex-crossref-cn.lua -t native -o C:\tmp\latex-pandoc-filter-check.native
```

修改 Word 转换脚本、图片预处理、样式规范化或表格后处理后，建议运行 `.\convert-docx.ps1` 生成 `temp.docx` 做人工检查。生成的 `temp.docx` 是输出文件，通常不提交。

## README 与技术文档分工

README 应回答：

- 这个模板适合做什么。
- 第一次使用需要准备什么环境。
- 新手主要改哪些文件。
- 新手暂时不用动哪些文件。
- 如何编译 PDF 和转换 Word。
- 去哪里看技术细节。

`doc/technical-stack.md` 应回答：

- 每个文件和目录的职责。
- LaTeX、Pandoc、PowerShell、Python、Word Open XML 的分工。
- PDF 编译和 Word 转换的数据流。
- Lua filter、DOCX 后处理和样式规范化的实现细节。
- 常见故障如何排查。

## Git 约定

- commit message 使用中文，并遵循约定式提交格式：

  ```text
  <type>(<scope>): <subject>

  [可选 body]

  [可选 footer]
  ```

- 常用 type 示例：`docs`、`fix`、`feat`、`refactor`、`test`、`chore`。
- 文档改动优先使用 `docs(...)`。
- 除非是非常简单的单点改动，否则 commit message 应在 subject 后补充 body，用子条目说明主要改动内容。
- 不要把无关生成文件、缓存或用户未要求的工作区改动一起提交。
