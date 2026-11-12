# AGENTS.md

## 项目目标

本仓库维护适合论文初稿写作的轻量 LaTeX 模板，以及统一的 Pandoc 转 Word 审阅稿工具。它不是完整期刊投稿模板，最终投稿格式应在定稿阶段迁移。

- 论文模板与转换工具分离：用户复制 [template/](<template/>) 新建论文，不复制工具代码。
- LaTeX 保留论文语义、公式、图表、交叉引用和 BibTeX 管理。
- Word 便于导师和合作者审阅；初稿阶段避免复杂期刊排版宏。
- 转换器从调用方论文项目解析输入、图片、缓存和输出，不把工具仓库当成论文目录。

## 文档所有权

- 根目录 [README.md](<README.md>) 是英文公共入口，保持简洁。
- [README.cn.md](<docs/README.cn.md>) 是中文翻译，结构与英文入口同步。
- [TODO.md](<TODO.md>) 记录当前工作，非简单任务写明验收标准。
- [index.md](<docs/index.md>) 是技术文档索引。
- [technical-stack.md](<docs/technical-stack.md>) 保存模块职责、转换链路、样式和排错说明。
- `docs/archive/` 保留已完成或历史计划，不因当前路径调整重写历史记录。

## 常用入口

- 论文主文件：[temp.tex](<template/temp.tex>)。
- 参考文献：[reference.bib](<template/reference.bib>)。
- 图片：[fig/](<template/fig/>)。
- PDF 的 BibTeX 样式：[gbt7714.bst](<template/gbt7714.bst>)。
- 编辑器配置：[settings.json](<template/.vscode/settings.json>)。
- Linux 软链入口：[lpt-docx](<bin/lpt-docx>)。
- Windows 仓库入口：[lpt-docx.ps1](<bin/lpt-docx.ps1>)。
- Python 包入口：[cli.py](<src/lpt_docx/cli.py>)、[__main__.py](<src/lpt_docx/__main__.py>)。
- Pandoc filter：[latex-crossref-cn.lua](<src/lpt_docx/resources/latex-crossref-cn.lua>)。
- 论文 Word 样式：[样式模板](<template/reference.docx>)，随论文复制并允许独立修改。
- 后备 Word 样式：[包内模板](<src/lpt_docx/resources/reference.docx>)，用于没有自有样式的论文。
- 转换后的 Word 示例：[temp.docx](<examples/temp.docx>)。
- Word 参考文献样式：[gbt7714.csl](<src/lpt_docx/resources/gbt7714.csl>)。

## 文件边界

模板改动主要位于 [template/](<template/>)，只保存复制到论文项目后仍有用的源文件和配置。生成文档与转换工具不放入模板。主文件与目录重命名后，编译配方和资源相对路径仍应有效。

维护转换流程时修改：

- [cli.py](<src/lpt_docx/cli.py>)：参数、资源定位和流程编排。
- [prepare_pandoc_compat.py](<src/lpt_docx/prepare_pandoc_compat.py>)：兼容宏、子图宽度及分页标记。
- [prepare_pandoc_images.py](<src/lpt_docx/prepare_pandoc_images.py>)：PDF 图片预处理。
- [apply_docx_table_styles.py](<src/lpt_docx/apply_docx_table_styles.py>)：Word 表格与图片布局。
- [namespace_reference_docx_styles.py](<src/lpt_docx/namespace_reference_docx_styles.py>)：Word 样式与编号。
- `src/lpt_docx/resources/`：随包分发的非 Python 资源。
- `bin/`：只负责定位工具环境并调用统一包入口，不重复实现转换逻辑。

源码运行与安装包使用同一套包内资源，不增加依赖仓库外层文件的运行时回退。Word 样式按显式 `--reference-doc`、论文项目内样式、包内后备模板的顺序选择，只读输入样式，不将输出后处理写回模板。Bash 入口必须支持绝对和相对软链，并保留论文调用目录。

以下属于生成物或本地环境，通常不提交：

- 生成 PDF、DOCX 和 LaTeX 辅助文件。
- 论文项目的 `.pandoc-cache/`、工具的 `.venv/`、`dist/` 和 `__pycache__/`。

例外是包内后备 Word 样式、论文模板中的可编辑 Word 样式、模板图片目录中的原始 PDF 素材，以及明确保留供预览的 [Word 转换示例](<examples/temp.docx>)。其他生成稿仍忽略。仓库与复制后的论文分别使用 [.gitignore](<.gitignore>) 和 [模板忽略规则](<template/.gitignore>)。

原有本地 `refference/` 沿用既有拼写，不擅自改为 `reference/`；新模板不依赖该目录，旧论文仍可通过自己的图片路径使用它。

## 转换与验证

在工具仓库根目录准备依赖和运行现有测试：

```console
uv sync
uv run python -m unittest discover -s tests -v
uv build
```

完整 PDF 编译在复制后的论文目录中执行，不在工具仓库根目录执行：

```console
xelatex -interaction=nonstopmode temp.tex
bibtex temp
xelatex -interaction=nonstopmode temp.tex
xelatex -interaction=nonstopmode temp.tex
```

论文主文件重命名后，相应修改命令中的文件名和 BibTeX basename。已安装命令或配置好软链时，在论文目录执行：

```console
lpt-docx
lpt-docx manuscript.tex --output manuscript-review.docx
```

维护者在仓库根目录验证自带模板时，将输出放在缓存中：

```bash
./bin/lpt-docx template/temp.tex --output .pandoc-cache/check.docx
```

```powershell
.\bin\lpt-docx.ps1 template\temp.tex --output .pandoc-cache\check.docx
```

修改文档后至少执行 `git diff --check`。修改模板结构、转换模块、资源或入口时，检查现有测试及仓库外论文转换；入口变更应实际通过软链调用验证。验证副本放在临时目录，不把生成文件混入可复制模板。

直接检查 Pandoc AST 时，可以使用：

```console
pandoc template/temp.tex --lua-filter=src/lpt_docx/resources/latex-crossref-cn.lua -t native
```

需要兼容预处理的写法应通过完整转换链路核对；直接 Pandoc 调用不包含分页、单位等预处理步骤。

## Git 约定

- 只有用户明确要求时才提交；不要混入用户未授权的工作区改动。
- 使用中文 Conventional Commits：`<type>(<scope>): <subject>`。
- 常用类型：`docs`、`fix`、`feat`、`refactor`、`test`、`chore`。
- 非简单改动在提交正文中用独立 bullet 概括主要变化、验证方式和迁移说明。
- 不提交无关生成文件或缓存。
