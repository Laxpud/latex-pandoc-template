import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
FILTER_PATH = ROOT / "filters" / "latex-crossref-cn.lua"
REFERENCE_DOCX = ROOT / "reference.docx"
STYLE_NORMALIZER_PATH = ROOT / "scripts" / "namespace-reference-docx-styles.py"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
VAL = f"{{{WORD_NS}}}val"


def load_style_normalizer():
    spec = importlib.util.spec_from_file_location(
        "namespace_reference_docx_styles",
        STYLE_NORMALIZER_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def list_paragraph_styles(docx_path: Path) -> dict[str, str]:
    with zipfile.ZipFile(docx_path) as docx:
        root = ET.fromstring(docx.read("word/document.xml"))

    result: dict[str, str] = {}
    for paragraph in root.findall(f".//{{{WORD_NS}}}p"):
        properties = paragraph.find(f"{{{WORD_NS}}}pPr")
        if properties is None or properties.find(f"{{{WORD_NS}}}numPr") is None:
            continue

        style = properties.find(f"{{{WORD_NS}}}pStyle")
        text = "".join(paragraph.itertext()).strip()
        if style is not None and text:
            result[text] = style.get(VAL, "")

    return result


class DocxListStylesTests(unittest.TestCase):
    def test_lists_keep_native_numbering_and_use_project_styles(self):
        tex = r"""
\documentclass{article}
\begin{document}
\begin{enumerate}
  \item Ordered item.
\end{enumerate}
\begin{itemize}
  \item Bullet item.
\end{itemize}
\end{document}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_tex = temp_path / "lists.tex"
            output_docx = temp_path / "lists.docx"
            reference_docx = temp_path / "reference.docx"
            input_tex.write_text(tex, encoding="utf-8")
            shutil.copy2(REFERENCE_DOCX, reference_docx)

            normalizer = load_style_normalizer()
            normalizer.namespace_docx_styles(reference_docx, reference_docx)

            subprocess.run(
                [
                    "pandoc",
                    str(input_tex),
                    "-o",
                    str(output_docx),
                    f"--lua-filter={FILTER_PATH}",
                    f"--reference-doc={reference_docx}",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            styles = list_paragraph_styles(output_docx)

        self.assertEqual(styles.get("Ordered item."), "LptOrderedList")
        self.assertEqual(styles.get("Bullet item."), "LptBulletList")


if __name__ == "__main__":
    unittest.main()
