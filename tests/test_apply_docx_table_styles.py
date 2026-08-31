import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from lxml import etree as ET


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "apply-docx-table-styles.py"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"


def load_module():
    spec = importlib.util.spec_from_file_location("apply_docx_table_styles", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def qn(local_name: str, namespace: str = WORD_NS) -> str:
    return f"{{{namespace}}}{local_name}"


class ApplyDocxTableStylesTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_numbered_equation_image_style_is_preserved(self):
        xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{WORD_NS}">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="LptEquationNumbered"/></w:pPr><w:r><w:drawing/></w:r></w:p>
    <w:p><w:r><w:drawing/></w:r></w:p>
  </w:body>
</w:document>
""".encode()

        rewritten, stats = self.module.process_document_xml(
            xml,
            header_style="LptTableHeader",
            body_style="LptTableBody",
            figure_style="LptFigure",
        )
        root = ET.fromstring(rewritten)
        styles = root.xpath("//w:p/w:pPr/w:pStyle/@w:val", namespaces={"w": WORD_NS})

        self.assertEqual(styles, ["LptEquationNumbered", "LptFigure"])
        self.assertEqual(stats.image_paragraphs, 2)

    def test_namespace_prefixes_and_ignorable_value_are_preserved(self):
        xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{WORD_NS}" xmlns:mc="{MC_NS}" xmlns:w14="urn:test:w14" mc:Ignorable="w14">
  <w:body><w:p/></w:body>
</w:document>
""".encode()

        rewritten, _ = self.module.process_document_xml(
            xml,
            header_style="LptTableHeader",
            body_style="LptTableBody",
            figure_style="LptFigure",
        )
        root = ET.fromstring(rewritten)

        self.assertEqual(root.nsmap["w14"], "urn:test:w14")
        self.assertEqual(root.get(qn("Ignorable", MC_NS)), "w14")

    def test_missing_document_part_does_not_replace_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            docx = Path(temp_dir) / "missing-document.docx"
            with zipfile.ZipFile(docx, "w") as archive:
                archive.writestr("[Content_Types].xml", b"<Types/>")
            original = docx.read_bytes()

            with self.assertRaisesRegex(ValueError, "word/document.xml"):
                self.module.apply_docx_table_styles(docx, docx)

            self.assertEqual(docx.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
