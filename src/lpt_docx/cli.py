"""Command-line entry point for the LaTeX-to-DOCX conversion pipeline."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PACKAGE_ROOT = Path(__file__).resolve().parent
DEVELOPMENT_ROOT = Path(__file__).resolve().parents[2]
GRAPHICSPATH_RE = re.compile(
    r"\\graphicspath\s*\{((?:\s*\{[^{}]*\}\s*)+)\}",
    re.DOTALL,
)
GRAPHICSPATH_ENTRY_RE = re.compile(r"\{([^{}]*)\}")


class PipelineError(RuntimeError):
    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code if exit_code > 0 else 1


@dataclass(frozen=True)
class ToolResources:
    lua_filter: Path
    csl: Path
    reference_doc: Path
    compat_script: Path
    image_script: Path
    table_style_script: Path
    style_normalizer_script: Path


@dataclass(frozen=True)
class ProjectPaths:
    invocation_dir: Path
    input_file: Path
    output_file: Path
    project_root: Path
    bibliographies: tuple[Path, ...]
    csl: Path
    reference_doc: Path
    cache_dir: Path
    resource_dirs: tuple[Path, ...]


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lpt-docx",
        description="Convert a LaTeX manuscript to a styled Word review draft.",
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        type=Path,
        help="Main TeX file. Defaults to ./temp.tex.",
    )
    parser.add_argument(
        "--input",
        dest="input_option",
        type=Path,
        help="Backward-compatible form of the input path.",
    )
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Base directory for manuscript resources. Defaults to the input directory.",
    )
    parser.add_argument(
        "--bibliography",
        action="append",
        type=Path,
        help="BibTeX database. Repeat for multiple files; defaults to PROJECT/reference.bib.",
    )
    parser.add_argument(
        "--resource-dir",
        action="append",
        default=[],
        type=Path,
        help="Additional Pandoc resource directory. May be repeated.",
    )
    parser.add_argument("--csl", type=Path, help="Override the bundled CSL file.")
    parser.add_argument(
        "--reference-doc",
        type=Path,
        help="Override the bundled Word reference document.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Cache directory. Defaults to PROJECT/.pandoc-cache.",
    )
    parser.add_argument("--image-dpi", type=positive_int, default=300)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.input_path is not None and args.input_option is not None:
        parser.error("specify the input either positionally or with --input, not both")
    args.input = args.input_option or args.input_path or Path("temp.tex")
    del args.input_path
    del args.input_option
    return args


def resolve_cli_path(path: Path, invocation_dir: Path) -> Path:
    return path.resolve() if path.is_absolute() else (invocation_dir / path).resolve()


def unique_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = path.resolve()
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            result.append(resolved)
    return tuple(result)


def bundled_path(packaged_relative: str, development_relative: str) -> Path:
    packaged = PACKAGE_ROOT / "resources" / packaged_relative
    if packaged.is_file():
        return packaged
    return DEVELOPMENT_ROOT / development_relative


def load_tool_resources() -> ToolResources:
    return ToolResources(
        lua_filter=bundled_path("latex-crossref-cn.lua", "filters/latex-crossref-cn.lua"),
        csl=bundled_path("gbt7714.csl", "gbt7714.csl"),
        reference_doc=bundled_path("reference.docx", "reference.docx"),
        compat_script=bundled_path(
            "scripts/prepare-pandoc-compat.py",
            "scripts/prepare-pandoc-compat.py",
        ),
        image_script=bundled_path(
            "scripts/prepare-pandoc-images.py",
            "scripts/prepare-pandoc-images.py",
        ),
        table_style_script=bundled_path(
            "scripts/apply-docx-table-styles.py",
            "scripts/apply-docx-table-styles.py",
        ),
        style_normalizer_script=bundled_path(
            "scripts/namespace-reference-docx-styles.py",
            "scripts/namespace-reference-docx-styles.py",
        ),
    )


def resolve_project_paths(
    args: argparse.Namespace,
    resources: ToolResources,
    invocation_dir: Path | None = None,
) -> ProjectPaths:
    invocation_dir = (invocation_dir or Path.cwd()).resolve()
    input_file = resolve_cli_path(args.input, invocation_dir)
    project_root = (
        resolve_cli_path(args.project_root, invocation_dir)
        if args.project_root is not None
        else input_file.parent
    )
    output_file = (
        resolve_cli_path(args.output, invocation_dir)
        if args.output is not None
        else input_file.with_suffix(".docx")
    )
    bibliography_args = args.bibliography or [project_root / "reference.bib"]
    bibliographies = tuple(
        resolve_cli_path(path, invocation_dir) if not path.is_absolute() else path.resolve()
        for path in bibliography_args
    )
    csl = (
        resolve_cli_path(args.csl, invocation_dir)
        if args.csl is not None
        else resources.csl
    )
    reference_doc = (
        resolve_cli_path(args.reference_doc, invocation_dir)
        if args.reference_doc is not None
        else resources.reference_doc
    )
    cache_dir = (
        resolve_cli_path(args.cache_dir, invocation_dir)
        if args.cache_dir is not None
        else project_root / ".pandoc-cache"
    )
    resource_dirs = unique_paths(
        [resolve_cli_path(path, invocation_dir) for path in args.resource_dir]
    )
    return ProjectPaths(
        invocation_dir=invocation_dir,
        input_file=input_file,
        output_file=output_file,
        project_root=project_root.resolve(),
        bibliographies=bibliographies,
        csl=csl.resolve(),
        reference_doc=reference_doc.resolve(),
        cache_dir=cache_dir.resolve(),
        resource_dirs=resource_dirs,
    )


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise PipelineError(f"{label} does not exist: {path}")


def require_directory(path: Path, label: str) -> None:
    if not path.is_dir():
        raise PipelineError(f"{label} does not exist or is not a directory: {path}")


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(f"{label}...", flush=True)
    try:
        result = subprocess.run(command, check=False, cwd=cwd)
    except OSError as exc:
        raise PipelineError(f"{label} could not start: {exc}") from exc
    if result.returncode != 0:
        raise PipelineError(
            f"{label} failed with exit code {result.returncode}",
            result.returncode,
        )


def graphicspath_entries(tex_text: str) -> list[str]:
    entries: list[str] = []
    for match in GRAPHICSPATH_RE.finditer(tex_text):
        for entry in GRAPHICSPATH_ENTRY_RE.findall(match.group(1)):
            cleaned = entry.strip().replace("\\", "/")
            if cleaned:
                entries.append(cleaned)
    return entries


def pandoc_resource_dirs(
    tex_text: str,
    paths: ProjectPaths,
    image_cache: Path,
    equation_cache: Path,
) -> tuple[Path, ...]:
    graphicspaths = []
    for entry in graphicspath_entries(tex_text):
        path = Path(entry)
        graphicspaths.append(
            path.resolve() if path.is_absolute() else (paths.project_root / path).resolve()
        )
    candidates = unique_paths(
        [
            paths.input_file.parent,
            paths.project_root,
            paths.project_root / "fig",
            paths.project_root / "refference" / "fig",
            *graphicspaths,
            *paths.resource_dirs,
            image_cache,
            equation_cache,
        ]
    )
    return tuple(path for path in candidates if path.is_dir())


def cache_key(input_file: Path) -> str:
    digest = hashlib.sha1(str(input_file.resolve()).encode("utf-8")).hexdigest()[:10]
    return f"{input_file.stem}-{digest}"


def convert(
    args: argparse.Namespace,
    tool_resources: ToolResources | None = None,
) -> Path:
    resources = tool_resources or load_tool_resources()
    paths = resolve_project_paths(args, resources)

    require_directory(paths.project_root, "Project root")
    require_file(paths.input_file, "Input TeX file")
    for bibliography in paths.bibliographies:
        require_file(bibliography, "Bibliography")
    for resource_dir in paths.resource_dirs:
        require_directory(resource_dir, "Resource directory")
    for path, label in (
        (paths.csl, "CSL file"),
        (paths.reference_doc, "Reference DOCX"),
        (resources.lua_filter, "Pandoc Lua filter"),
        (resources.compat_script, "Compatibility preprocessor"),
        (resources.image_script, "Image preprocessor"),
        (resources.table_style_script, "DOCX table postprocessor"),
        (resources.style_normalizer_script, "DOCX style normalizer"),
    ):
        require_file(path, label)

    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise PipelineError("Pandoc was not found on PATH.")

    paths.cache_dir.mkdir(parents=True, exist_ok=True)
    image_cache = paths.cache_dir / "images"
    equation_cache = paths.cache_dir / "equations"
    run_cache = paths.cache_dir / "runs"
    run_cache.mkdir(parents=True, exist_ok=True)
    source_text = paths.input_file.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(
        dir=run_cache,
        prefix=f"{cache_key(paths.input_file)}-",
    ) as run_dir_text:
        run_dir = Path(run_dir_text)
        compat_input = run_dir / "compat.tex"
        pandoc_input = run_dir / "pandoc.tex"

        run_step(
            "Preparing LaTeX compatibility input for Pandoc",
            [
                sys.executable,
                str(resources.compat_script),
                "--input",
                str(paths.input_file),
                "--output",
                str(compat_input),
                "--equation-cache-dir",
                str(equation_cache),
            ],
            cwd=paths.project_root,
        )
        run_step(
            "Preparing images for Pandoc",
            [
                sys.executable,
                str(resources.image_script),
                "--input",
                str(compat_input),
                "--output",
                str(pandoc_input),
                "--cache-dir",
                str(image_cache),
                "--base-dir",
                str(paths.project_root),
                "--source-dir",
                str(paths.input_file.parent),
                "--dpi",
                str(args.image_dpi),
            ],
            cwd=paths.project_root,
        )

        paths.output_file.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            delete=False,
            dir=paths.output_file.parent,
            prefix=f".{paths.output_file.stem}-",
            suffix=".docx",
        ) as temp_file:
            temp_output = Path(temp_file.name)
        try:
            resource_path = os.pathsep.join(
                str(path)
                for path in pandoc_resource_dirs(
                    source_text,
                    paths,
                    image_cache,
                    equation_cache,
                )
            )
            pandoc_command = [
                pandoc,
                str(pandoc_input),
                "-o",
                str(temp_output),
                "--citeproc",
                f"--lua-filter={resources.lua_filter}",
                *(f"--bibliography={path}" for path in paths.bibliographies),
                f"--csl={paths.csl}",
                f"--resource-path={resource_path}",
                f"--reference-doc={paths.reference_doc}",
            ]
            run_step("Running Pandoc", pandoc_command, cwd=paths.project_root)
            run_step(
                "Applying Word table styles",
                [sys.executable, str(resources.table_style_script), str(temp_output)],
                cwd=paths.project_root,
            )
            run_step(
                "Normalizing Word styles",
                [sys.executable, str(resources.style_normalizer_script), str(temp_output)],
                cwd=paths.project_root,
            )
            os.replace(temp_output, paths.output_file)
        finally:
            if temp_output.exists():
                temp_output.unlink()

    print(f"Wrote {paths.output_file}")
    return paths.output_file


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        convert(args)
    except PipelineError as exc:
        print(f"lpt-docx: {exc}", file=sys.stderr)
        return exc.exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
