#!/usr/bin/env python
"""Prepare LaTeX image references for Pandoc Word conversion.

The source manuscript can keep PDF vector figures for LaTeX output. This helper
renders referenced PDF figures to PNG for Pandoc's DOCX writer and writes a
temporary TeX file that points to those cached PNG files.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
import sys
from pathlib import Path

try:
    import fitz
except ImportError as exc:  # pragma: no cover - exercised by missing env
    raise SystemExit(
        "Missing dependency: PyMuPDF. Run `uv sync` in the repository root first."
    ) from exc


GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\s*\{[^{}]*\}\s*)+)\}", re.DOTALL)
GRAPHICSPATH_ENTRY_RE = re.compile(r"\{([^{}]*)\}")
INCLUDEGRAPHICS_RE = re.compile(
    r"(\\includegraphics(?:\s*\[[^\]]*\])?\s*\{)([^{}]+)(\})",
    re.DOTALL,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render PDF figures to cached PNGs and rewrite a temporary TeX file for Pandoc."
    )
    parser.add_argument("--input", required=True, help="Source TeX file.")
    parser.add_argument("--output", required=True, help="Temporary TeX file to write.")
    parser.add_argument("--cache-dir", required=True, help="Directory for generated PNG images.")
    parser.add_argument("--dpi", type=int, default=300, help="Rasterization DPI. Default: 300.")
    return parser.parse_args()


def normalize_tex_path(path_text: str) -> str:
    return path_text.strip().replace("\\", "/")


def graphicspath_entries(tex_text: str) -> list[str]:
    entries: list[str] = []
    for match in GRAPHICSPATH_RE.finditer(tex_text):
        for entry in GRAPHICSPATH_ENTRY_RE.findall(match.group(1)):
            cleaned = normalize_tex_path(entry)
            if cleaned:
                entries.append(cleaned)
    return entries


def candidate_paths(image_ref: str, tex_dir: Path, search_dirs: list[Path]) -> list[Path]:
    ref = Path(normalize_tex_path(image_ref))
    refs = [ref]
    if ref.suffix == "":
        refs.append(ref.with_suffix(".pdf"))

    candidates: list[Path] = []
    for item in refs:
        if item.is_absolute():
            candidates.append(item)
        else:
            candidates.append(tex_dir / item)
            for search_dir in search_dirs:
                candidates.append(search_dir / item)
    return candidates


def resolve_pdf(image_ref: str, tex_dir: Path, search_dirs: list[Path]) -> Path:
    searched = candidate_paths(image_ref, tex_dir, search_dirs)
    for path in searched:
        if path.exists() and path.is_file():
            return path.resolve()

    searched_text = "\n  - ".join(str(path) for path in searched)
    raise FileNotFoundError(
        f"Cannot find PDF image `{image_ref}`. Searched:\n  - {searched_text}"
    )


def cache_name(pdf_path: Path, dpi: int) -> str:
    digest = hashlib.sha1(str(pdf_path).encode("utf-8")).hexdigest()[:10]
    return f"{pdf_path.stem}-{digest}-{dpi}dpi.png"


def png_dpi(path: Path) -> tuple[int, int] | None:
    """Read PNG pHYs density metadata, rounded to DPI."""
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None

    offset = 8
    while offset + 8 <= len(data):
        chunk_len = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data_start = offset + 8
        chunk_data_end = chunk_data_start + chunk_len
        if chunk_data_end + 4 > len(data):
            return None
        if chunk_type == b"pHYs":
            chunk_data = data[chunk_data_start:chunk_data_end]
            if len(chunk_data) != 9 or chunk_data[8] != 1:
                return None
            x_ppm = struct.unpack(">I", chunk_data[0:4])[0]
            y_ppm = struct.unpack(">I", chunk_data[4:8])[0]
            return round(x_ppm * 0.0254), round(y_ppm * 0.0254)
        offset = chunk_data_end + 4

    return None


def cached_png_is_current(pdf_path: Path, output_png: Path, dpi: int) -> bool:
    if not output_png.exists():
        return False
    if output_png.stat().st_mtime < pdf_path.stat().st_mtime:
        return False
    return png_dpi(output_png) == (dpi, dpi)


def render_first_page(pdf_path: Path, output_png: Path, dpi: int) -> None:
    output_png.parent.mkdir(parents=True, exist_ok=True)
    if cached_png_is_current(pdf_path, output_png, dpi):
        return

    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    with fitz.open(pdf_path) as doc:
        if doc.page_count == 0:
            raise ValueError(f"PDF image has no pages: {pdf_path}")
        page = doc.load_page(0)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        pixmap.set_dpi(dpi, dpi)
        pixmap.save(output_png)


def tex_relative_path(path: Path, base_dir: Path) -> str:
    try:
        relative = path.resolve().relative_to(base_dir.resolve())
        return relative.as_posix()
    except ValueError:
        return path.resolve().as_posix()


def prepare_tex(input_tex: Path, output_tex: Path, cache_dir: Path, dpi: int) -> int:
    tex_dir = input_tex.resolve().parent
    tex_text = input_tex.read_text(encoding="utf-8")
    search_dirs = [tex_dir / "fig"]
    for entry in graphicspath_entries(tex_text):
        path = Path(entry)
        search_dirs.append(path if path.is_absolute() else tex_dir / path)

    converted: dict[str, str] = {}

    def rewrite_includegraphics(match: re.Match[str]) -> str:
        prefix, image_ref, suffix = match.groups()
        normalized = normalize_tex_path(image_ref)
        ext = Path(normalized).suffix.lower()
        if ext not in ("", ".pdf"):
            return match.group(0)

        pdf_path = resolve_pdf(normalized, tex_dir, search_dirs)
        png_path = cache_dir.resolve() / cache_name(pdf_path, dpi)
        render_first_page(pdf_path, png_path, dpi)
        replacement = png_path.name
        converted[str(pdf_path)] = replacement
        return f"{prefix}{replacement}{suffix}"

    rewritten = INCLUDEGRAPHICS_RE.sub(rewrite_includegraphics, tex_text)
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_tex.write_text(rewritten, encoding="utf-8", newline="")
    return len(converted)


def main() -> int:
    args = parse_args()
    input_tex = Path(args.input)
    output_tex = Path(args.output)
    cache_dir = Path(args.cache_dir)

    if args.dpi <= 0:
        raise SystemExit("--dpi must be a positive integer.")
    if not input_tex.exists():
        raise SystemExit(f"Input TeX file does not exist: {input_tex}")

    try:
        count = prepare_tex(input_tex, output_tex, cache_dir, args.dpi)
    except Exception as exc:
        print(f"prepare-pandoc-images: {exc}", file=sys.stderr)
        return 1

    print(f"Prepared {count} PDF image(s) for Pandoc: {output_tex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
