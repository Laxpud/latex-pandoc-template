# LaTeX Pandoc 论文手稿模板

这是一个面向论文初稿写作的极简 LaTeX 模板。它保留标题、作者、摘要、关键词、章节、图表、公式、交叉引用和参考文献等常用论文结构，同时尽量减少复杂期刊排版命令，方便后续用 Pandoc 转成 Word 审阅稿。

## 适合做什么

- 用 `temp.tex` 写论文初稿。
- 用 XeLaTeX 编译 PDF，检查公式、图片和参考文献。
- 用 Pandoc 转换为 Word，便于导师、合作者或审稿前内部修改。
- 在定稿阶段再迁移到目标期刊模板。

## 环境准备

最低需要安装以下工具：

- TeX Live，并确保 `xelatex` 和 `bibtex` 可用。
- Pandoc。
- PowerShell。
- uv，用来创建 Python 环境并运行图片预处理脚本。

可选编辑器环境：

- VS Code。
- LaTeX Workshop 扩展。

本仓库的 `.vscode/settings.json` 已经写好 LaTeX Workshop 配方：

- `latexmk`：使用 `latexmk -xelatex` 自动处理多轮编译。
- `xelatex -> bibtex -> xelatex*2`：手动指定完整的参考文献编译流程。

为了避免打开文件后自动反复编译，仓库中已将 `latex-workshop.latex.autoBuild.run` 设置为 `never`。需要编译时，可在 VS Code 命令面板中执行 `LaTeX Workshop: Build with recipe` 并选择对应配方。

首次使用时，在仓库根目录运行：

```powershell
uv sync
```

当前本机已验证的主要环境：

- XeTeX 3.141592653-2.6-0.999998，TeX Live 2026。
- Pandoc 3.8，Lua 5.4。
- uv 0.10.4。
- uv Python 3.14.3。
- Python 依赖：`PyMuPDF>=1.24.0`。

更完整的文件说明、转换链路和维护细节见 [技术栈与实现说明](doc/technical-stack.md)。

## 快速开始

1. 编辑 `temp.tex`。
2. 运行 `uv sync` 准备 Python 依赖。
3. 编译 PDF，或在 VS Code 中选择 LaTeX Workshop 配方。
4. 运行 `.\convert-docx.ps1` 转换 Word 审阅稿。

## 第一次使用时主要改哪些文件

如果你刚开始接触 LaTeX，通常只需要关注这几个位置：

- `temp.tex`：论文正文。标题、作者、摘要、关键词、章节、图表、公式和引用都从这里改。
- `reference.bib`：参考文献数据库。新增论文、书籍、网页等文献条目时改这里。
- `fig/`：正文图片目录。把论文中需要使用的 PNG、JPG、PDF 图片放到这里。

写作时建议从 `temp.tex` 里的示例结构开始替换内容，不要一开始就大幅改导言区和转换脚本。需要了解每个文件的具体职责时，再看 [技术栈与实现说明](doc/technical-stack.md)。

## 第一次使用时先注意哪些文件

下面这些文件通常不需要在写作初稿时修改：

- `gbt7714.bst` 和 `gbt7714.csl`：分别用于 PDF 和 Word 的参考文献格式。
- `reference.docx`：Word 样式模板，只有需要调整 Word 输出样式时再改。
- `.vscode/settings.json`：VS Code 编译配方，已经配置好 LaTeX Workshop。
- `convert-docx.ps1`、`scripts/` 和 `filters/`：Word 转换流程相关脚本，日常写作只需要运行，不需要修改。
- `.pandoc-cache/`、`.venv/` 和 LaTeX 辅助文件：自动生成内容，不需要手动维护，也不需要提交到 Git。

## 编译 PDF

可以在 VS Code 中使用 LaTeX Workshop：

1. 打开 `temp.tex`。
2. 执行 `LaTeX Workshop: Build with recipe`。
3. 选择 `latexmk` 或 `xelatex -> bibtex -> xelatex*2`。

也可以在仓库根目录手动运行：

```powershell
xelatex -interaction=nonstopmode temp.tex
bibtex temp
xelatex -interaction=nonstopmode temp.tex
xelatex -interaction=nonstopmode temp.tex
```

生成结果为 `temp.pdf`。如果没有新增或修改参考文献，通常只运行一次或两次 `xelatex` 也可以。

## 转换为 Word

推荐直接运行根目录快捷脚本：

```powershell
.\convert-docx.ps1
```

生成结果为 `temp.docx`。该脚本等价于调用：

```powershell
.\scripts\tex-to-docx.ps1 `
    -InputFile temp.tex `
    -OutputFile temp.docx `
    -Bibliography reference.bib `
    -Csl gbt7714.csl `
    -ReferenceDoc reference.docx
```

脚本会自动完成这些步骤：

- 将 LaTeX 中引用的 PDF 图片转换为 Pandoc 更容易写入 Word 的 PNG 图片。
- 调用 Pandoc 和 Lua filter 生成 DOCX。
- 为 Word 表格补充三线表边框和表格段落样式，并自动居中、按内容调整表格宽度。
- 规范化 Word 文档中的项目样式 ID，使其使用 `Lpt...` 前缀。

如果需要自定义输入、输出或样式模板，可以直接调用 `scripts/tex-to-docx.ps1` 并传入参数。

## Word 样式模板

`reference.docx` 中的项目样式 ID 使用 `Lpt...` 前缀，例如 `LptHeading1`、`LptBodyText`、`LptTableCaption` 和 `LptReferenceItem`，以避免和 Word/Pandoc 内置样式 ID 重复。

替换或重新生成 `reference.docx` 后，可以运行：

```powershell
uv run python .\scripts\namespace-reference-docx-styles.py reference.docx
```

调整标题格式时，不要在 `reference.docx` 正文里手动输入 `1`、`1.1` 这类编号；标题编号需要通过 Word 多级列表绑定到 `LptHeading1`、`LptHeading2` 和 `LptHeading3` 样式。上面的脚本会自动修复这三个标题样式的多级编号关系。

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
