import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
NORMALIZER_PATH = ROOT / "scripts" / "namespace-reference-docx-styles.py"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
VAL = f"{{{WORD_NS}}}val"
STYLE_ID = f"{{{WORD_NS}}}styleId"
ABSTRACT_NUM_ID = f"{{{WORD_NS}}}abstractNumId"
NUM_ID = f"{{{WORD_NS}}}numId"

ET.register_namespace("w", WORD_NS)


def qn(local_name: str) -> str:
    return f"{{{WORD_NS}}}{local_name}"


def load_normalizer():
    spec = importlib.util.spec_from_file_location("docx_style_normalizer", NORMALIZER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load normalizer: {NORMALIZER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_heading_styles(root: ET.Element, num_id: str) -> None:
    for level in range(1, 4):
        style = ET.SubElement(
            root,
            qn("style"),
            {STYLE_ID: f"LptHeading{level}", qn("type"): "paragraph"},
        )
        ET.SubElement(style, qn("name"), {VAL: f"LptHeading{level}"})
        properties = ET.SubElement(style, qn("pPr"))
        num_properties = ET.SubElement(properties, qn("numPr"))
        ET.SubElement(num_properties, qn("ilvl"), {VAL: str(level - 1)})
        ET.SubElement(num_properties, qn("numId"), {VAL: num_id})


def add_abstract_numbering(
    root: ET.Element,
    abstract_num_id: str,
    paragraph_styles: tuple[str, ...],
) -> None:
    abstract_num = ET.SubElement(
        root,
        qn("abstractNum"),
        {ABSTRACT_NUM_ID: abstract_num_id},
    )
    for level, style_id in enumerate(paragraph_styles):
        lvl = ET.SubElement(abstract_num, qn("lvl"), {qn("ilvl"): str(level)})
        ET.SubElement(lvl, qn("pStyle"), {VAL: style_id})
        ET.SubElement(lvl, qn("lvlText"), {VAL: f"%{level + 1}"})


def add_num(root: ET.Element, num_id: str, abstract_num_id: str) -> None:
    num = ET.SubElement(root, qn("num"), {NUM_ID: num_id})
    ET.SubElement(num, qn("abstractNumId"), {VAL: abstract_num_id})


def add_numbered_paragraph(root: ET.Element, num_id: str, text: str) -> None:
    paragraph = ET.SubElement(root, qn("p"))
    properties = ET.SubElement(paragraph, qn("pPr"))
    num_properties = ET.SubElement(properties, qn("numPr"))
    ET.SubElement(num_properties, qn("ilvl"), {VAL: "0"})
    ET.SubElement(num_properties, qn("numId"), {VAL: num_id})
    run = ET.SubElement(paragraph, qn("r"))
    ET.SubElement(run, qn("t")).text = text


def write_minimal_docx(
    path: Path,
    styles: ET.Element,
    numbering: ET.Element,
    document: ET.Element,
) -> None:
    # 最小夹具只保留后处理器真正读取的三个部件，避免测试依赖 Word 或 Pandoc。
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("word/styles.xml", ET.tostring(styles, encoding="utf-8"))
        docx.writestr(
            "word/numbering.xml",
            ET.tostring(numbering, encoding="utf-8"),
        )
        docx.writestr("word/document.xml", ET.tostring(document, encoding="utf-8"))


def read_xml(path: Path, part_name: str) -> ET.Element:
    with zipfile.ZipFile(path) as docx:
        return ET.fromstring(docx.read(part_name))


def heading_style_num_ids(styles: ET.Element) -> set[str]:
    values: set[str] = set()
    for level in range(1, 4):
        style = styles.find(f"{qn('style')}[@{STYLE_ID}='LptHeading{level}']")
        if style is None:
            continue
        num_id = style.find(f"{qn('pPr')}/{qn('numPr')}/{qn('numId')}")
        if num_id is not None:
            values.add(num_id.get(VAL, ""))
    return values


def numbering_order(numbering: ET.Element) -> list[str]:
    order: list[str] = []
    for child in numbering:
        if child.tag == qn("abstractNum"):
            order.append(f"abstractNum:{child.get(ABSTRACT_NUM_ID, '')}")
        elif child.tag == qn("num"):
            order.append(f"num:{child.get(NUM_ID, '')}")
    return order


class DocxNumberingTests(unittest.TestCase):
    def setUp(self):
        self.normalizer = load_normalizer()

    def test_reuses_word_resaved_heading_numbering_and_preserves_item_lists(self):
        styles = ET.Element(qn("styles"))
        add_heading_styles(styles, "4")

        numbering = ET.Element(qn("numbering"))
        add_abstract_numbering(
            numbering,
            "6",
            ("LptHeading1", "LptHeading2", "LptHeading3"),
        )
        add_abstract_numbering(numbering, "990", ("OrderedList",))
        add_abstract_numbering(numbering, "991", ("BulletList",))
        add_num(numbering, "4", "6")
        add_num(numbering, "1001", "990")
        add_num(numbering, "1002", "991")

        document = ET.Element(qn("document"))
        body = ET.SubElement(document, qn("body"))
        for index, num_id in enumerate(("1001", "1001", "1002", "1002"), 1):
            add_numbered_paragraph(body, num_id, f"Item {index}")

        with tempfile.TemporaryDirectory() as temp_dir:
            input_docx = Path(temp_dir) / "input.docx"
            output_docx = Path(temp_dir) / "output.docx"
            write_minimal_docx(input_docx, styles, numbering, document)

            self.normalizer.namespace_docx_styles(input_docx, output_docx)

            output_styles = read_xml(output_docx, "word/styles.xml")
            output_numbering = read_xml(output_docx, "word/numbering.xml")
            output_document = read_xml(output_docx, "word/document.xml")

        self.assertEqual(heading_style_num_ids(output_styles), {"4"})
        self.assertNotIn("abstractNum:99", numbering_order(output_numbering))
        self.assertEqual(
            [
                node.get(VAL)
                for node in output_document.findall(f".//{qn('numPr')}/{qn('numId')}")
            ],
            ["1001", "1001", "1002", "1002"],
        )

    def test_does_not_overwrite_unrelated_numbering_that_uses_id_99(self):
        styles = ET.Element(qn("styles"))
        add_heading_styles(styles, "4")

        numbering = ET.Element(qn("numbering"))
        add_abstract_numbering(numbering, "99", ("UnrelatedList",))
        add_num(numbering, "99", "99")
        document = ET.Element(qn("document"))
        ET.SubElement(document, qn("body"))

        with tempfile.TemporaryDirectory() as temp_dir:
            input_docx = Path(temp_dir) / "input.docx"
            output_docx = Path(temp_dir) / "output.docx"
            write_minimal_docx(input_docx, styles, numbering, document)

            self.normalizer.namespace_docx_styles(input_docx, output_docx)

            output_styles = read_xml(output_docx, "word/styles.xml")
            output_numbering = read_xml(output_docx, "word/numbering.xml")

        unrelated = output_numbering.find(
            f"{qn('abstractNum')}[@{ABSTRACT_NUM_ID}='99']"
        )
        self.assertIsNotNone(unrelated)
        self.assertEqual(
            [node.get(VAL) for node in unrelated.findall(f"{qn('lvl')}/{qn('pStyle')}")],
            ["UnrelatedList"],
        )
        self.assertNotEqual(heading_style_num_ids(output_styles), {"99"})

    def test_rejects_abstract_numbering_after_concrete_numbering(self):
        styles = ET.Element(qn("styles"))
        add_heading_styles(styles, "1")

        numbering = ET.Element(qn("numbering"))
        add_num(numbering, "1", "1")
        add_abstract_numbering(
            numbering,
            "1",
            ("LptHeading1", "LptHeading2", "LptHeading3"),
        )
        document = ET.Element(qn("document"))
        ET.SubElement(document, qn("body"))

        with tempfile.TemporaryDirectory() as temp_dir:
            input_docx = Path(temp_dir) / "input.docx"
            output_docx = Path(temp_dir) / "output.docx"
            write_minimal_docx(input_docx, styles, numbering, document)

            with self.assertRaisesRegex(ValueError, "abstractNum.*num"):
                self.normalizer.namespace_docx_styles(input_docx, output_docx)


if __name__ == "__main__":
    unittest.main()
