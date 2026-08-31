# TODO

本文档只记录当前仍需要推进的项目工作。已经稳定下来的使用说明放在 `README.md` / `docs/README.cn.md`，技术细节放在 `docs/technical-stack.md`。

## 文档结构维护

- [x] 完成一次新文档结构的链接巡检。
  - 验收标准：根 README、`docs/README.cn.md`、`docs/index.md` 和 `AGENTS.md` 中不再出现旧的 `doc` 目录路径；公共入口不链接目录级 README。
- [ ] 按实际使用反馈精简或扩展 `docs/technical-stack.md`。
  - 验收标准：转换链路、兼容预处理、Word 样式系统和排错说明与当前脚本行为一致。

## 转换兼容层

- [x] 将 Word 转换工具重构为可安装的 Python 包。
  - 验收标准：安装后可从任意目录运行 `lpt-docx`；工具内置 Lua filter、CSL 和 Word 样式模板；输入、参考文献、图片、缓存和输出路径都按论文项目解析；保留 PowerShell 与 Bash 兼容入口；Windows 和 Ubuntu 测试覆盖包安装及仓库外转换。
- [x] 提供 Windows 和 Linux 共用的 Python Word 转换核心。
  - 验收标准：PowerShell 与 Bash 根入口调用同一 Python 核心；Linux 不安装 PowerShell 也能生成有效 DOCX；Windows 和 Ubuntu CI 均运行完整测试及各自入口。
- [ ] 定稿编号公式转换策略。
  - 验收标准：在 SVG 图片公式和 Pandoc 与 Word 原生 OMML 公式之间选定默认路径，并用 `temp.tex` 示例验证公式居中、编号对齐和交叉引用。
- [ ] 用一篇真实论文做完整转换回归。
  - 验收标准：不复制真实论文内容进模板仓库；只把发现的通用兼容问题转化为 `temp.tex` 示例、脚本测试或技术文档说明。
- [ ] 评估是否需要 SVG 的 PNG fallback。
  - 验收标准：明确是否要求旧版 Word 兼容；若需要，则补充 `rsvg-convert` 依赖说明或脚本 fallback。
- [x] 修复图片转换后承载表格边框未隐藏的问题。
  - 验收标准：`temp.docx` 中由图片、题注或图片布局辅助结构生成的表格不显示可见边框，同时不影响正文表格的边框样式。
- [x] 让 DOCX 子图按 LaTeX 声明宽度自动换行。
  - 验收标准：四个 `0.48\linewidth` 子图转换为一个两行两列的无边框图片布局表，图片尺寸、`(a)` 至 `(d)` 子图题编号及项目样式保持正确。
- [x] 补齐 `\item` 列表命令对应的 Word 样式。
  - 验收标准：`itemize`、`enumerate` 等 LaTeX 列表转换后使用稳定的 Word 列表样式，编号、缩进、换行和多级列表表现符合审阅稿预期。
