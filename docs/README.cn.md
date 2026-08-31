# LaTeX Pandoc 论文手稿模板

- 🌐 **[English README](../README.md)**：English guide for this template.
- 🗺️ **[技术文档索引](index.md)**：技术说明、维护文档和历史计划入口。
- 🛠️ **[技术栈与实现说明](technical-stack.md)**：文件职责、转换链路、脚本实现和维护说明。
- ✅ **[项目 TODO](../TODO.md)**：当前文档和转换流程维护事项。
- 🤝 **[参与贡献](#参与贡献)**：报告问题、分享使用场景或一起改进模板。

这是一个面向论文初稿写作的极简 LaTeX 模板。它保留标题、作者、摘要、关键词、章节、图表、公式、交叉引用和参考文献等常用论文结构，同时尽量减少复杂期刊排版命令，方便后续用 Pandoc 转成 Word 审阅稿。

如果这个模板帮你少踩了一些 LaTeX 和 Word 转换的坑，欢迎给仓库点个 Star。也欢迎你提交问题、分享使用场景，或一起改进这个模板。

## 适合做什么

- 用 `temp.tex` 写论文初稿。
- 用 XeLaTeX 编译 PDF，检查公式、图片和参考文献。
- 用 Pandoc 转换为 Word，便于导师、合作者或审稿前内部修改。
- 在定稿阶段再迁移到目标期刊模板。

## 环境准备

最低需要安装以下工具：

- TeX Live，并确保 `xelatex` 和 `bibtex` 可用。官方下载页面：[TeX Live](https://www.tug.org/texlive/acquire.html)。
- Pandoc。官方下载页面：[Installing pandoc](https://pandoc.org/installing.html)。
- uv，用来创建 Python 环境并运行转换脚本。官方下载页面：[Installing uv](https://docs.astral.sh/uv/getting-started/installation/)。
- Windows 使用 PowerShell，Linux 使用 Bash。Windows 自带 PowerShell，常见 Linux 发行版通常自带 Bash。

Git 是可选工具。如果不想安装 Git，也可以直接从 GitHub 下载 ZIP。官方下载页面：[Git Downloads](https://git-scm.com/downloads/)。

Word 转换流程会在 Windows 和 Ubuntu 上自动测试，测试基线为：

- Pandoc 3.8.3，Lua 5.4。
- uv 0.11.32 和 Python 3.10。
- Python 依赖：`lxml>=5.3.0` 和 `PyMuPDF>=1.24.0`。

PDF 编译仍使用 TeX Live 提供的 XeLaTeX 和 BibTeX。

更完整的文件说明、转换链路和维护细节见 [技术栈与实现说明](technical-stack.md)。

## 快速开始

下面从一个全新的本地目录开始说明。Windows 和 Linux 不同的命令会分别列出。

建议以本仓库的 `temp.tex` 作为写作母版，逐步替换其中的示例内容。当前转换流程围绕该模板采用的受控 LaTeX 子集设计；直接套用任意期刊模板或自定义模板，可能引入兼容预处理或 DOCX 后处理无法稳定处理的结构。

1. 获取项目文件。

   如果已经安装 Git，推荐用 `git clone`：

   ```powershell
   git clone https://github.com/Laxpud/latex-pandoc-template.git
   cd latex-pandoc-template
   ```

   如果没有安装 Git，也可以手动下载：

   1. 打开项目页面：<https://github.com/Laxpud/latex-pandoc-template>。
   2. 点击 `Code`。
   3. 选择 `Download ZIP`。
   4. 解压 ZIP 文件。
   5. 在终端中进入解压后的 `latex-pandoc-template` 文件夹。

2. 把 Word 转换器安装为 uv 工具：

   ```powershell
   uv tool install .
   ```

   这一步会在隔离环境中安装 Python 依赖，并让 `lpt-docx` 可以从任意论文目录调用。如果 uv 提示可执行文件目录不在 `PATH` 中，运行 `uv tool update-shell` 后重新打开终端。仓库维护者可以另行运行 `uv sync`，创建用于测试和开发的 `.venv/`。

3. 在项目目录中编译示例论文：

   ```console
   xelatex -interaction=nonstopmode temp.tex
   bibtex temp
   xelatex -interaction=nonstopmode temp.tex
   xelatex -interaction=nonstopmode temp.tex
   ```

   编译成功后，会得到 `temp.pdf`。

4. 转换 Word 审阅稿：

   ```console
   lpt-docx
   ```

   转换成功后，会得到 `temp.docx`。如果不希望安装用户级命令，仍可使用仓库入口 `.\convert-docx.ps1` 和 `./convert-docx.sh`。

5. 开始替换示例内容。

   优先改 `temp.tex`、`reference.bib` 和 `fig/`。建议先保持示例中的章节、图表、公式和参考文献结构，逐步替换为自己的论文内容。

## 第一次使用时主要改哪些文件

如果你刚开始接触 LaTeX，通常只需要关注这几个位置：

- `temp.tex`：论文正文。标题、作者、摘要、关键词、章节、图表、公式和引用都从这里改。
- `reference.bib`：参考文献数据库。新增论文、书籍、网页等文献条目时改这里。
- `fig/`：正文图片目录。把论文中需要使用的 PNG、JPG、PDF 图片放到这里。

写作时建议从 `temp.tex` 里的示例结构开始替换内容，不要一开始就大幅改导言区和转换脚本。需要了解每个文件的具体职责时，再看 [技术栈与实现说明](technical-stack.md)。

### 可选的 VS Code 写作流程

如果更喜欢图形化编辑器，可以安装 [VS Code](https://code.visualstudio.com/download) 和 [LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop) 扩展，然后在终端中打开项目：

```console
code .
```

如果 `code` 命令不可用，可以先打开 VS Code，选择 `File -> Open Folder...`，再选择项目文件夹。仓库提供的 `.vscode/settings.json` 会被自动读取，通常不需要修改，其中包含两个 LaTeX Workshop 配方：

- `latexmk`：使用 `latexmk -xelatex` 自动处理多轮编译。
- `xelatex -> bibtex -> xelatex*2`：明确执行完整的参考文献编译流程。

为了避免打开或保存文件时反复编译，仓库已将 `latex-workshop.latex.autoBuild.run` 设置为 `never`。需要生成 `temp.pdf` 时，打开 `temp.tex`，在命令面板中执行 `LaTeX Workshop: Build with recipe`，再选择任一配方。

## 第一次使用时先注意哪些文件

下面这些文件通常不需要在写作初稿时修改：

- `gbt7714.bst` 和 `gbt7714.csl`：分别用于 PDF 和 Word 的参考文献格式。
- `reference.docx`：Word 样式模板，只有需要调整 Word 输出样式时再改。
- `convert-docx.ps1`、`convert-docx.sh`、`src/lpt_docx/`、`scripts/` 和 `filters/`：Word 转换包与兼容脚本，日常写作只需要运行，不需要修改。
- `.pandoc-cache/`、`.venv/` 和 LaTeX 辅助文件：自动生成内容，不需要手动维护，也不需要提交到 Git。

## 编译 PDF

在任一平台的仓库根目录运行完整编译流程：

```console
xelatex -interaction=nonstopmode temp.tex
bibtex temp
xelatex -interaction=nonstopmode temp.tex
xelatex -interaction=nonstopmode temp.tex
```

生成结果为 `temp.pdf`。如果没有新增或修改参考文献，通常只运行一次或两次 `xelatex` 也可以。

## 转换为 Word

如果已在快速开始中完成 uv 工具安装，进入论文目录后直接运行：

```console
lpt-docx
lpt-docx manuscript.tex --output manuscript-review.docx
```

无参数时，`lpt-docx` 读取当前目录的 `temp.tex`。项目根目录默认为输入文件所在目录，输出默认为同名 `.docx`，参考文献默认为项目根目录的 `reference.bib`，缓存写入论文项目的 `.pandoc-cache/`。CSL、Word 样式模板、Lua filter 和后处理脚本由安装包自带。

如果直接在仓库中工作且没有安装命令，可运行当前平台对应的根目录入口。

Windows：

```powershell
.\convert-docx.ps1
```

Linux：

```bash
./convert-docx.sh
```

两个入口都会调用同一份 Python 核心并生成 `temp.docx`，等价的直接命令为：

```console
uv run lpt-docx temp.tex --output temp.docx --bibliography reference.bib
```

转换器开发期可以使用 `uv tool install --editable /path/to/latex-pandoc-template`，使已安装命令继续跟随当前工作区。

脚本会自动完成这些步骤：

- 展开少量常用兼容宏，例如 `\gls`、`\SI`、`\SIrange`、`\ang` 和 `\bm`。
- 将 LaTeX 中引用的 PDF 图片转换为 Pandoc 更容易写入 Word 的 PNG 图片。
- 调用 Pandoc 和 Lua filter 生成 DOCX。
- 为 Word 表格补充三线表边框和表格段落样式，并自动居中、按内容调整表格宽度。
- 规范化 Word 文档中的项目样式 ID，使其使用 `Lpt...` 前缀。

如果需要自定义输入、输出、项目根目录、参考文献、附加资源目录、样式模板、缓存目录或图片 DPI，可以传入 `--input`、`--output`、`--project-root`、`--bibliography`、`--resource-dir`、`--csl`、`--reference-doc`、`--cache-dir` 或 `--image-dpi`。`--bibliography` 和 `--resource-dir` 可重复使用。命令行中显式传入的相对路径按调用目录解析，TeX 正文内的资源路径按论文项目根目录和 `\graphicspath` 解析。

## Word 样式模板

`reference.docx` 中的项目样式 ID 使用 `Lpt...` 前缀，例如 `LptHeading1`、`LptBodyText`、`LptTableCaption` 和 `LptReferenceItem`，以避免和 Word/Pandoc 内置样式 ID 重复。

替换或重新生成 `reference.docx` 后，可以运行：

```console
uv run python scripts/namespace-reference-docx-styles.py reference.docx
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

## 参与贡献

欢迎参与这个项目，尤其是下面这些方向：

- 报告 LaTeX 编译或 Pandoc 转 Word 时遇到的问题。
- 补充更清晰的新手使用说明。
- 改进 Word 样式模板、图表格式或参考文献格式。
- 分享不同论文写作场景下的兼容性问题和解决办法。

如果你准备提交改动，建议先确认生成文件没有被一起提交；复杂改动可以在提交说明里用子条目写清楚主要变化。
