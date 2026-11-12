# LaTeX Pandoc 论文手稿模板

- 🌐 **[English README](<../README.md>)**：英文入口。
- 🛠️ **[技术说明](<technical-stack.md>)**：转换实现、样式和排错。
- 🗺️ **[文档索引](<index.md>)** · ✅ **[项目 TODO](<../TODO.md>)**

本项目提供极简 LaTeX 论文模板和可复用的 Pandoc 转 Word 工具。每篇新论文只需复制 [模板目录](<../template/>)；转换器留在本仓库，从论文目录调用即可。模板保留作者及单位、摘要、关键词、图表、公式、引用和交叉引用，不依赖期刊专用文档类。

本项目用于初稿写作和审阅，不是最终投稿模板。如果它对你有帮助，欢迎点 Star、提问题或参与贡献。

## 仓库结构

```text
template/                    新建论文时复制整个目录
  temp.tex                   论文主文件
  reference.bib              参考文献数据库
  gbt7714.bst                PDF 参考文献样式
  fig/                       示例图片
  .vscode/settings.json     LaTeX Workshop 编译配方
  .gitignore                 生成文件忽略规则
  LICENSE                    随模板复制的许可说明
src/lpt_docx/                转换模块
  resources/                 Lua filter、CSL 和 Word 样式模板
bin/                        仓库调用入口
  lpt-docx                   Bash 入口，支持软链
  lpt-docx.ps1               PowerShell 入口
tests/                      现有转换测试
```

复制后的模板已包含 PDF 编译所需的论文文件。Python 代码、Lua filter 和 Word 转换资源由工具统一维护，不需要再复制到每篇论文里。

## 环境准备

- PDF 编译需要 TeX Live，并确保 `xelatex` 和 `bibtex` 可用：[TeX Live](https://www.tug.org/texlive/acquire.html)。
- Word 转换需要 Pandoc：[Installing Pandoc](https://pandoc.org/installing.html)。
- 转换器通过 uv 管理 Python 环境：[Installing uv](https://docs.astral.sh/uv/getting-started/installation/)。
- 仓库入口在 Linux 使用 Bash，在 Windows 使用 PowerShell。

现有 CI 面向 Windows 和 Ubuntu，基线为 Pandoc 3.8.3、Lua 5.4、uv 0.11.32 和 Python 3.10。Python 依赖为 `lxml>=5.3.0` 和 `PyMuPDF>=1.24.0`，由 uv 自动准备。PDF 编译使用本地 TeX Live。

## 快速开始

### 1. 获取仓库

```console
git clone https://github.com/Laxpud/latex-pandoc-template.git
cd latex-pandoc-template
```

没有 Git 时，可以在 [GitHub](https://github.com/Laxpud/latex-pandoc-template) 中通过 `Code -> Download ZIP` 下载并解压。

### 2. 准备转换命令

Linux 下，在仓库根目录将 [Bash 入口](<../bin/lpt-docx>) 软链到个人 bin 目录：

```bash
mkdir -p "$HOME/bin"
ln -s "$(pwd)/bin/lpt-docx" "$HOME/bin/lpt-docx"
export PATH="$HOME/bin:$PATH"
```

可以改用任何已加入 `PATH` 的个人 bin 目录；必要时把 `PATH` 设置加入 shell 配置。此命令不会覆盖已有软链或可执行文件。使用软链时请保留工具仓库：入口会沿绝对或相对软链逐级定位工具环境，但不改变当前论文工作目录。

Windows 用户，或在任一平台更偏好安装命令的用户，可以运行：

```console
uv tool install .
```

如果 uv 的可执行文件目录尚未加入 `PATH`，运行 `uv tool update-shell` 后重新打开终端。安装后的命令与仓库入口使用同一个 Python 包。

### 3. 复制模板，新建论文

Linux 下，从仓库根目录运行：

```bash
cp -a template ../my-paper
cd ../my-paper
```

Windows PowerShell：

```powershell
Copy-Item -Recurse template ..\my-paper
Set-Location ..\my-paper
```

选择一个新的目标目录，再替换示例内容；隐藏的编辑器配置和生成文件忽略规则也会一起复制。论文目录可以自由改名；如果同时重命名主 TeX 文件，转换时传入新文件名即可。

### 4. 编译 PDF 并转换 Word

在复制后的论文目录中运行：

```console
xelatex -interaction=nonstopmode temp.tex
bibtex temp
xelatex -interaction=nonstopmode temp.tex
xelatex -interaction=nonstopmode temp.tex
lpt-docx
```

PDF 和 Word 审阅稿会生成在主 TeX 文件旁边。主文件重命名后可运行：

```console
lpt-docx manuscript.tex
lpt-docx manuscript.tex --output manuscript-review.docx
```

## 日常编辑的文件

在复制后的论文目录中，主要编辑以下文件的副本：

- [temp.tex](<../template/temp.tex>)：标题、作者、编号单位、通讯作者邮箱、摘要、关键词和正文。
- [reference.bib](<../template/reference.bib>)：参考文献条目。
- [fig/](<../template/fig/>)：需要随论文保留的图片。

[BibTeX 样式](<../template/gbt7714.bst>) 随论文复制，用于 PDF 编译。转换器的 [CSL](<../src/lpt_docx/resources/gbt7714.csl>) 和 [Word 样式模板](<../src/lpt_docx/resources/reference.docx>) 则保留在工具仓库中。

### 可选的 VS Code 写作流程

安装 [VS Code](https://code.visualstudio.com/download) 和 [LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop)，然后打开复制后的论文目录，而不是转换工具仓库：

```console
code .
```

随模板复制的 [编辑器配置](<../template/.vscode/settings.json>) 提供 `latexmk` 和 `xelatex -> bibtex -> xelatex*2` 两个编译配方。自动编译默认关闭，需要时执行 `LaTeX Workshop: Build with recipe`。配方使用当前文档名称，重命名主文件后不需要修改配置。

## 转换选项

无参数时，`lpt-docx` 读取当前论文目录中的 [temp.tex](<../template/temp.tex>) 副本。项目根目录默认为输入文件所在目录，输出使用输入文件名加 `.docx` 后缀，参考文献默认使用论文自带的 [reference.bib](<../template/reference.bib>)，缓存写入论文项目的 `.pandoc-cache/`。默认 Lua filter、CSL 和 Word 样式来自转换器自身的包，而不是论文目录或命令调用目录。

现有命令行选项保持可用：

```console
lpt-docx --help
lpt-docx paper.tex --bibliography references.bib --output review.docx
lpt-docx tex/paper.tex --project-root . --resource-dir extra-assets
```

命令行中的相对路径按调用目录解析；TeX 图片路径按论文项目根目录和 `\graphicspath` 解析。`--bibliography` 与 `--resource-dir` 可以重复使用；同时支持 `--input`、`--csl`、`--reference-doc`、`--cache-dir` 和 `--image-dpi`。

不安装或软链命令时，也可以在论文目录中用绝对路径调用仓库入口：

```bash
/path/to/latex-pandoc-template/bin/lpt-docx manuscript.tex
```

```powershell
& "C:\tools\latex-pandoc-template\bin\lpt-docx.ps1" manuscript.tex
```

## 写作建议

- 从现有模板逐步替换示例内容；任意期刊模板可能使用转换器不支持的命令。
- 保持作者上标与单位编号一致；修改邮箱时同步修改 `mailto:` 目标和显示文字，详见 [Front Matter](<technical-stack.md#front-matter>)。
- 如果需要正文另起一页，保留关键词与引言之间的显式分页命令。
- 使用标准 `\section`、`\subsection`、`\subsubsection`、`figure`、`table`、`equation`、`\label`、`\ref` 和 `\cite` 结构，表格优先使用 `booktabs`。
- 图片保留在论文项目内。PDF 图片会为 Word 渲染为缓存 PNG，普通 PNG 和 JPG 可以直接引用。
- 初稿阶段避免期刊专用双栏、页眉页脚和复杂标题页，内容定稿后再迁移到期刊模板。

## 维护与迁移

原先位于仓库根目录的论文文件现已归入模板目录；转换模块与资源全部归入 [Python 包](<../src/lpt_docx/>)。旧的根目录转换入口和旧 Python 脚本入口由 bin 入口替代；已安装的 `lpt-docx` 命令及命令行参数保持支持。原先以非 editable 方式安装的工具，需要重新安装或升级才能使用重构后的版本。

开发时在仓库根目录运行：

```console
uv sync
uv run python -m unittest discover -s tests -v
uv build
```

替换 Word 样式模板后，需要修复其样式编号时，在仓库根目录运行：

```console
uv run python -m lpt_docx.namespace_reference_docx_styles src/lpt_docx/resources/reference.docx
```

生成文档、LaTeX 辅助文件、Python 环境和缓存不属于源文件。[模板忽略规则](<../template/.gitignore>) 会随论文一起复制；原始 PDF 图片仍可纳入版本控制。样式维护与排错方法见 [技术说明](<technical-stack.md>)。

## 参与贡献

欢迎报告实际转换问题、改进文档，或完善图表、参考文献和 Word 样式。提交时排除生成物，并在非简单改动的提交正文中说明主要变化和验证方式。
