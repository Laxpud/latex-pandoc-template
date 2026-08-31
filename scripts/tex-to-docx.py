#!/usr/bin/env python
"""Run the repository's cross-platform LaTeX-to-DOCX conversion pipeline."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent


class PipelineError(RuntimeError):
    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code if exit_code > 0 else 1


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a LaTeX manuscript to a styled Word review draft."
    )
    parser.add_argument("--input", type=Path, default=ROOT / "temp.tex")
    parser.add_argument("--output", type=Path, default=ROOT / "temp.docx")
    parser.add_argument(
        "--bibliography",
        type=Path,
        default=ROOT / "reference.bib",
    )
    parser.add_argument("--csl", type=Path, default=ROOT / "gbt7714.csl")
    parser.add_argument(
        "--reference-doc",
        type=Path,
        default=ROOT / "reference.docx",
    )
    parser.add_argument("--image-dpi", type=positive_int, default=300)
    return parser.parse_args()


def resolve_cli_path(path: Path, invocation_dir: Path) -> Path:
    return path.resolve() if path.is_absolute() else (invocation_dir / path).resolve()


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise PipelineError(f"{label} does not exist: {path}")


def run_step(label: str, command: list[str]) -> None:
    print(f"{label}...", flush=True)
    try:
        result = subprocess.run(command, check=False)
    except OSError as exc:
        raise PipelineError(f"{label} could not start: {exc}") from exc
    if result.returncode != 0:
        raise PipelineError(
            f"{label} failed with exit code {result.returncode}",
            result.returncode,
        )


def convert(args: argparse.Namespace) -> Path:
    invocation_dir = Path.cwd()
    input_file = resolve_cli_path(args.input, invocation_dir)
    output_file = resolve_cli_path(args.output, invocation_dir)
    bibliography = resolve_cli_path(args.bibliography, invocation_dir)
    csl = resolve_cli_path(args.csl, invocation_dir)
    reference_doc = resolve_cli_path(args.reference_doc, invocation_dir)

    lua_filter = ROOT / "filters" / "latex-crossref-cn.lua"
    compat_script = SCRIPT_DIR / "prepare-pandoc-compat.py"
    image_script = SCRIPT_DIR / "prepare-pandoc-images.py"
    table_style_script = SCRIPT_DIR / "apply-docx-table-styles.py"
    style_normalizer_script = SCRIPT_DIR / "namespace-reference-docx-styles.py"
    for path, label in (
        (input_file, "Input TeX file"),
        (bibliography, "Bibliography"),
        (csl, "CSL file"),
        (reference_doc, "Reference DOCX"),
        (lua_filter, "Pandoc Lua filter"),
        (compat_script, "Compatibility preprocessor"),
        (image_script, "Image preprocessor"),
        (table_style_script, "DOCX table postprocessor"),
        (style_normalizer_script, "DOCX style normalizer"),
    ):
        require_file(path, label)

    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise PipelineError("Pandoc was not found on PATH.")

    cache_dir = ROOT / ".pandoc-cache"
    image_cache = cache_dir / "images"
    compat_cache = cache_dir / "compat"
    equation_cache = cache_dir / "equations"
    compat_input = compat_cache / "temp-compat.tex"
    pandoc_input = cache_dir / "temp-pandoc.tex"

    run_step(
        "Preparing LaTeX compatibility input for Pandoc",
        [
            sys.executable,
            str(compat_script),
            "--input",
            str(input_file),
            "--output",
            str(compat_input),
            "--equation-cache-dir",
            str(equation_cache),
        ],
    )
    run_step(
        "Preparing images for Pandoc",
        [
            sys.executable,
            str(image_script),
            "--input",
            str(compat_input),
            "--output",
            str(pandoc_input),
            "--cache-dir",
            str(image_cache),
            "--base-dir",
            str(ROOT),
            "--dpi",
            str(args.image_dpi),
        ],
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        delete=False,
        dir=output_file.parent,
        prefix=f".{output_file.stem}-",
        suffix=".docx",
    ) as temp_file:
        temp_output = Path(temp_file.name)
    try:
        resource_path = os.pathsep.join(
            str(path)
            for path in (
                ROOT,
                ROOT / "fig",
                ROOT / "refference" / "fig",
                image_cache,
                equation_cache,
            )
        )
        run_step(
            "Running Pandoc",
            [
                pandoc,
                str(pandoc_input),
                "-o",
                str(temp_output),
                "--citeproc",
                f"--lua-filter={lua_filter}",
                f"--bibliography={bibliography}",
                f"--csl={csl}",
                f"--resource-path={resource_path}",
                f"--reference-doc={reference_doc}",
            ],
        )
        run_step(
            "Applying Word table styles",
            [sys.executable, str(table_style_script), str(temp_output)],
        )
        run_step(
            "Normalizing Word styles",
            [sys.executable, str(style_normalizer_script), str(temp_output)],
        )
        os.replace(temp_output, output_file)
    finally:
        if temp_output.exists():
            temp_output.unlink()

    print(f"Wrote {output_file}")
    return output_file


def main() -> int:
    args = parse_args()
    try:
        convert(args)
    except PipelineError as exc:
        print(f"tex-to-docx: {exc}", file=sys.stderr)
        return exc.exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
