#!/usr/bin/env python
"""Apply this template's table, subfigure, and image styles to a DOCX file."""

from __future__ import annotations

import argparse
import copy
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from lxml import etree as ET


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
NS = {"w": WORD_NS, "wp": WP_NS, "a": A_NS, "pic": PIC_NS}
MARKER_RE = re.compile(
    r"LPTSUBFIGWIDTH:(?P<subfigure>[0-9]+(?:\.[0-9]+)?)"
    r"(?:;LPTIMAGEWIDTH:(?P<image>[0-9]+(?:\.[0-9]+)?))?"
)


@dataclass(frozen=True)
class LayoutMarker:
    subfigure_width: float
    image_width: float | None


@dataclass
class LayoutItem:
    cell: ET._Element
    width: float
    image_width: float | None
    original_cell_width_twips: float


@dataclass(frozen=True)
class ProcessingStats:
    data_tables: int
    figure_tables: int
    subfigure_tables: int
    image_paragraphs: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply project table and image styles to a DOCX file."
    )
    parser.add_argument("docx", help="DOCX file to rewrite in place.")
    parser.add_argument(
        "--output",
        help="Optional output path. Defaults to rewriting the input DOCX in place.",
    )
    parser.add_argument("--header-style", default="LptTableHeader")
    parser.add_argument("--body-style", default="LptTableBody")
    parser.add_argument("--figure-style", default="LptFigure")
    return parser.parse_args()


def qn(local_name: str, namespace: str = WORD_NS) -> str:
    return f"{{{namespace}}}{local_name}"


def ensure_child(
    parent: ET._Element,
    local_name: str,
    *,
    prepend: bool = False,
) -> ET._Element:
    child = parent.find(qn(local_name))
    if child is not None:
        return child

    child = ET.Element(qn(local_name))
    if prepend and len(parent):
        parent.insert(0, child)
    else:
        parent.append(child)
    return child


def clear_border(borders: ET._Element, local_name: str) -> None:
    border = ensure_child(borders, local_name)
    border.attrib.clear()
    border.set(qn("val"), "nil")


def set_border(borders: ET._Element, local_name: str, size: str) -> None:
    border = ensure_child(borders, local_name)
    border.attrib.clear()
    border.set(qn("val"), "single")
    border.set(qn("sz"), size)
    border.set(qn("space"), "0")
    border.set(qn("color"), "000000")


def set_three_line_table_borders(table: ET._Element) -> None:
    table_properties = ensure_child(table, "tblPr", prepend=True)
    table_borders = ensure_child(table_properties, "tblBorders")

    set_border(table_borders, "top", "12")
    set_border(table_borders, "bottom", "12")
    for name in ("left", "right", "insideH", "insideV"):
        clear_border(table_borders, name)

    rows = table.xpath("./w:tr", namespaces=NS)
    for row_index, row in enumerate(rows):
        is_first_row = row_index == 0
        is_last_row = row_index == len(rows) - 1
        for cell in row.xpath("./w:tc", namespaces=NS):
            cell_properties = ensure_child(cell, "tcPr", prepend=True)
            cell_borders = ensure_child(cell_properties, "tcBorders")
            for name in ("left", "right", "insideH", "insideV"):
                clear_border(cell_borders, name)

            if is_first_row:
                set_border(cell_borders, "top", "12")
                set_border(cell_borders, "bottom", "8")
            elif is_last_row:
                clear_border(cell_borders, "top")
                set_border(cell_borders, "bottom", "12")
            else:
                clear_border(cell_borders, "top")
                clear_border(cell_borders, "bottom")


def set_table_autofit_and_center(table: ET._Element) -> None:
    table_properties = ensure_child(table, "tblPr", prepend=True)
    justification = ensure_child(table_properties, "jc")
    justification.set(qn("val"), "center")

    table_width = ensure_child(table_properties, "tblW")
    table_width.set(qn("type"), "auto")
    table_width.set(qn("w"), "0")

    table_layout = ensure_child(table_properties, "tblLayout")
    table_layout.set(qn("type"), "autofit")


def set_paragraph_style(paragraph: ET._Element, style_name: str) -> None:
    properties = paragraph.find(qn("pPr"))
    if properties is None:
        properties = ET.Element(qn("pPr"))
        paragraph.insert(0, properties)

    style = properties.find(qn("pStyle"))
    if style is None:
        style = ET.Element(qn("pStyle"))
        properties.insert(0, style)
    style.set(qn("val"), style_name)


def get_subfigure_layout_marker(cell: ET._Element) -> LayoutMarker | None:
    for drawing_property in cell.xpath(".//wp:docPr", namespaces=NS):
        match = MARKER_RE.search(drawing_property.get("descr", ""))
        if match is None:
            continue
        image_group = match.group("image")
        return LayoutMarker(
            subfigure_width=float(match.group("subfigure")),
            image_width=float(image_group) if image_group is not None else None,
        )
    return None


def remove_subfigure_layout_marker(cell: ET._Element) -> None:
    for drawing_property in cell.xpath(".//wp:docPr", namespaces=NS):
        description = drawing_property.get("descr", "")
        if "LPTSUBFIGWIDTH:" not in description:
            continue

        cleaned = re.sub(rf"\s*\|\s*{MARKER_RE.pattern}", "", description).strip()
        if cleaned == description:
            cleaned = MARKER_RE.sub("", description).strip()
        if cleaned:
            drawing_property.set("descr", cleaned)
        else:
            drawing_property.attrib.pop("descr", None)


def set_cell_grid_span_and_width(
    cell: ET._Element,
    grid_span: int,
    width_twips: int,
) -> None:
    properties = ensure_child(cell, "tcPr", prepend=True)
    width = ensure_child(properties, "tcW")
    width.set(qn("type"), "dxa")
    width.set(qn("w"), str(width_twips))

    existing_span = properties.find(qn("gridSpan"))
    if grid_span <= 1:
        if existing_span is not None:
            properties.remove(existing_span)
        return

    span = ensure_child(properties, "gridSpan")
    span.set(qn("val"), str(grid_span))


def set_cell_drawing_width(cell: ET._Element, target_width_emu: int) -> None:
    if target_width_emu <= 0:
        return

    for extent in cell.xpath(".//wp:extent", namespaces=NS):
        old_width = int(extent.get("cx", "0"))
        old_height = int(extent.get("cy", "0"))
        if old_width <= 0 or old_height <= 0:
            continue

        target_height_emu = round(old_height * target_width_emu / old_width)
        extent.set("cx", str(target_width_emu))
        extent.set("cy", str(target_height_emu))

        # Word stores drawing dimensions in both locations and may repair the
        # document if they disagree.
        for shape_extent in cell.xpath(
            ".//pic:spPr/a:xfrm/a:ext",
            namespaces=NS,
        ):
            shape_extent.set("cx", str(target_width_emu))
            shape_extent.set("cy", str(target_height_emu))


def set_subfigure_table_layout(table: ET._Element) -> bool:
    cells = table.xpath("./w:tr/w:tc", namespaces=NS)
    if len(cells) < 2:
        return False

    grid_columns = table.xpath("./w:tblGrid/w:gridCol", namespaces=NS)
    total_width_twips = sum(int(column.get(qn("w"), "0")) for column in grid_columns)
    if total_width_twips <= 0:
        return False

    original_cell_width_twips = total_width_twips / len(cells)
    items: list[LayoutItem] = []
    for cell in cells:
        marker = get_subfigure_layout_marker(cell)
        if marker is None:
            # Keep Pandoc's original layout unless every cell belongs to the
            # compatibility preprocessor's marked subfigure set.
            return False
        items.append(
            LayoutItem(
                cell=cell,
                width=marker.subfigure_width,
                image_width=marker.image_width,
                original_cell_width_twips=original_cell_width_twips,
            )
        )

    layout_rows: list[list[LayoutItem]] = []
    current_items: list[LayoutItem] = []
    current_width = 0.0
    for item in items:
        if current_items and current_width + item.width > 1.000001:
            layout_rows.append(current_items)
            current_items = []
            current_width = 0.0
        current_items.append(item)
        current_width += item.width
    if current_items:
        layout_rows.append(current_items)

    boundaries = {0, 1_000_000}
    for row_items in layout_rows:
        row_width = sum(item.width for item in row_items)
        cumulative = 0.0
        for item in row_items[:-1]:
            cumulative += item.width / row_width
            boundaries.add(round(cumulative * 1_000_000))
    sorted_boundaries = sorted(boundaries)

    table_grid = table.find(qn("tblGrid"))
    if table_grid is None:
        return False
    for child in list(table_grid):
        table_grid.remove(child)
    for start, end in zip(sorted_boundaries, sorted_boundaries[1:]):
        grid_width = round(total_width_twips * (end - start) / 1_000_000)
        ET.SubElement(table_grid, qn("gridCol"), {qn("w"): str(grid_width)})

    table_properties = ensure_child(table, "tblPr", prepend=True)
    justification = ensure_child(table_properties, "jc")
    justification.set(qn("val"), "center")
    table_width = ensure_child(table_properties, "tblW")
    table_width.set(qn("type"), "dxa")
    table_width.set(qn("w"), str(total_width_twips))
    table_layout = ensure_child(table_properties, "tblLayout")
    table_layout.set(qn("type"), "fixed")

    original_rows = table.xpath("./w:tr", namespaces=NS)
    row_properties = original_rows[0].find(qn("trPr"))
    for row in original_rows:
        table.remove(row)

    for row_items in layout_rows:
        new_row = ET.Element(qn("tr"))
        if row_properties is not None:
            new_row.append(copy.deepcopy(row_properties))

        row_width = sum(item.width for item in row_items)
        start_boundary = 0
        cumulative = 0.0
        for index, item in enumerate(row_items):
            if index == len(row_items) - 1:
                end_boundary = 1_000_000
            else:
                cumulative += item.width / row_width
                end_boundary = round(cumulative * 1_000_000)

            start_grid_index = sorted_boundaries.index(start_boundary)
            end_grid_index = sorted_boundaries.index(end_boundary)
            grid_span = end_grid_index - start_grid_index
            cell_width_twips = round(
                total_width_twips * (end_boundary - start_boundary) / 1_000_000
            )
            set_cell_grid_span_and_width(item.cell, grid_span, cell_width_twips)

            if item.image_width is not None:
                target_width_emu = round(
                    total_width_twips * 635 * item.width * item.image_width
                )
            else:
                scale = cell_width_twips / item.original_cell_width_twips
                current_extent = item.cell.find(f".//{qn('extent', WP_NS)}")
                target_width_emu = (
                    round(int(current_extent.get("cx", "0")) * scale)
                    if current_extent is not None
                    else 0
                )
            set_cell_drawing_width(item.cell, target_width_emu)
            remove_subfigure_layout_marker(item.cell)
            new_row.append(item.cell)
            start_boundary = end_boundary
        table.append(new_row)

    return True


def process_document_xml(
    xml_bytes: bytes,
    *,
    header_style: str,
    body_style: str,
    figure_style: str,
) -> tuple[bytes, ProcessingStats]:
    parser = ET.XMLParser(remove_blank_text=False, resolve_entities=False)
    root = ET.fromstring(xml_bytes, parser=parser)
    data_table_count = 0
    figure_table_count = 0
    subfigure_table_count = 0

    for table in root.xpath("//w:tbl", namespaces=NS):
        table_style = table.find("./w:tblPr/w:tblStyle", namespaces=NS)
        table_style_id = table_style.get(qn("val"), "") if table_style is not None else ""
        if table_style_id == "FigureTable":
            figure_table_count += 1
            if set_subfigure_table_layout(table):
                subfigure_table_count += 1
            continue

        data_table_count += 1
        set_table_autofit_and_center(table)
        set_three_line_table_borders(table)
        rows = table.xpath("./w:tr", namespaces=NS)
        for row_index, row in enumerate(rows):
            style_name = header_style if row_index == 0 else body_style
            for paragraph in row.xpath("./w:tc//w:p", namespaces=NS):
                set_paragraph_style(paragraph, style_name)

    image_paragraphs = root.xpath("//w:p[.//w:drawing]", namespaces=NS)
    for paragraph in image_paragraphs:
        paragraph_style = paragraph.find("./w:pPr/w:pStyle", namespaces=NS)
        style_id = (
            paragraph_style.get(qn("val"), "")
            if paragraph_style is not None
            else ""
        )
        if style_id != "LptEquationNumbered":
            set_paragraph_style(paragraph, figure_style)

    rewritten = ET.tostring(
        root,
        encoding="UTF-8",
        xml_declaration=True,
        standalone=True,
    )
    return rewritten, ProcessingStats(
        data_tables=data_table_count,
        figure_tables=figure_table_count,
        subfigure_tables=subfigure_table_count,
        image_paragraphs=len(image_paragraphs),
    )


def apply_docx_table_styles(
    input_docx: Path,
    output_docx: Path,
    *,
    header_style: str = "LptTableHeader",
    body_style: str = "LptTableBody",
    figure_style: str = "LptFigure",
) -> ProcessingStats:
    if not input_docx.is_file():
        raise FileNotFoundError(f"DOCX file does not exist: {input_docx}")

    with zipfile.ZipFile(input_docx, "r") as source:
        items = source.infolist()
        parts = {item.filename: source.read(item.filename) for item in items}

    document_name = "word/document.xml"
    if document_name not in parts:
        raise ValueError(f"{document_name} not found in {input_docx}")
    parts[document_name], stats = process_document_xml(
        parts[document_name],
        header_style=header_style,
        body_style=body_style,
        figure_style=figure_style,
    )

    output_docx.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        delete=False,
        dir=output_docx.parent,
        prefix=f".{output_docx.stem}-",
        suffix=".docx",
    ) as temp_file:
        temp_path = Path(temp_file.name)
    try:
        with zipfile.ZipFile(temp_path, "w") as target:
            for item in items:
                target.writestr(item, parts[item.filename])
        os.replace(temp_path, output_docx)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return stats


def main() -> int:
    args = parse_args()
    input_docx = Path(args.docx).resolve()
    output_docx = Path(args.output).resolve() if args.output else input_docx
    try:
        stats = apply_docx_table_styles(
            input_docx,
            output_docx,
            header_style=args.header_style,
            body_style=args.body_style,
            figure_style=args.figure_style,
        )
    except (OSError, ValueError, ET.XMLSyntaxError, zipfile.BadZipFile) as exc:
        raise SystemExit(f"apply-docx-table-styles: {exc}") from exc

    print(
        "Applied DOCX table styles: "
        f"{stats.data_tables} data table(s), "
        f"{stats.figure_tables} figure table(s), "
        f"{stats.subfigure_tables} subfigure layout(s), "
        f"{stats.image_paragraphs} image paragraph(s): {output_docx}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
