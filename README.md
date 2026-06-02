# LaTeX Pandoc 论文手稿模板

这是一个面向论文初稿写作的极简 LaTeX 模板。它保留标题、作者、摘要、关键词、章节、图表、公式、交叉引用和参考文献等常用论文结构，同时尽量减少复杂期刊排版命令，方便后续用 Pandoc 转成 Word 审阅稿。

## 适合做什么

- 用 `temp.tex` 写论文初稿。
- 用 XeLaTeX 编译 PDF，检查公式、图片和参考文献。
- 用 Pandoc 转换为 Word，便于导师、合作者或审稿前内部修改。
- 在定稿阶段再迁移到目标期刊模板。

## 环境准备

需要安装以下工具：

- TeX Live，并确保 `xelatex` 和 `bibtex` 可用。
- Pandoc。
- PowerShell。
- uv，用来运行 Python 图片预处理脚本。

首次使用时，在仓库根目录运行：

```powershell
uv sync
```

## 文件说明

- `temp.tex`：论文主文件，正文、摘要、关键词、图表和公式都从这里改。
- `temp-ref.bib`：BibTeX 参考文献数据库。
- `temp-ref.bst`：LaTeX 编译 PDF 时使用的参考文献样式。
- `temp-ref.csl`：Pandoc 转 Word 时使用的参考文献样式。
- `fig/`：正文图片目录。
- `scripts/tex-to-docx.ps1`：将 LaTeX 手稿转换为 Word 的主脚本。
- `filters/latex-crossref-cn.lua`：Pandoc Lua filter，用于处理中文图表题、公式编号、交叉引用和 Word 段落样式。
- `.pandoc-cache/`：转换 Word 时生成的临时文件目录，会被 Git 忽略。

## 编译 PDF

在仓库根目录运行：

```powershell
xelatex -interaction=nonstopmode temp.tex
bibtex temp
xelatex -interaction=nonstopmode temp.tex
xelatex -interaction=nonstopmode temp.tex
```

生成结果为 `temp.pdf`。如果没有新增或修改参考文献，通常只运行一次或两次 `xelatex` 也可以。

## 转换为 Word

在仓库根目录运行：

```powershell
.\scripts\tex-to-docx.ps1 -InputFile temp.tex -OutputFile temp-crossref.docx -Bibliography temp-ref.bib -Csl temp-ref.csl
```

脚本会自动完成这些步骤：

- 将 LaTeX 中引用的 PDF 图片转换为 Pandoc 更容易写入 Word 的 PNG 图片。
- 调用 Pandoc 和 Lua filter 生成 DOCX。
- 为 Word 表格补充三线表边框和表格段落样式。

如果需要使用自定义 Word 样式模板，可以加上 `-ReferenceDoc`：

```powershell
.\scripts\tex-to-docx.ps1 -InputFile temp.tex -OutputFile temp-crossref.docx -Bibliography temp-ref.bib -Csl temp-ref.csl -ReferenceDoc reference.docx
```

## 写作建议

- 标题、作者、摘要和关键词保留在正文开头。
- 正文章节使用 `\section`、`\subsection`、`\subsubsection`。
- 图片使用标准 `figure` 环境，并保留一个 `\caption` 和一个 `\label`。
- 表格优先使用 `booktabs` 的 `\toprule`、`\midrule`、`\bottomrule`。
- 公式使用标准 `equation` 环境，并用 `\label` 标记。
- 引用参考文献使用普通 `\cite{...}`。

建议避免在初稿阶段加入复杂期刊模板命令，例如自定义双栏、页眉页脚、复杂标题页、双语图题计数器回退等。这些内容可以在最终投递前再迁移到期刊模板中处理。

## 图片说明

LaTeX 编译 PDF 时可以直接使用 PDF 矢量图。转 Word 时，`scripts/prepare-pandoc-images.py` 会自动把被 `\includegraphics` 引用的 PDF 图片渲染为 PNG，并写入 `.pandoc-cache/images/`。

普通 PNG、JPG 等位图可以直接放入 `fig/` 后引用。

## Git 提示

生成文件会被 `.gitignore` 忽略，包括：

- `*.pdf`
- `*.docx`
- LaTeX 辅助文件
- `.pandoc-cache/`
- `.venv/`

通常只需要提交源文件、脚本、过滤器、参考文献文件和 `fig/` 中需要保留的图片资源。
