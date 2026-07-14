#!/usr/bin/env python
"""Normalize this template's custom Word style IDs in a docx."""

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
ABSTRACT_NUM_ID = f"{{{WORD_NS}}}abstractNumId"
NUM_ID = f"{{{WORD_NS}}}numId"
ILVL = f"{{{WORD_NS}}}ilvl"
POS = f"{{{WORD_NS}}}pos"
LEFT = f"{{{WORD_NS}}}left"
HANGING = f"{{{WORD_NS}}}hanging"
FIRST_LINE = f"{{{WORD_NS}}}firstLine"
FIRST_LINE_CHARS = f"{{{WORD_NS}}}firstLineChars"

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
    "OrderedList": "LptOrderedList",
    "BulletList": "LptBulletList",
    "FigureCaption": "LptFigureCaption",
    "TableCaption": "LptTableCaption",
    "EquationNumbered": "LptEquationNumbered",
    "ReferencesHeading": "LptReferencesHeading",
    "ReferenceItem": "LptReferenceItem",
    "TableHeader": "LptTableHeader",
    "TableBody": "LptTableBody",
}
INVERSE_STYLE_ID_MAP = {value: key for key, value in STYLE_ID_MAP.items()}
FIGURE_STYLE_SOURCES = {
    "LptFigure": "CaptionedFigure",
    "LptSubfigureCaption": "ImageCaption",
}
PROJECT_STYLE_IDS = set(STYLE_ID_MAP.values()) | set(FIGURE_STYLE_SOURCES)
HEADING_NUMBERING_LEVELS = (
    ("0", "LptHeading1", "%1", "360"),
    ("1", "LptHeading2", "%1.%2", "540"),
    ("2", "LptHeading3", "%1.%2.%3", "720"),
)
LIST_STYLE_IDS = ("LptOrderedList", "LptBulletList")

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


def qn(local_name_value: str) -> str:
    return f"{{{WORD_NS}}}{local_name_value}"


def set_attr(element: ET.Element, attr_name: str, value: str) -> int:
    if element.get(attr_name) == value:
        return 0
    element.set(attr_name, value)
    return 1


def remove_children(element: ET.Element, local_name_value: str) -> int:
    removed = 0
    for child in list(element):
        if local_name(child) == local_name_value:
            element.remove(child)
            removed += 1
    return removed


def ensure_style_child(style: ET.Element, local_name_value: str) -> ET.Element:
    child = style.find(qn(local_name_value))
    if child is not None:
        return child

    child = ET.Element(qn(local_name_value))
    if local_name_value == "pPr":
        for index, existing_child in enumerate(style):
            if local_name(existing_child) == "rPr":
                style.insert(index, child)
                return child
    style.append(child)
    return child


def set_child_val(parent: ET.Element, local_name_value: str, value: str) -> int:
    child = parent.find(qn(local_name_value))
    if child is None:
        child = ET.SubElement(parent, qn(local_name_value))
    return set_attr(child, VAL, value)


def replace_child(parent: ET.Element, child: ET.Element, before_names: set[str]) -> int:
    old_child = parent.find(child.tag)
    if old_child is not None:
        parent.remove(old_child)

    for index, existing_child in enumerate(parent):
        if local_name(existing_child) in before_names:
            parent.insert(index, child)
            return 1

    parent.append(child)
    return 1


def heading_num_pr(level: str, num_id: str) -> ET.Element:
    num_pr = ET.Element(qn("numPr"))
    ET.SubElement(num_pr, qn("ilvl"), {VAL: level})
    ET.SubElement(num_pr, qn("numId"), {VAL: num_id})
    return num_pr


def ensure_heading_style_numbering(root: ET.Element, num_id: str) -> int:
    changed = 0

    for level, style_id, _, _ in HEADING_NUMBERING_LEVELS:
        style = root.find(f"{qn('style')}[@{STYLE_ID}='{style_id}']")
        if style is None:
            continue

        ppr = ensure_style_child(style, "pPr")
        changed += replace_child(
            ppr,
            heading_num_pr(level, num_id),
            before_names={"spacing", "ind", "outlineLvl", "rPr"},
        )

    return changed


def create_heading_level(
    level: str,
    style_id: str,
    level_text: str,
    left: str,
) -> ET.Element:
    lvl = ET.Element(qn("lvl"), {ILVL: level})
    ET.SubElement(lvl, qn("start"), {VAL: "1"})
    ET.SubElement(lvl, qn("numFmt"), {VAL: "decimal"})
    ET.SubElement(lvl, qn("pStyle"), {VAL: style_id})
    ET.SubElement(lvl, qn("lvlText"), {VAL: level_text})
    ET.SubElement(lvl, qn("lvlJc"), {VAL: "left"})

    ppr = ET.SubElement(lvl, qn("pPr"))
    tabs = ET.SubElement(ppr, qn("tabs"))
    ET.SubElement(tabs, qn("tab"), {VAL: "num", POS: left})
    ET.SubElement(ppr, qn("ind"), {LEFT: left, HANGING: "360"})
    return lvl




def find_style_id_by_name(root: ET.Element, style_name: str) -> str | None:
    for style in root.findall(qn("style")):
        name = style.find(qn("name"))
        if name is not None and name.get(VAL) == style_name:
            return style.get(STYLE_ID)
    return None


def remove_duplicate_styles(root: ET.Element) -> int:
    seen: set[str] = set()
    changed = 0

    for style in list(root.findall(qn("style"))):
        style_id = style.get(STYLE_ID)
        if not style_id:
            continue
        if style_id not in seen:
            seen.add(style_id)
            continue
        root.remove(style)
        changed += 1

    return changed


def normalize_body_text_style_refs(root: ET.Element) -> int:
    style_ids = {
        style.get(STYLE_ID)
        for style in root.findall(qn("style"))
        if style.get(STYLE_ID)
    }
    if "BodyText" in style_ids:
        return 0

    body_text_id = (
        find_style_id_by_name(root, "Body Text")
        or find_style_id_by_name(root, "Normal")
    )
    if not body_text_id:
        return 0

    changed = 0
    for style in root.findall(qn("style")):
        for ref_name in ("basedOn", "next"):
            ref = style.find(qn(ref_name))
            if ref is not None and ref.get(VAL) == "BodyText":
                changed += set_attr(ref, VAL, body_text_id)

    return changed


def style_heading_num_id(root: ET.Element) -> str | None:
    """返回三个项目标题样式共同引用的编号 ID。"""

    num_ids: set[str] = set()
    for _, style_id, _, _ in HEADING_NUMBERING_LEVELS:
        style = root.find(f"{qn('style')}[@{STYLE_ID}='{style_id}']")
        if style is None:
            continue
        num_id = style.find(f"{qn('pPr')}/{qn('numPr')}/{qn('numId')}")
        if num_id is not None and num_id.get(VAL):
            num_ids.add(num_id.get(VAL, ""))

    return next(iter(num_ids)) if len(num_ids) == 1 else None


def abstract_num_id_for_num(num: ET.Element) -> str:
    abstract_num_id = num.find(qn("abstractNumId"))
    return "" if abstract_num_id is None else abstract_num_id.get(VAL, "")


def is_heading_abstract_num(abstract_num: ET.Element) -> bool:
    """通过标题级别绑定识别项目拥有的多级编号，而不依赖内部数字。"""

    expected = {style_id for _, style_id, _, _ in HEADING_NUMBERING_LEVELS}
    actual = {
        style.get(VAL, "")
        for style in abstract_num.findall(f"{qn('lvl')}/{qn('pStyle')}")
        if style.get(VAL)
    }
    return expected.issubset(actual)


def next_available_numbering_id(
    root: ET.Element,
    element_name: str,
    attribute_name: str,
) -> str:
    """分配最小的正整数 ID，避免覆盖 Word 或 Pandoc 已生成的编号。"""

    used_ids = {
        child.get(attribute_name, "")
        for child in root.findall(qn(element_name))
        if child.get(attribute_name)
    }
    candidate = 1
    while str(candidate) in used_ids:
        candidate += 1
    return str(candidate)


def insert_abstract_num(root: ET.Element, abstract_num: ET.Element) -> None:
    """abstractNum 必须位于所有 num 和清理标记之前。"""

    for index, child in enumerate(root):
        if local_name(child) in {"num", "numIdMacAtCleanup"}:
            root.insert(index, abstract_num)
            return
    root.append(abstract_num)


def insert_num(root: ET.Element, num: ET.Element) -> None:
    """num 位于 abstractNum 之后、numIdMacAtCleanup 之前。"""

    for index, child in enumerate(root):
        if local_name(child) == "numIdMacAtCleanup":
            root.insert(index, num)
            return
    root.append(num)


def find_heading_numbering(
    root: ET.Element,
    preferred_num_id: str | None,
) -> tuple[ET.Element, ET.Element] | None:
    """查找 Word 重存后仍由 LptHeading1-3 共同使用的编号定义。"""

    heading_abstract_nums = [
        abstract_num
        for abstract_num in root.findall(qn("abstractNum"))
        if is_heading_abstract_num(abstract_num)
    ]
    if not heading_abstract_nums:
        return None

    by_id = {
        abstract_num.get(ABSTRACT_NUM_ID, ""): abstract_num
        for abstract_num in heading_abstract_nums
    }
    nums = root.findall(qn("num"))

    # 优先复用 styles.xml 当前引用的编号，避免 Word 另存后产生无意义的再次重编号。
    if preferred_num_id:
        for num in nums:
            if num.get(NUM_ID) != preferred_num_id:
                continue
            abstract_num = by_id.get(abstract_num_id_for_num(num))
            if abstract_num is not None:
                return abstract_num, num

    for num in nums:
        abstract_num = by_id.get(abstract_num_id_for_num(num))
        if abstract_num is not None:
            return abstract_num, num
    return None


def ensure_heading_numbering(
    root: ET.Element,
    preferred_num_id: str | None,
) -> tuple[int, str]:
    """复用或创建项目标题编号，并返回样式应引用的实际 numId。"""

    changed = 0
    existing = find_heading_numbering(root, preferred_num_id)
    if existing is None:
        abstract_num_id = next_available_numbering_id(
            root,
            "abstractNum",
            ABSTRACT_NUM_ID,
        )
        abstract_num = ET.Element(
            qn("abstractNum"),
            {ABSTRACT_NUM_ID: abstract_num_id},
        )
        insert_abstract_num(root, abstract_num)
        changed += 1

        num_id = next_available_numbering_id(root, "num", NUM_ID)
        num = ET.Element(qn("num"), {NUM_ID: num_id})
        insert_num(root, num)
        changed += 1
    else:
        abstract_num, num = existing
        abstract_num_id = abstract_num.get(ABSTRACT_NUM_ID, "")
        num_id = num.get(NUM_ID, "")
        changed += remove_children(abstract_num, "multiLevelType")
        changed += remove_children(abstract_num, "lvl")

    ET.SubElement(abstract_num, qn("multiLevelType"), {VAL: "multilevel"})
    changed += 1
    for level, style_id, level_text, left in HEADING_NUMBERING_LEVELS:
        abstract_num.append(create_heading_level(level, style_id, level_text, left))
        changed += 1

    changed += remove_children(num, "abstractNumId")

    ET.SubElement(
        num,
        qn("abstractNumId"),
        {VAL: abstract_num_id},
    )
    changed += 1
    return changed, num_id


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


def ensure_figure_styles(root: ET.Element) -> int:
    """从 Pandoc 默认图片样式创建可由项目稳定引用的图片样式。"""

    changed = 0
    for target_id, source_id in FIGURE_STYLE_SOURCES.items():
        target_style = root.find(f"{qn('style')}[@{STYLE_ID}='{target_id}']")
        if target_style is not None:
            continue

        source_style = root.find(f"{qn('style')}[@{STYLE_ID}='{source_id}']")
        if source_style is None:
            continue

        target_style = ET.fromstring(ET.tostring(source_style, encoding="utf-8"))
        target_style.set(STYLE_ID, target_id)
        target_style.set(qn("type"), "paragraph")
        target_style.set(qn("customStyle"), "1")
        set_child_val(target_style, "name", target_id)
        root.append(target_style)
        changed += 1

    return changed


def ensure_list_styles(root: ET.Element) -> int:
    """确保列表项样式继承正文外观，但不接管 Pandoc 的编号定义。"""

    body_style = root.find(f"{qn('style')}[@{STYLE_ID}='LptBodyText']")
    if body_style is None:
        return 0

    changed = 0
    for style_id in LIST_STYLE_IDS:
        style = root.find(f"{qn('style')}[@{STYLE_ID}='{style_id}']")
        if style is None:
            style = ET.Element(
                qn("style"),
                {
                    STYLE_ID: style_id,
                    qn("type"): "paragraph",
                    qn("customStyle"): "1",
                },
            )
            root.append(style)
            changed += 1

        changed += set_attr(style, qn("type"), "paragraph")
        changed += set_attr(style, qn("customStyle"), "1")
        changed += set_child_val(style, "name", style_id)
        changed += set_child_val(style, "basedOn", "LptBodyText")
        changed += set_child_val(style, "next", style_id)

        ppr = ensure_style_child(style, "pPr")
        changed += remove_children(ppr, "numPr")
        list_indent = ET.Element(
            qn("ind"),
            {
                FIRST_LINE: "0",
                FIRST_LINE_CHARS: "0",
            },
        )
        changed += replace_child(
            ppr,
            list_indent,
            before_names={"spacing", "contextualSpacing", "jc", "outlineLvl", "rPr"},
        )

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


def rewrite_styles_xml(root: ET.Element, heading_num_id: str | None) -> int:
    changed = remove_duplicate_styles(root)
    changed += insert_project_heading_styles(root)
    changed += ensure_figure_styles(root)
    changed += ensure_list_styles(root)

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

    if heading_num_id is not None:
        changed += ensure_heading_style_numbering(root, heading_num_id)
    changed += normalize_body_text_style_refs(root)
    changed += remove_duplicate_styles(root)
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


def validate_numbering_root(root: ET.Element) -> set[str]:
    """验证 Word 会严格修复的编号顺序、唯一性和引用关系。"""

    abstract_ids: list[str] = []
    num_ids: list[str] = []
    abstract_targets: list[tuple[str, str]] = []
    seen_num = False

    for child in root:
        child_name = local_name(child)
        if child_name == "num":
            seen_num = True
            num_id = child.get(NUM_ID, "")
            num_ids.append(num_id)
            abstract_targets.append((num_id, abstract_num_id_for_num(child)))
        elif child_name == "abstractNum":
            if seen_num:
                raise ValueError(
                    "word/numbering.xml: abstractNum must precede every num element"
                )
            abstract_ids.append(child.get(ABSTRACT_NUM_ID, ""))

    duplicate_abstract_ids = {
        value for value in abstract_ids if abstract_ids.count(value) > 1
    }
    if duplicate_abstract_ids:
        raise ValueError(
            "word/numbering.xml: duplicate abstractNumId values: "
            + ", ".join(sorted(duplicate_abstract_ids))
        )

    duplicate_num_ids = {value for value in num_ids if num_ids.count(value) > 1}
    if duplicate_num_ids:
        raise ValueError(
            "word/numbering.xml: duplicate numId values: "
            + ", ".join(sorted(duplicate_num_ids))
        )

    abstract_id_set = set(abstract_ids)
    missing_targets = [
        f"numId={num_id}->abstractNumId={abstract_num_id}"
        for num_id, abstract_num_id in abstract_targets
        if abstract_num_id not in abstract_id_set
    ]
    if missing_targets:
        raise ValueError(
            "word/numbering.xml: missing abstract numbering targets: "
            + ", ".join(missing_targets)
        )
    return set(num_ids)


def validate_num_id_references(
    xml_bytes: bytes,
    part_name: str,
    defined_num_ids: set[str],
) -> None:
    root = ET.fromstring(xml_bytes)
    missing = {
        node.get(VAL, "")
        for node in root.findall(f".//{qn('numId')}")
        if node.get(VAL, "") not in defined_num_ids | {"0"}
    }
    if missing:
        raise ValueError(
            f"{part_name}: references undefined numId values: "
            + ", ".join(sorted(missing))
        )


def validate_docx_parts(parts: dict[str, bytes]) -> None:
    numbering_bytes = parts.get("word/numbering.xml")
    if numbering_bytes is None:
        return

    defined_num_ids = validate_numbering_root(ET.fromstring(numbering_bytes))
    for part_name in ("word/styles.xml", "word/document.xml"):
        xml_bytes = parts.get(part_name)
        if xml_bytes is not None:
            validate_num_id_references(xml_bytes, part_name, defined_num_ids)


def rewrite_xml(
    xml_bytes: bytes,
    part_name: str,
    heading_num_id: str | None,
) -> tuple[bytes, int]:
    root = ET.fromstring(xml_bytes)
    if part_name == "word/styles.xml":
        changed = rewrite_styles_xml(root, heading_num_id)
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

    # 编号 ID 是 numbering.xml 与 styles.xml 的跨部件契约，必须先整体读取，
    # 再把 Word 实际保存的编号传给样式重写，不能逐个 ZIP 条目独立处理。
    with zipfile.ZipFile(input_docx, "r") as source:
        items = source.infolist()
        parts = {item.filename: source.read(item.filename) for item in items}

    preferred_num_id = None
    styles_bytes = parts.get("word/styles.xml")
    if styles_bytes is not None:
        preferred_num_id = style_heading_num_id(ET.fromstring(styles_bytes))

    heading_num_id = None
    numbering_bytes = parts.get("word/numbering.xml")
    if numbering_bytes is not None:
        numbering_root = ET.fromstring(numbering_bytes)
        changed, heading_num_id = ensure_heading_numbering(
            numbering_root,
            preferred_num_id,
        )
        total_changed += changed
        parts["word/numbering.xml"] = ET.tostring(
            numbering_root,
            encoding="utf-8",
            xml_declaration=True,
        )

    for item in items:
        if item.filename == "word/numbering.xml":
            continue
        if should_rewrite_xml_part(item.filename):
            parts[item.filename], changed = rewrite_xml(
                parts[item.filename],
                part_name=item.filename,
                heading_num_id=heading_num_id,
            )
            total_changed += changed

    validate_docx_parts(parts)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_path = Path(temp_file.name)
    try:
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target:
            for item in items:
                target.writestr(item, parts[item.filename])
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
