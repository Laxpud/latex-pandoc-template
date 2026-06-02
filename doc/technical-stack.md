# 技术栈与实现说明

本文档记录本项目从 LaTeX 手稿到 PDF、Word 审阅稿的主要技术栈、转换链路和维护注意事项。README 面向日常使用，本文件面向后续维护和扩展。

## 整体目标

本项目不是完整期刊模板，而是一个适合论文初稿阶段使用的中间模板。它的核心取舍是：写作阶段优先保留论文语义和审阅便利性，最终投稿阶段再迁移到目标期刊模板。

采用“极简 LaTeX 初稿模板 + Pandoc Word 审阅稿”的原因：

- LaTeX 适合维护公式、图表、交叉引用和 BibTeX 参考文献。
- Word 更适合导师、合作者和审稿前内部修改。
- Pandoc 对标准 LaTeX 结构支持较好，但对复杂期刊模板命令、双栏布局、复杂标题页和自定义计数器支持不稳定。
- 因此，初稿模板应尽量使用标准命令表达论文语义，避免把最终排版逻辑提前混入写作文件。

项目希望稳定支持的内容包括：

- 标题、作者、日期、摘要、关键词。
- `\section`、`\subsection`、`\subsubsection` 三级标题。
- 标准 `figure`、`table`、`equation` 环境。
- `\label`、`\ref` 和 `\cite`。
- PDF、PNG、JPG 等常见图片格式。
- GB/T 7714 风格参考文献。
- Word 中的中文图题、表题、公式编号和项目自定义样式。

## 环境与依赖

当前仓库已在以下环境中验证：

- 操作环境：Windows + PowerShell。
- TeX 引擎：XeTeX 3.141592653-2.6-0.999998，TeX Live 2026。
- 参考文献编译：BibTeX，随 TeX Live 提供。
- Pandoc：3.8，内置 Lua 5.4。
- uv：0.10.4。
- Python：由 uv 管理，当前为 Python 3.14.3。
- Python 依赖：`PyMuPDF>=1.24.0`。

各工具职责如下：

- TeX Live 提供 `xelatex`、`bibtex` 和常用 LaTeX 宏包，用于生成 PDF。
- XeLaTeX 负责中文、数学公式、图片和最终 PDF 排版。
- BibTeX 根据 `reference.bib` 和 `gbt7714.bst` 生成 PDF 侧参考文献。
- Pandoc 负责把预处理后的 LaTeX 输入转换为 DOCX。
- Pandoc citeproc 根据 `reference.bib` 和 `gbt7714.csl` 生成 Word 侧参考文献。
- Pandoc Lua filter 负责补充中文编号、交叉引用和 Word 自定义样式。
- PowerShell 负责串联转换流程，并直接处理 DOCX 中的 Open XML。
- uv 负责创建 Python 环境并运行图片预处理、样式规范化脚本。
- PyMuPDF 用于把 PDF 图片渲染为 Pandoc DOCX writer 更容易处理的 PNG。
- VS Code 和 LaTeX Workshop 提供编辑器内的 PDF 编译入口。

`pyproject.toml` 中声明 Python 最低版本为 `>=3.10`。日常使用时优先运行：

```powershell
uv sync
```

这样 uv 会根据 `uv.lock` 准备项目环境，避免手工安装 Python 依赖导致版本漂移。

## 项目文件说明

本节集中说明仓库中主要文件和目录的职责。README 只保留第一次使用时需要关注的文件，维护时以本节为准。

### 写作与资源文件

- `temp.tex`：论文主文件。标题、作者、摘要、关键词、章节、图表、公式、交叉引用和正文引用都在这里维护。
- `reference.bib`：BibTeX 参考文献数据库。PDF 编译和 Word 转换共用这一份文献数据。
- `fig/`：正文图片目录。建议放入需要随论文一起保留的 PNG、JPG、PDF 等图片资源。
- `temp.cls`：预留的类文件位置。目前为空文件，不参与当前模板逻辑。

### 参考文献与 Word 样式

- `gbt7714.bst`：PDF 编译时 BibTeX 使用的 GB/T 7714 样式文件。
- `gbt7714.csl`：Pandoc citeproc 转 Word 时使用的 GB/T 7714 CSL 样式文件。
- `reference.docx`：Pandoc 的 Word 样式模板，包含项目自定义的 `Lpt...` 样式。

### 转换入口与脚本

- `convert-docx.ps1`：项目推荐的 Word 转换快捷入口。它固定使用当前项目文件名，把 `temp.tex` 转换为 `temp.docx`。
- `scripts/tex-to-docx.ps1`：Word 转换主脚本，负责串联图片预处理、Pandoc、表格后处理和样式规范化。
- `scripts/prepare-pandoc-images.py`：图片预处理脚本，把 LaTeX 中引用的 PDF 图片渲染为 PNG，并写入 Pandoc 临时输入文件。
- `scripts/apply-docx-table-styles.ps1`：DOCX 表格后处理脚本，直接修改 `word/document.xml`，补充三线表边框、居中、自适应宽度和表格段落样式。
- `scripts/namespace-reference-docx-styles.py`：样式规范化脚本，维护 `Lpt...` 样式 ID、标题编号和文档内样式引用。
- `filters/latex-crossref-cn.lua`：Pandoc Lua filter，负责中文图表题、公式编号、交叉引用、front matter、参考文献和 Word 段落样式。

### 编辑器、依赖和缓存

- `.vscode/settings.json`：VS Code 和 LaTeX Workshop 的本项目编译配方。
- `pyproject.toml`：Python 项目配置，声明 `PyMuPDF` 等脚本依赖。
- `uv.lock`：uv 锁定文件，用于复现 Python 依赖环境。
- `.pandoc-cache/`：Pandoc 转 Word 时生成的临时目录，包括临时 TeX 输入和缓存 PNG 图片。该目录被 Git 忽略。
- `.venv/`：uv 创建的本地 Python 虚拟环境。该目录被 Git 忽略。
- `refference/`：原始期刊模板或参考材料目录。当前被 Git 忽略，名称沿用了仓库已有拼写。

### 生成文件

以下文件通常由编译或转换生成，不需要手动维护：

- `temp.pdf`：LaTeX 编译生成的 PDF。
- `temp.docx`：Word 转换生成的审阅稿。
- `temp.aux`、`temp.bbl`、`temp.blg`、`temp.log`、`temp.synctex.gz` 等：LaTeX 辅助文件。

这些生成文件大多已在 `.gitignore` 中忽略。例外是 `reference.docx`，它是样式模板，不是普通输出文件，需要保留在仓库中。

## LaTeX 写作层

主文件为 `temp.tex`，使用 `article` 文档类，并加载常用论文写作包：

- `ctex`：中文支持。
- `amsmath`：数学公式。
- `booktabs`：三线表。
- `natbib`：参考文献引用。
- `graphicx`：图片插入。
- `geometry`：页面边距。

图片搜索路径由以下命令指定：

```latex
\graphicspath{{fig/}{refference/fig/}}
```

其中 `fig/` 是项目正文图片目录，`refference/` 主要用于存放原始期刊模板或参考材料，并被 `.gitignore` 忽略。正式维护时建议：

- 需要跟随论文一起提交的图片放入 `fig/`。
- 原始模板、样例文件或不需要提交的参考材料放入 `refference/`。
- 尽量保留标准 `figure`、`table`、`equation` 环境。
- 避免在初稿阶段加入双栏、页眉页脚、复杂标题页和期刊专用宏。

## PDF 编译链路

PDF 编译使用 XeLaTeX 和 BibTeX：

```powershell
xelatex -interaction=nonstopmode temp.tex
bibtex temp
xelatex -interaction=nonstopmode temp.tex
xelatex -interaction=nonstopmode temp.tex
```

每一步的作用：

- 第一次 `xelatex` 读取 `temp.tex`，生成 `temp.aux`，记录引用、交叉引用和参考文献请求。
- `bibtex temp` 读取 `temp.aux`、`reference.bib` 和 `gbt7714.bst`，生成 `temp.bbl`。
- 第二次 `xelatex` 把 `temp.bbl` 写入 PDF，并开始解析参考文献和交叉引用编号。
- 第三次 `xelatex` 用于稳定目录、图表、公式和参考文献引用等编号结果。

PDF 侧参考文献配置在 `temp.tex` 末尾：

```latex
\bibliographystyle{gbt7714}
\bibliography{reference}
```

因此 PDF 编译使用：

- `gbt7714.bst`：BibTeX 样式。
- `reference.bib`：参考文献数据库。

如果没有新增参考文献、没有改变 `\label` 或章节结构，通常不需要完整四步；但文档中保留完整流程，便于第一次编译或排查引用问题。

## VS Code 编译配方

`.vscode/settings.json` 已经配置 LaTeX Workshop：

- `latex-workshop.latex.autoBuild.run` 为 `never`。
- `latexmk` recipe 使用 `latexmk -xelatex`。
- `xelatex -> bibtex -> xelatex*2` recipe 显式执行完整多轮编译。

关闭自动编译的原因：

- 参考文献多轮编译耗时较长。
- 保存文件时自动触发编译容易造成中间文件频繁变化。
- 手动选择 recipe 更适合论文写作和排错。

两个 recipe 的使用建议：

- `latexmk` 适合日常写作，自动判断需要运行几轮。
- `xelatex -> bibtex -> xelatex*2` 适合第一次完整编译、参考文献更新后编译、或需要排查 BibTeX/交叉引用问题时使用。

LaTeX Workshop 工具参数中使用 `%DOC%` 和 `%DOCFILE%`：

- `%DOC%` 代表当前主 TeX 文件路径。
- `%DOCFILE%` 代表不带扩展名的文件名，供 BibTeX 使用。

## Word 转换链路

推荐入口为根目录下的快捷脚本：

```powershell
.\convert-docx.ps1
```

它会切换到仓库根目录，然后调用：

```powershell
.\scripts\tex-to-docx.ps1 `
    -InputFile "temp.tex" `
    -OutputFile "temp.docx" `
    -Bibliography "reference.bib" `
    -Csl "gbt7714.csl" `
    -ReferenceDoc "reference.docx"
```

需要注意：`scripts/tex-to-docx.ps1` 自身仍保留一组通用默认参数：

- `InputFile = "temp.tex"`
- `OutputFile = "temp-crossref.docx"`
- `Bibliography = "temp-ref.bib"`
- `Csl = "temp-ref.csl"`
- `ReferenceDoc = ""`
- `ImageDpi = 300`

这些默认值不是当前项目推荐入口。当前项目推荐通过 `convert-docx.ps1` 传入实际文件名，保证使用 `reference.bib`、`gbt7714.csl` 和 `reference.docx`。

`scripts/tex-to-docx.ps1` 的主要流程：

1. 设置 `$ErrorActionPreference = "Stop"`，确保中间步骤失败时立即停止。
2. 计算仓库根目录、Lua filter、Pandoc 缓存目录和图片缓存目录。
3. 调用 `scripts/prepare-pandoc-images.py` 生成 `.pandoc-cache/temp-pandoc.tex`。
4. 组装 Pandoc 参数并执行 DOCX 转换。
5. 调用 `scripts/apply-docx-table-styles.ps1` 修正表格 Open XML。
6. 调用 `scripts/namespace-reference-docx-styles.py` 规范化 DOCX 样式 ID。

Pandoc 核心参数包括：

- 输入文件：`.pandoc-cache/temp-pandoc.tex`。
- 输出文件：由 `-OutputFile` 指定。
- `--citeproc`：启用 Pandoc 内置参考文献处理。
- `--lua-filter=filters/latex-crossref-cn.lua`：启用中文编号和样式处理。
- `--bibliography=...`：指定 BibTeX 数据库。
- `--csl=...`：指定 Word 侧参考文献样式。
- `--resource-path=.;fig;refference/fig;.pandoc-cache/images`：指定图片搜索路径。
- `--reference-doc=reference.docx`：指定 Word 样式模板。

缓存目录 `.pandoc-cache/` 被 `.gitignore` 忽略，里面的内容可随时删除后重新生成。

## 图片预处理

Word 不直接支持将 PDF 矢量图作为普通图片稳定写入 DOCX。为了兼顾 LaTeX PDF 输出和 Word 审阅稿，本项目允许在 `temp.tex` 中继续引用 PDF 图片，然后在 Word 转换前自动渲染为 PNG。

图片预处理由 `scripts/prepare-pandoc-images.py` 完成，命令参数包括：

- `--input`：源 TeX 文件。
- `--output`：写给 Pandoc 使用的临时 TeX 文件。
- `--cache-dir`：PNG 图片缓存目录。
- `--dpi`：PDF 渲染 DPI，默认 300。

脚本会扫描：

- `\graphicspath{...}`：读取额外图片搜索目录。
- `\includegraphics[...]{...}`：定位正文引用图片。

查找 PDF 图片时会考虑：

- `\includegraphics` 中直接写出的路径。
- 当前 TeX 文件所在目录。
- 默认 `fig/` 目录。
- `\graphicspath` 中声明的目录。
- 没写扩展名时，额外尝试 `.pdf`。

只会转换扩展名为空或 `.pdf` 的图片引用。PNG、JPG 等位图保持原样。

缓存 PNG 文件名由三部分组成：

- 原 PDF 文件名 stem。
- PDF 绝对路径的 SHA-1 摘要前 10 位。
- DPI，例如 `300dpi`。

这种命名可以避免不同目录下同名 PDF 图片互相覆盖。

缓存失效判断：

- 缓存 PNG 不存在时重新渲染。
- 缓存 PNG 早于源 PDF 修改时间时重新渲染。
- 缓存 PNG 的 pHYs DPI 元数据与当前 DPI 不一致时重新渲染。

渲染规则：

- 使用 PyMuPDF 打开 PDF。
- 只渲染第一页。
- 使用 `dpi / 72.0` 计算缩放矩阵。
- 输出 PNG 并写入 DPI 元数据。

常见失败场景：

- `uv sync` 未运行，导致 PyMuPDF 缺失。
- `\includegraphics` 引用的 PDF 文件不存在。
- `\graphicspath` 中路径写错。
- PDF 文件为空或无法打开。
- 多页 PDF 图片只需要第一页以外的内容；当前脚本不会渲染后续页面。

## Pandoc Lua Filter

`filters/latex-crossref-cn.lua` 是 Word 转换的核心语义修正层。它在 Pandoc AST 上工作，不直接修改源 TeX 文件。

主要状态包括：

- `refs`：保存图、表、公式 label 到编号的映射。
- `counters`：保存图、表、公式计数器。
- `styles`：保存项目自定义 Word 样式名。

### Front Matter

filter 会读取 Pandoc meta 中的 `title`、`author`、`date` 和 `abstract`，转换为正文开头的自定义样式段落：

- `LptPaperTitle`
- `LptAuthorBlock`
- `LptPaperDate`
- `LptAbstract`

作者之间使用不换行空格保持 Word 中的视觉间距稳定。摘要首段会自动补齐或保留 `摘要：` 前缀。

处理完成后，filter 会清空 meta 中的 title、author、date 和 abstract，避免 Pandoc DOCX writer 再按默认方式输出一遍。

### 标题和正文

`Header` 节点会被转换为带自定义样式的 `Div`：

- 一级标题：`LptHeading1`
- 二级标题：`LptHeading2`
- 三级标题：`LptHeading3`

普通段落和普通行会使用 `LptBodyText`。关键词段落通过开头的 `关键词` 或加粗 `关键词` 识别，并使用 `LptKeywords`。

### 图、表、公式编号

filter 先遍历文档块收集编号：

- `Figure` 且有 identifier 时计入图编号。
- `Table` 或包含表格的 `Div`，且 identifier 以 `tab:` 开头时计入表编号。
- 单独显示数学段落中含 `\label{...}` 时计入公式编号。

随后重写正文块：

- 图片 caption 自动加 `图 N` 前缀，并使用 `LptFigureCaption`。
- 表格 caption 自动加 `表 N` 前缀，并使用 `LptTableCaption`。
- 带 label 的显示公式会改写为带左右 tab 和 `(N)` 的段落，并使用 `LptEquationNumbered`。

公式处理会去掉 `\begin{equation}`、`\end{equation}` 和 `\label{...}`，只保留公式主体。

### 交叉引用

Pandoc 会把部分 LaTeX `\ref` 转成带 `reference` 属性的 link。filter 根据 link 的目标 label 查找 `refs`：

- 公式引用替换为 `(N)`。
- 图、表引用替换为 `N`。

源文本中通常写作 `图~\ref{...}`、`表~\ref{...}`、`式~\ref{...}`，因此 filter 只替换编号本身，不重复写“图”“表”“式”。

### 参考文献

Pandoc citeproc 生成的参考文献容器通常是 identifier 为 `refs` 的 `Div`。filter 会：

- 在参考文献前插入 `参考文献` 标题，并使用 `LptReferencesHeading`。
- 将每个 `csl-entry` 中的段落改为 `LptReferenceItem`。

参考文献内容本身仍由 Pandoc citeproc 和 `gbt7714.csl` 负责。

### CJK 与 ASCII 空格修正

filter 保留了一组 UTF-8 字符级函数，可用于删除 CJK 字符和 ASCII token 之间的空格。这个功能最初用于处理中文与英文、数字、公式或代码相邻时的空格问题。

该功能目前默认关闭，因为这些空格有时来自源 TeX 文件本身，而不是 Pandoc 自动增加的内容。默认关闭可以避免转换时意外改变作者在源文件中实际写下的空格。

如需恢复旧行为，可以使用以下两种方式之一：

- 将 `filters/latex-crossref-cn.lua` 顶部 `config.normalize_cjk_ascii_spacing` 改为 `true`。
- 直接调用 Pandoc 时传入 metadata：`-M lpt-normalize-cjk-ascii-spacing=true`。

开启后，该处理仍会跳过作者段落，因为作者之间故意使用不换行空格控制视觉间距。

### 表格样式标记

Lua filter 会在 Pandoc AST 层面为表头和表身单元格内容加样式：

- 表头：`LptTableHeader`
- 表身：`LptTableBody`

但 Word 中三线表边框、自适应宽度和居中还需要后续 Open XML 脚本补充。

## Word 样式系统

`reference.docx` 是 Pandoc 的 Word 样式模板。项目自定义样式统一使用 `Lpt...` 前缀，避免和 Word、Pandoc 或用户系统中的内置样式 ID 冲突。

主要样式用途：

- `LptPaperTitle`：论文标题。
- `LptAuthorBlock`：作者信息。
- `LptPaperDate`：日期。
- `LptAbstract`：摘要。
- `LptKeywords`：关键词。
- `LptHeading1`：一级标题。
- `LptHeading2`：二级标题。
- `LptHeading3`：三级标题。
- `LptBodyText`：正文。
- `LptFigureCaption`：图题。
- `LptTableCaption`：表题。
- `LptEquationNumbered`：带编号公式。
- `LptReferencesHeading`：参考文献标题。
- `LptReferenceItem`：参考文献条目。
- `LptTableHeader`：表头单元格段落。
- `LptTableBody`：表身单元格段落。

命名空间化样式 ID 的原因：

- Pandoc 和 Word 都可能使用 `Heading1`、`BodyText` 等通用 ID。
- 不同语言版本 Word 中样式显示名可能不同，但 style ID 是 Open XML 中真正被引用的字段。
- 使用 `Lpt...` 可以减少样式模板、Pandoc 输出和后处理脚本之间的冲突。
- 后续维护时只要保持 `Lpt...` ID 稳定，就可以替换样式外观而不改变转换逻辑。

## DOCX 表格后处理

`scripts/apply-docx-table-styles.ps1` 会直接修改 DOCX 压缩包中的 `word/document.xml`。

处理范围：

- 打开目标 DOCX 到临时文件。
- 读取 `word/document.xml`。
- 遍历所有 `w:tbl`。
- 修改表格属性、边框和单元格段落样式。
- 写回 `word/document.xml`。
- 用处理后的临时 DOCX 覆盖原输出文件。

表格布局处理：

- 设置表格居中：`w:jc` 为 `center`。
- 设置表格宽度自动：`w:tblW` 为 `auto`。
- 设置表格布局自适应：`w:tblLayout` 为 `autofit`。

三线表边框处理：

- 表格整体 top 和 bottom 使用黑色单线。
- 清除 left、right、insideH、insideV。
- 第一行单元格 top 为粗线，bottom 为较细线。
- 最后一行单元格 bottom 为粗线。
- 中间行清除上下边框。

段落样式处理：

- 第一行所有单元格段落使用 `LptTableHeader`。
- 其余行所有单元格段落使用 `LptTableBody`。
- 脚本参数允许覆盖表头和表身样式名，但项目默认使用上述两个样式。

这个脚本不修改 `word/styles.xml`，也不负责创建样式；样式必须存在于 `reference.docx` 或由样式规范化脚本维护。

## 样式规范化脚本

`scripts/namespace-reference-docx-styles.py` 用于规范化 DOCX 中的项目样式 ID。它既可以处理 `reference.docx`，也会在 Word 转换完成后处理输出 DOCX。

主要职责：

- 将未加前缀的项目样式 ID 映射为 `Lpt...`。
- 重写文档内 `pStyle`、`rStyle` 和 `tblStyle` 引用。
- 在缺少 `LptHeading1`、`LptHeading2`、`LptHeading3` 时，从 `Heading1`、`Heading2`、`Heading3` 复制项目标题样式。
- 为项目标题样式绑定多级编号。
- 确保 `word/numbering.xml` 中存在项目标题编号定义。
- 清理重复 style ID。
- 将非项目样式中的 `Lpt...` 引用恢复为内置样式引用，避免污染 Word 内置样式。
- 修正 `LptBodyText` 与正文基准样式之间的关系。

样式 ID 映射集中在脚本中的 `STYLE_ID_MAP`。维护样式时应优先修改这张映射，而不是在多个脚本中散落新增样式名。

标题编号使用固定编号 ID：

- `abstractNumId = 99`
- `numId = 99`

三级标题编号格式为：

- 一级：`%1`
- 二级：`%1.%2`
- 三级：`%1.%2.%3`

标题缩进由脚本写入 `word/numbering.xml`。如果在 Word 中手工调整编号样式后又运行该脚本，脚本会按当前规则重新写入项目标题编号关系。

## 维护与排错

### Pandoc 找不到图片

检查顺序：

1. `\includegraphics` 中的文件名是否正确。
2. 图片是否在 `fig/`、TeX 文件同目录或 `\graphicspath` 声明目录中。
3. `scripts/tex-to-docx.ps1` 的 `--resource-path` 是否包含该目录。
4. 如果图片是 PDF，确认 `prepare-pandoc-images.py` 是否成功生成缓存 PNG。

### PDF 图片没有更新

可能原因：

- 源 PDF 修改时间没有晚于缓存 PNG。
- 使用的 DPI 没变，缓存仍被判断为有效。
- 引用路径指向了另一个同名 PDF。

可删除 `.pandoc-cache/images/` 后重新运行 `.\convert-docx.ps1`。

### 引用编号异常

检查内容：

- 图 label 是否在 `figure` 环境中。
- 表 label 是否以 `tab:` 开头。
- 公式是否是单独显示数学段落，并包含 `\label{...}`。
- 正文是否使用 `图~\ref{...}`、`表~\ref{...}`、`式~\ref{...}` 这类写法。
- 是否引入了 Pandoc 无法稳定识别的自定义引用命令。

### Word 标题编号异常

优先运行：

```powershell
uv run python .\scripts\namespace-reference-docx-styles.py reference.docx
```

然后重新生成 DOCX。不要在 `reference.docx` 正文中手工输入 `1`、`1.1` 作为标题编号；标题编号应由多级列表和 `LptHeading1`、`LptHeading2`、`LptHeading3` 样式绑定。

### Word 样式丢失

检查内容：

- 转换时是否传入 `-ReferenceDoc reference.docx`。
- `reference.docx` 中是否存在对应的 `Lpt...` 样式。
- 输出 DOCX 是否经过 `namespace-reference-docx-styles.py`。
- Lua filter 中的 `styles` 表是否和 `reference.docx` 中的样式 ID 一致。

### 参考文献异常

PDF 侧检查：

- `reference.bib` 中是否存在对应 cite key。
- 是否运行过 `bibtex temp`。
- `temp.bbl` 是否更新。

Word 侧检查：

- `scripts/tex-to-docx.ps1` 是否传入 `--citeproc`。
- `-Bibliography` 是否指向 `reference.bib`。
- `-Csl` 是否指向 `gbt7714.csl`。
- Pandoc 输出中是否存在 identifier 为 `refs` 的参考文献容器。

### 表格不是三线表

检查内容：

- `scripts/apply-docx-table-styles.ps1` 是否运行成功。
- 输出 DOCX 是否被后续 Word 操作覆盖了表格边框。
- 表格是否是 Pandoc 能识别的标准表格结构。
- `reference.docx` 中是否存在 `LptTableHeader` 和 `LptTableBody`。

## 维护建议

- README 只保留日常使用说明和关键入口。
- 技术细节、脚本职责和样式系统说明集中放在本文档。
- 修改转换流程时，同时检查 `convert-docx.ps1`、`scripts/tex-to-docx.ps1` 和本文档。
- 修改 Word 样式时，优先通过 `reference.docx` 和 `namespace-reference-docx-styles.py` 保持样式 ID 稳定。
- 新增 Pandoc 样式时，同步维护 Lua filter 的 `styles` 表、`STYLE_ID_MAP` 和 `reference.docx`。
- 新增支持的 LaTeX 写法时，先确认 Pandoc AST 输出形态，再决定是否修改 Lua filter。
- 脚本行为发生变化后，优先用 `temp.tex` 中的图、表、公式、引用和参考文献示例做回归检查。
