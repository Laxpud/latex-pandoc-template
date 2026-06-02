#!/usr/bin/env python
"""Namespace this template's custom Word style IDs in a reference docx."""

from __future__ import annotations

import argparse
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
STYLE_ID = f"{{{WORD_NS}}}styleId"
VAL = f"{{{WORD_NS}}}val"

STYLE_ID_MAP = {
    "PaperTitle": "LptPaperTitle",
    "AuthorBlock": "LptAuthorBlock",
    "PaperDate": "LptPaperDate",
    "Abstract": "LptAbstract",
    "Keywords": "LptKeywords",
    "Heading1": "LptHeading1",
    "Heading2": "LptHeading2",
    "Heading3": "LptHeading3",
    "BodyText": "LptBodyText",
    "FigureCaption": "LptFigureCaption",
    "TableCaption": "LptTableCaption",
    "EquationNumbered": "LptEquationNumbered",
    "ReferencesHeading": "LptReferencesHeading",
    "ReferenceItem": "LptReferenceItem",
    "TableHeader": "LptTableHeader",
    "TableBody": "LptTableBody",
}
INVERSE_STYLE_ID_MAP = {value: key for key, value in STYLE_ID_MAP.items()}
PROJECT_STYLE_IDS = set(STYLE_ID_MAP.values())

ET.register_namespace("w", WORD_NS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rewrite project custom Word styles to Lpt-prefixed style IDs."
    )
    parser.add_argument("docx", help="Reference docx to rewrite in place.")
    parser.add_argument(
        "--output",
        help="Optional output path. Defaults to rewriting the input docx in place.",
    )
    return parser.parse_args()


def child_val(element: ET.Element, local_name: str) -> str:
    child = element.find(f"{{{WORD_NS}}}{local_name}")
    return child.get(VAL, "") if child is not None else ""


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def ensure_child(element: ET.Element, local_name_value: str) -> ET.Element:
    child = element.find(f"{{{WORD_NS}}}{local_name_value}")
    if child is not None:
        return child
    child = ET.Element(f"{{{WORD_NS}}}{local_name_value}")
    insert_index = 1 if len(element) > 0 and local_name(element[0]) == "name" else 0
    element.insert(insert_index, child)
    return child


def is_project_style(style: ET.Element, style_id: str) -> bool:
    style_name = child_val(style, "name")
    if style_id in PROJECT_STYLE_IDS:
        return True
    return style_name == style_id or style_name in PROJECT_STYLE_IDS


def insert_project_heading_styles(root: ET.Element) -> int:
    changed = 0
    existing = {
        style.get(STYLE_ID)
        for style in root.findall(f"{{{WORD_NS}}}style")
        if style.get(STYLE_ID)
    }

    for source_id in ("Heading1", "Heading2", "Heading3"):
        target_id = STYLE_ID_MAP[source_id]
        if target_id in existing:
            continue

        source_style = None
        for style in root.findall(f"{{{WORD_NS}}}style"):
            if style.get(STYLE_ID) == source_id:
                source_style = style
                break
        if source_style is None:
            continue

        target_style = ET.fromstring(ET.tostring(source_style, encoding="utf-8"))
        target_style.set(STYLE_ID, target_id)
        target_style.set(f"{{{WORD_NS}}}customStyle", "1")

        name = target_style.find(f"{{{WORD_NS}}}name")
        if name is not None:
            name.set(VAL, target_id)

        based_on = target_style.find(f"{{{WORD_NS}}}basedOn")
        if based_on is not None:
            based_on.set(VAL, "Normal")

        next_style = target_style.find(f"{{{WORD_NS}}}next")
        if next_style is not None:
            next_style.set(VAL, "LptBodyText")

        link = target_style.find(f"{{{WORD_NS}}}link")
        if link is not None:
            target_style.remove(link)

        root.append(target_style)
        existing.add(target_id)
        changed += 1

    return changed


def rewrite_style_refs_in_project_style(style: ET.Element) -> int:
    changed = 0

    for element in style.iter():
        value = element.get(VAL)
        if value in STYLE_ID_MAP:
            element.set(VAL, STYLE_ID_MAP[value])
            changed += 1

    style_id = style.get(STYLE_ID)
    if style_id == "LptBodyText":
        based_on = ensure_child(style, "basedOn")
        if based_on.get(VAL) != "BodyText":
            based_on.set(VAL, "BodyText")
            changed += 1

    return changed


def restore_builtin_style_refs(style: ET.Element) -> int:
    changed = 0

    for element in style.iter():
        if local_name(element) == "name":
            continue
        value = element.get(VAL)
        if value in INVERSE_STYLE_ID_MAP:
            element.set(VAL, INVERSE_STYLE_ID_MAP[value])
            changed += 1

    return changed


def rewrite_styles_xml(root: ET.Element) -> int:
    changed = insert_project_heading_styles(root)

    for style in root.findall(f"{{{WORD_NS}}}style"):
        style_id = style.get(STYLE_ID)
        if not style_id:
            continue

        if not is_project_style(style, style_id):
            changed += restore_builtin_style_refs(style)
            continue

        new_id = STYLE_ID_MAP.get(style_id, style_id)
        if style_id != new_id:
            style.set(STYLE_ID, new_id)
            changed += 1

        name = style.find(f"{{{WORD_NS}}}name")
        if name is not None and name.get(VAL) != new_id:
            name.set(VAL, new_id)
            changed += 1

        changed += rewrite_style_refs_in_project_style(style)

    return changed


def rewrite_document_style_refs(root: ET.Element) -> int:
    changed = 0

    for element in root.iter():
        if local_name(element) not in {"pStyle", "rStyle", "tblStyle"}:
            continue
        value = element.get(VAL)
        if value not in STYLE_ID_MAP:
            continue
        element.set(VAL, STYLE_ID_MAP[value])
        changed += 1

    return changed


def rewrite_xml(xml_bytes: bytes, is_styles_xml: bool) -> tuple[bytes, int]:
    root = ET.fromstring(xml_bytes)
    if is_styles_xml:
        changed = rewrite_styles_xml(root)
    else:
        changed = rewrite_document_style_refs(root)

    if changed == 0:
        return xml_bytes, 0
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), changed


def should_rewrite_xml_part(name: str) -> bool:
    return name.startswith("word/") and name.endswith(".xml")


def namespace_docx_styles(input_docx: Path, output_docx: Path) -> int:
    total_changed = 0
    output_docx.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_path = Path(temp_file.name)

    try:
        with zipfile.ZipFile(input_docx, "r") as source:
            with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target:
                for item in source.infolist():
                    data = source.read(item.filename)
                    if should_rewrite_xml_part(item.filename):
                        data, changed = rewrite_xml(
                            data,
                            is_styles_xml=item.filename == "word/styles.xml",
                        )
                        total_changed += changed
                    target.writestr(item, data)
        shutil.move(str(temp_path), output_docx)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return total_changed


def main() -> int:
    args = parse_args()
    input_docx = Path(args.docx)
    output_docx = Path(args.output) if args.output else input_docx

    if not input_docx.exists():
        raise SystemExit(f"Reference docx does not exist: {input_docx}")

    changed = namespace_docx_styles(input_docx, output_docx)
    print(f"Rewrote {changed} style ID reference(s): {output_docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
