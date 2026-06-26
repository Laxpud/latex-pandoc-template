#!/usr/bin/env python
"""为 Pandoc 转换准备 LaTeX 兼容输入。

这个脚本只覆盖当前模板需要的窄子集：常用 glossary 宏、常用
siunitx 宏、`\bm`，以及带 `eq:` 标签的编号公式 SVG 化。它不是
完整 LaTeX 解释器，遇到超出约定的复杂宏时会尽量保持原文。
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class Acronym:
    key: str
    short: str
    long: str


@dataclass
class Symbol:
    key: str
    value: str
    description: str


@dataclass
class Equation:
    label: str
    latex: str


@dataclass
class PrepareResult:
    text: str
    equations_rendered: int


NEWACRONYM_RE = re.compile(r"\\newacronym\b")
NEWSYMBOL_RE = re.compile(r"\\glsxtrnewsymbol\b")
PRINT_GLOSSARY_RE = re.compile(r"\\printunsrtglossary\s*(\[[^\]]*\])?")
EQUATION_RE = re.compile(
    r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}",
    re.DOTALL,
)
LABEL_RE = re.compile(r"\\label\s*\{\s*([^}]+)\s*\}")
DEGREE_SIGN = "\N{DEGREE SIGN}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Expand a small compatibility subset before Pandoc conversion."
    )
    parser.add_argument("--input", required=True, help="Source TeX file.")
    parser.add_argument("--output", required=True, help="Preprocessed TeX file.")
    parser.add_argument(
        "--equation-cache-dir",
        required=True,
        help="Directory for generated SVG equation assets.",
    )
    return parser.parse_args()


def read_group(text: str, start: int, open_char: str = "{", close_char: str = "}") -> tuple[str, int] | None:
    """读取一个支持嵌套括号的 LaTeX 参数组。

    `start` 必须指向左括号。返回参数内容和右括号后一位索引。
    """

    if start >= len(text) or text[start] != open_char:
        return None

    depth = 0
    content_start = start + 1
    i = start
    while i < len(text):
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return text[content_start:i], i + 1
        i += 1

    return None


def skip_space(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def read_optional_group(text: str, index: int) -> tuple[str, int]:
    index = skip_space(text, index)
    if index < len(text) and text[index] == "[":
        result = read_group(text, index, "[", "]")
        if result:
            return result
    return "", index


def read_required_groups(text: str, index: int, count: int) -> tuple[list[str], int] | None:
    groups: list[str] = []
    cursor = index
    for _ in range(count):
        cursor = skip_space(text, cursor)
        result = read_group(text, cursor)
        if not result:
            return None
        value, cursor = result
        groups.append(value)
    return groups, cursor


def latex_to_plain(text: str) -> str:
    """把宏定义里的简单 LaTeX 内容降级为适合 Word 审阅稿的文本。"""

    text = expand_siunitx(text)
    text = replace_command_groups(text, "ensuremath", 1, lambda args: args[0])
    text = replace_command_groups(text, "mathrm", 1, lambda args: args[0])
    text = replace_command_groups(text, "text", 1, lambda args: args[0])
    text = text.replace(r"\degree", DEGREE_SIGN)
    text = text.replace(r"\Omega", "Ω")
    text = text.replace(r"\beta", "β")
    text = text.replace(r"\_", "_")
    text = text.replace("$", "")
    text = re.sub(r"\\[,;:! ]", " ", text)
    text = re.sub(r"\\[A-Za-z]+", "", text)
    text = text.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", text).strip()


def parse_description(options: str) -> str:
    match = re.search(r"description\s*=\s*\{", options)
    if not match:
        return ""
    result = read_group(options, match.end() - 1)
    return latex_to_plain(result[0]) if result else ""


def collect_glossary_definitions(tex_text: str) -> tuple[dict[str, Acronym], dict[str, Symbol]]:
    acronyms: dict[str, Acronym] = {}
    symbols: dict[str, Symbol] = {}

    for match in NEWACRONYM_RE.finditer(tex_text):
        parsed = read_required_groups(tex_text, match.end(), 3)
        if not parsed:
            continue
        groups, _ = parsed
        key, short, long = groups
        acronyms[key] = Acronym(key=key, short=latex_to_plain(short), long=latex_to_plain(long))

    for match in NEWSYMBOL_RE.finditer(tex_text):
        options, cursor = read_optional_group(tex_text, match.end())
        parsed = read_required_groups(tex_text, cursor, 2)
        if not parsed:
            continue
        groups, _ = parsed
        key, value = groups
        symbols[key] = Symbol(
            key=key,
            value=latex_to_plain(value),
            description=parse_description(options),
        )

    return acronyms, symbols


def strip_glossary_definitions(tex_text: str) -> str:
    """删除已被预处理展开的 glossary 定义，避免 Pandoc 看到残留宏。"""

    ranges: list[tuple[int, int]] = []

    for match in NEWACRONYM_RE.finditer(tex_text):
        parsed = read_required_groups(tex_text, match.end(), 3)
        if parsed:
            _, end = parsed
            ranges.append((match.start(), end))

    for match in NEWSYMBOL_RE.finditer(tex_text):
        _, cursor = read_optional_group(tex_text, match.end())
        parsed = read_required_groups(tex_text, cursor, 2)
        if parsed:
            _, end = parsed
            ranges.append((match.start(), end))

    if not ranges:
        return tex_text

    output: list[str] = []
    cursor = 0
    for start, end in sorted(ranges):
        output.append(tex_text[cursor:start])
        cursor = end
    output.append(tex_text[cursor:])
    return "".join(output)


def replace_command_groups(
    text: str,
    command: str,
    group_count: int,
    replacement: Callable[[list[str]], str],
) -> str:
    pattern = re.compile(r"\\" + re.escape(command) + r"\b")
    output: list[str] = []
    cursor = 0

    for match in pattern.finditer(text):
        parsed = read_required_groups(text, match.end(), group_count)
        if not parsed:
            continue
        groups, end = parsed
        output.append(text[cursor : match.start()])
        output.append(replacement(groups))
        cursor = end

    output.append(text[cursor:])
    return "".join(output)


def unit_text(unit: str) -> str:
    unit = latex_to_plain(unit)
    replacements = {
        "degree": DEGREE_SIGN,
        "degrees": DEGREE_SIGN,
        "Hz": "Hz",
        "dB": "dB",
        "m": "m",
        "mm": "mm",
        "kW": "kW",
    }
    return replacements.get(unit, unit)


def expand_siunitx(text: str) -> str:
    text = replace_command_groups(
        text,
        "SIrange",
        3,
        lambda args: f"{latex_to_plain(args[0])}--{latex_to_plain(args[1])} {unit_text(args[2])}",
    )
    text = replace_command_groups(
        text,
        "SI",
        2,
        lambda args: f"{latex_to_plain(args[0])} {unit_text(args[1])}",
    )
    text = replace_command_groups(text, "ang", 1, lambda args: f"{latex_to_plain(args[0])}{DEGREE_SIGN}")

    # 兼容少量历史误写：`\si{300}{degree}` 也降级成 `300 °`。
    text = replace_command_groups(
        text,
        "si",
        2,
        lambda args: f"{latex_to_plain(args[0])} {unit_text(args[1])}",
    )
    text = replace_command_groups(text, "si", 1, lambda args: unit_text(args[0]))
    return text


def expand_glossaries(text: str, acronyms: dict[str, Acronym], symbols: dict[str, Symbol]) -> str:
    def singular(args: list[str]) -> str:
        key = args[0]
        if key in acronyms:
            return acronyms[key].short
        if key in symbols:
            return symbols[key].value
        return key

    def plural(args: list[str]) -> str:
        key = args[0]
        if key in acronyms:
            return acronyms[key].short + "s"
        if key in symbols:
            return symbols[key].value
        return key + "s"

    text = replace_command_groups(text, "glspl", 1, plural)
    text = replace_command_groups(text, "gls", 1, singular)
    return text


def latex_table_cell(text: str) -> str:
    """转义 glossary 表格单元格中会打断 LaTeX `tabular` 的字符。

    预处理已经把常见宏降级为纯文本，这里只处理表格语法敏感字符。
    这样生成的 `tabular` 既能被 Pandoc 识别为 Word 表格，也不会把
    glossary 的内部 key 泄漏到审阅稿中。
    """

    return text.replace("\\", r"\textbackslash{} ").replace("&", r"\&").replace("%", r"\%")


def glossary_table(rows: list[tuple[str, str]]) -> str:
    """生成 Pandoc LaTeX reader 易识别的两列表格。"""

    if not rows:
        return ""
    lines = [r"\begin{tabular}{ll}"]
    for left, right in rows:
        lines.append(rf"\textbf{{{latex_table_cell(left)}}} & {latex_table_cell(right)} \\")
    lines.append(r"\end{tabular}")
    return "\n".join(lines)


def glossary_replacement(kind: str, acronyms: dict[str, Acronym], symbols: dict[str, Symbol]) -> str:
    """把 glossary 打平成普通 Word 表格，避免项目符号和悬挂缩进。

    这里不复刻 glossaries-extra 的正式符号表版式，只保留“符号/缩略语 +
    说明”的审阅信息。内部 key 只用于正文 `\\gls{key}` 查表，不应出现在
    Word 正文里，否则会把实现细节暴露给读者。
    """

    if kind == "symbols":
        return glossary_table(
            [(item.value, item.description) for item in symbols.values()]
        )

    if kind == "acronym":
        return glossary_table(
            [(item.short, item.long) for item in acronyms.values()]
        )

    return ""


def expand_print_glossary(text: str, acronyms: dict[str, Acronym], symbols: dict[str, Symbol]) -> str:
    def repl(match: re.Match[str]) -> str:
        options = match.group(1) or ""
        kind_match = re.search(r"type\s*=\s*([A-Za-z]+)", options)
        kind = kind_match.group(1) if kind_match else ""
        return glossary_replacement(kind, acronyms, symbols)

    return PRINT_GLOSSARY_RE.sub(repl, text)


def replace_bm(text: str) -> str:
    return replace_command_groups(text, "bm", 1, lambda args: rf"\boldsymbol{{{args[0]}}}")


def clean_equation_latex(equation_body: str) -> tuple[str, str | None]:
    label_match = LABEL_RE.search(equation_body)
    label = label_match.group(1).strip() if label_match else None
    cleaned = LABEL_RE.sub("", equation_body)
    cleaned_lines = [line for line in cleaned.splitlines() if line.strip()]
    return "\n".join(cleaned_lines).strip(), label


def cache_stem(equation_latex: str) -> str:
    digest = hashlib.sha1(equation_latex.encode("utf-8")).hexdigest()[:12]
    return f"eq-{digest}"


def standalone_equation_source(equation_latex: str) -> str:
    return "\n".join(
        [
            r"\documentclass[border=2pt]{standalone}",
            r"\usepackage{amsmath}",
            r"\usepackage{amssymb}",
            r"\usepackage{bm}",
            r"\begin{document}",
            r"\(\displaystyle",
            equation_latex,
            r"\)",
            r"\end{document}",
            "",
        ]
    )


def render_equation_svg(equation: Equation, cache_dir: Path) -> Path:
    """把单个公式渲染为 SVG，并在缓存目录保存源 LaTeX 侧车文件。"""

    cache_dir.mkdir(parents=True, exist_ok=True)
    stem = cache_stem(equation.latex)
    svg_path = cache_dir / f"{stem}.svg"
    source_path = cache_dir / f"{stem}.tex"

    source_text = standalone_equation_source(equation.latex)
    if svg_path.exists() and source_path.exists() and source_path.read_text(encoding="utf-8") == source_text:
        return svg_path

    source_path.write_text(source_text, encoding="utf-8", newline="\n")
    build_dir = cache_dir / f"{stem}-build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)
    build_tex = build_dir / "equation.tex"
    build_tex.write_text(source_text, encoding="utf-8", newline="\n")

    latex_cmd = [
        "latex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "equation.tex",
    ]
    subprocess.run(latex_cmd, check=True, cwd=build_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    dvi_path = build_dir / "equation.dvi"
    dvisvgm_cmd = [
        "dvisvgm",
        "--no-fonts",
        "--exact",
        f"--output={svg_path.resolve()}",
        str(dvi_path.resolve()),
    ]
    subprocess.run(dvisvgm_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return svg_path


def image_path_for_tex(path: Path, input_dir: Path) -> str:
    try:
        return path.resolve().relative_to(input_dir.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def equation_image_block(equation: Equation, svg_path: Path, input_dir: Path) -> str:
    source_note = f"LaTeX equation source: {svg_path.with_suffix('.tex').name}"
    target = image_path_for_tex(svg_path, input_dir)
    return "\n".join(
        [
            rf"\hypertarget{{{equation.label}}}{{\includegraphics[width=0.9\linewidth,alt={{{source_note}}}]{{{target}}}}}",
            "",
        ]
    )


def rewrite_labeled_equations(
    text: str,
    input_dir: Path,
    equation_cache_dir: Path,
    render_equation_svg_func: Callable[[Equation, Path], Path],
) -> tuple[str, int]:
    rendered_count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal rendered_count
        equation_latex, label = clean_equation_latex(match.group(1))
        if not label:
            return match.group(0)
        equation = Equation(label=label, latex=equation_latex)
        svg_path = render_equation_svg_func(equation, equation_cache_dir)
        rendered_count += 1
        return equation_image_block(equation, svg_path, input_dir)

    return EQUATION_RE.sub(repl, text), rendered_count


def prepare_tex_text(
    tex_text: str,
    input_dir: Path,
    equation_cache_dir: Path,
    render_equation_svg: Callable[[Equation, Path], Path] = render_equation_svg,
) -> PrepareResult:
    acronyms, symbols = collect_glossary_definitions(tex_text)
    text = strip_glossary_definitions(tex_text)
    text = expand_print_glossary(text, acronyms, symbols)
    text = expand_glossaries(text, acronyms, symbols)
    text = expand_siunitx(text)
    text = replace_bm(text)
    rendered_count = 0
    # 暂时关闭编号公式 SVG 化，回退到 Pandoc/Word 原生公式路径，便于比较
    # SVG 图片基线和公式编号纵向对齐问题。恢复 SVG 路径时取消下面几行注释。
    # text, rendered_count = rewrite_labeled_equations(
    #     text,
    #     input_dir=input_dir,
    #     equation_cache_dir=equation_cache_dir,
    #     render_equation_svg_func=render_equation_svg,
    # )
    return PrepareResult(text=text, equations_rendered=rendered_count)


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    equation_cache_dir = Path(args.equation_cache_dir)

    if not input_path.exists():
        raise SystemExit(f"Input TeX file does not exist: {input_path}")

    result = prepare_tex_text(
        input_path.read_text(encoding="utf-8"),
        input_dir=input_path.resolve().parent,
        equation_cache_dir=equation_cache_dir,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.text, encoding="utf-8", newline="")
    print(f"Prepared compatibility input: {output_path}")
    print(f"Rendered {result.equations_rendered} equation SVG(s): {equation_cache_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
