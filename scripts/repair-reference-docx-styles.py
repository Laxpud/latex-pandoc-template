#!/usr/bin/env python
"""Repair duplicate Word style IDs in a Pandoc reference docx.

Pandoc can hang when a reference docx contains duplicate w:styleId values.
This helper keeps the most likely custom style ID and renames the conflicting
fallback style into a unique internal ID before Pandoc reads the document.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
STYLE_ID = f"{{{WORD_NS}}}styleId"
VAL = f"{{{WORD_NS}}}val"

ET.register_namespace("w", WORD_NS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy a reference docx and make duplicate Word style IDs unique."
    )
    parser.add_argument("--input", required=True, help="Input reference docx.")
    parser.add_argument("--output", required=True, help="Output repaired docx.")
    return parser.parse_args()


def child_val(element: ET.Element, local_name: str) -> str:
    child = element.find(f"{{{WORD_NS}}}{local_name}")
    return child.get(VAL, "") if child is not None else ""


def unique_style_id(base: str, used: set[str]) -> str:
    candidate = f"{base}Base"
    if candidate not in used:
        return candidate

    index = 2
    while f"{candidate}{index}" in used:
        index += 1
    return f"{candidate}{index}"


def choose_keeper(style_id: str, styles: list[ET.Element]) -> ET.Element:
    for style in styles:
        if child_val(style, "name") == style_id:
            return style
    return styles[-1]


def repair_styles_xml(styles_xml: bytes) -> tuple[bytes, list[str]]:
    root = ET.fromstring(styles_xml)
    groups: dict[str, list[ET.Element]] = defaultdict(list)

    for style in root.findall(f"{{{WORD_NS}}}style"):
        style_id = style.get(STYLE_ID)
        if style_id:
            groups[style_id].append(style)

    used = set(groups)
    repaired: list[str] = []

    for style_id, styles in groups.items():
        if len(styles) < 2:
            continue

        keeper = choose_keeper(style_id, styles)
        renamed_ids: list[str] = []

        for style in styles:
            if style is keeper:
                continue
            new_id = unique_style_id(style_id, used)
            used.add(new_id)
            style.set(STYLE_ID, new_id)
            renamed_ids.append(new_id)

        based_on = keeper.find(f"{{{WORD_NS}}}basedOn")
        if based_on is not None and based_on.get(VAL) == style_id:
            based_on.set(VAL, renamed_ids[0] if renamed_ids else "Normal")

        repaired.append(f"{style_id} -> {', '.join(renamed_ids)}")

    return ET.tostring(root, encoding="utf-8", xml_declaration=True), repaired


def write_repaired_docx(input_docx: Path, output_docx: Path) -> list[str]:
    output_docx.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(input_docx, "r") as source:
        if "word/styles.xml" not in source.namelist():
            shutil.copyfile(input_docx, output_docx)
            return []

        styles_xml, repaired = repair_styles_xml(source.read("word/styles.xml"))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
            temp_path = Path(temp_file.name)

        try:
            with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target:
                for item in source.infolist():
                    data = styles_xml if item.filename == "word/styles.xml" else source.read(item.filename)
                    target.writestr(item, data)
            shutil.move(str(temp_path), output_docx)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    return repaired


def main() -> int:
    args = parse_args()
    input_docx = Path(args.input)
    output_docx = Path(args.output)

    if not input_docx.exists():
        raise SystemExit(f"Reference docx does not exist: {input_docx}")

    repaired = write_repaired_docx(input_docx, output_docx)
    if repaired:
        print("Repaired duplicate reference docx style IDs: " + "; ".join(repaired))
    else:
        print(f"Reference docx style IDs are unique: {output_docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
