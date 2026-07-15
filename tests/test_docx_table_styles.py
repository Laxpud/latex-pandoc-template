import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
FIGURE_PATH = ROOT / "fig" / "example-fig-2.png"
FILTER_PATH = ROOT / "filters" / "latex-crossref-cn.lua"
REFERENCE_DOCX = ROOT / "reference.docx"
STYLE_NORMALIZER_PATH = ROOT / "scripts" / "namespace-reference-docx-styles.py"
TABLE_STYLE_SCRIPT = ROOT / "scripts" / "apply-docx-table-styles.ps1"
COMPAT_PREP_SCRIPT = ROOT / "scripts" / "prepare-pandoc-compat.py"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
VAL = f"{{{WORD_NS}}}val"
WIDTH = f"{{{WORD_NS}}}w"


def find_powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def read_tables(docx_path: Path) -> list[ET.Element]:
    with zipfile.ZipFile(docx_path) as docx:
        document = ET.fromstring(docx.read("word/document.xml"))
    return document.findall(f".//{{{WORD_NS}}}tbl")


def read_styles(docx_path: Path) -> dict[str, ET.Element]:
    with zipfile.ZipFile(docx_path) as docx:
        styles = ET.fromstring(docx.read("word/styles.xml"))
    return {
        style.get(f"{{{WORD_NS}}}styleId", ""): style
        for style in styles.findall(f"{{{WORD_NS}}}style")
    }


def paragraph_style(paragraph: ET.Element) -> str:
    properties = paragraph.find(f"{{{WORD_NS}}}pPr")
    if properties is None:
        return ""
    style = properties.find(f"{{{WORD_NS}}}pStyle")
    return "" if style is None else style.get(VAL, "")


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(
        text.text or "" for text in paragraph.findall(f".//{{{WORD_NS}}}t")
    )


def read_paragraphs(docx_path: Path) -> list[ET.Element]:
    with zipfile.ZipFile(docx_path) as docx:
        document = ET.fromstring(docx.read("word/document.xml"))
    return document.findall(f".//{{{WORD_NS}}}p")


def table_style(table: ET.Element) -> str:
    properties = table.find(f"{{{WORD_NS}}}tblPr")
    if properties is None:
        return ""
    style = properties.find(f"{{{WORD_NS}}}tblStyle")
    return "" if style is None else style.get(VAL, "")


def paragraph_styles(table: ET.Element) -> set[str]:
    return {
        style.get(VAL, "")
        for style in table.findall(f".//{{{WORD_NS}}}pStyle")
        if style.get(VAL)
    }


class DocxTableStylesTests(unittest.TestCase):
    def test_four_relative_width_subfigures_wrap_into_two_docx_rows(self):
        powershell = find_powershell()
        if powershell is None:
            self.skipTest("PowerShell is required to test DOCX table post-processing")

        image_path = FIGURE_PATH.as_posix()
        subfigures = "\n".join(
            rf"""
  \begin{{subfigure}}[t]{{0.48\linewidth}}
    \centering
    \includegraphics[width=\linewidth,alt={{Accessible subfigure {index}}}]{{{image_path}}}
    \caption{{Subfigure {index}}}
  \end{{subfigure}}
  \hfill
"""
            for index in range(1, 5)
        )
        tex = rf"""
\documentclass{{article}}
\usepackage{{graphicx}}
\usepackage{{subcaption}}
\begin{{document}}
\begin{{figure}}[htbp]
  \centering
{subfigures}
  \caption{{Four subfigures}}
\end{{figure}}
\end{{document}}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_tex = temp_path / "four-subfigures.tex"
            compat_tex = temp_path / "four-subfigures-compat.tex"
            equation_cache = temp_path / "equations"
            output_docx = temp_path / "four-subfigures.docx"
            input_tex.write_text(tex, encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(COMPAT_PREP_SCRIPT),
                    "--input",
                    str(input_tex),
                    "--output",
                    str(compat_tex),
                    "--equation-cache-dir",
                    str(equation_cache),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "pandoc",
                    str(compat_tex),
                    "-o",
                    str(output_docx),
                    f"--lua-filter={FILTER_PATH}",
                    f"--reference-doc={REFERENCE_DOCX}",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-File",
                    str(TABLE_STYLE_SCRIPT),
                    "-DocxFile",
                    str(output_docx),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            tables = read_tables(output_docx)
            paragraphs = read_paragraphs(output_docx)

        figure_tables = [
            table for table in tables if table_style(table) == "FigureTable"
        ]
        self.assertEqual(len(figure_tables), 1)
        rows = figure_tables[0].findall(f"{{{WORD_NS}}}tr")
        self.assertEqual(
            [len(row.findall(f"{{{WORD_NS}}}tc")) for row in rows],
            [2, 2],
        )
        self.assertNotIn(
            "LPTSUBFIGWIDTH:",
            "".join(paragraph_text(paragraph) for paragraph in paragraphs),
        )
        descriptions = [
            drawing.get("descr", "")
            for drawing in figure_tables[0].findall(f".//{{{WP_NS}}}docPr")
        ]
        self.assertEqual(
            descriptions,
            [f"Accessible subfigure {index}" for index in range(1, 5)],
        )
        self.assertNotIn("LPTSUBFIGWIDTH:", "".join(descriptions))

        captions = {
            paragraph_text(paragraph): paragraph_style(paragraph)
            for paragraph in paragraphs
            if paragraph_text(paragraph)
        }
        for index, label in enumerate(("a", "b", "c", "d"), start=1):
            self.assertEqual(
                captions.get(f"({label}) Subfigure {index}"),
                "LptSubfigureCaption",
            )

        grid_width = sum(
            int(column.get(WIDTH, "0"))
            for column in figure_tables[0].findall(
                f"{{{WORD_NS}}}tblGrid/{{{WORD_NS}}}gridCol"
            )
        )
        expected_image_width = round(grid_width * 0.48 * 635)
        extents = figure_tables[0].findall(f".//{{{WP_NS}}}extent")
        self.assertEqual(len(extents), 4)
        for extent in extents:
            self.assertAlmostEqual(
                int(extent.get("cx", "0")),
                expected_image_width,
                delta=635,
            )

    def test_figure_layout_table_is_ignored_but_data_table_is_styled(self):
        powershell = find_powershell()
        if powershell is None:
            self.skipTest("PowerShell is required to test DOCX table post-processing")

        image_path = FIGURE_PATH.as_posix()
        tex = rf"""
\documentclass{{article}}
\usepackage{{graphicx}}
\usepackage{{subcaption}}
\begin{{document}}
\begin{{figure}}[htbp]
  \begin{{center}}
    \includegraphics[width=0.65\linewidth]{{{image_path}}}
  \end{{center}}
  \caption{{Centered figure}}
\end{{figure}}
\begin{{figure}}[htbp]
  \centering
  \begin{{subfigure}}[t]{{0.49\linewidth}}
    \centering
    \includegraphics[width=\linewidth]{{{image_path}}}
    \caption{{First subfigure}}
  \end{{subfigure}}
  \hfill
  \begin{{subfigure}}[t]{{0.49\linewidth}}
    \centering
    \includegraphics[width=\linewidth]{{{image_path}}}
    \caption{{Second subfigure}}
  \end{{subfigure}}
  \caption{{Combined figure}}
\end{{figure}}
\begin{{table}}[htbp]
  \centering
  \begin{{tabular}}{{lc}}
    Name & Value \\
    Alpha & 1 \\
  \end{{tabular}}
\end{{table}}
\end{{document}}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_tex = temp_path / "tables.tex"
            output_docx = temp_path / "tables.docx"
            input_tex.write_text(tex, encoding="utf-8")

            subprocess.run(
                [
                    "pandoc",
                    str(input_tex),
                    "-o",
                    str(output_docx),
                    f"--reference-doc={REFERENCE_DOCX}",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-File",
                    str(TABLE_STYLE_SCRIPT),
                    "-DocxFile",
                    str(output_docx),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            tables = read_tables(output_docx)

        figure_tables = [
            table for table in tables if table_style(table) == "FigureTable"
        ]
        data_tables = [
            table for table in tables if table_style(table) != "FigureTable"
        ]
        self.assertEqual(len(figure_tables), 2)
        self.assertEqual(len(data_tables), 1)

        for figure_table in figure_tables:
            figure_properties = figure_table.find(f"{{{WORD_NS}}}tblPr")
            self.assertIsNotNone(figure_properties)
            self.assertIsNone(figure_properties.find(f"{{{WORD_NS}}}tblBorders"))
            self.assertTrue(
                paragraph_styles(figure_table).isdisjoint(
                    {"LptTableHeader", "LptTableBody"}
                )
            )

        data_table = data_tables[0]
        data_properties = data_table.find(f"{{{WORD_NS}}}tblPr")
        self.assertIsNotNone(data_properties)
        borders = data_properties.find(f"{{{WORD_NS}}}tblBorders")
        self.assertIsNotNone(borders)
        self.assertEqual(borders.find(f"{{{WORD_NS}}}top").get(VAL), "single")
        self.assertEqual(borders.find(f"{{{WORD_NS}}}bottom").get(VAL), "single")
        self.assertEqual(
            paragraph_styles(data_table),
            {"LptTableHeader", "LptTableBody"},
        )

    def test_all_figure_images_and_subcaptions_use_project_styles(self):
        powershell = find_powershell()
        if powershell is None:
            self.skipTest("PowerShell is required to test DOCX table post-processing")

        image_path = FIGURE_PATH.as_posix()
        tex = rf"""
\documentclass{{article}}
\usepackage{{graphicx}}
\usepackage{{subcaption}}
\begin{{document}}
\begin{{figure}}[htbp]
  \centering
  \includegraphics[width=0.65\linewidth]{{{image_path}}}
  \caption{{Ordinary figure}}
  \label{{fig:ordinary}}
\end{{figure}}
\begin{{figure}}[htbp]
  \begin{{center}}
    \includegraphics[width=0.65\linewidth]{{{image_path}}}
  \end{{center}}
  \caption{{Centered figure}}
  \label{{fig:centered}}
\end{{figure}}
\begin{{figure}}[htbp]
  \centering
  \begin{{subfigure}}[t]{{0.49\linewidth}}
    \centering
    \includegraphics[width=\linewidth]{{{image_path}}}
    \caption{{First subfigure}}
  \end{{subfigure}}
  \hfill
  \begin{{subfigure}}[t]{{0.49\linewidth}}
    \centering
    \includegraphics[width=\linewidth]{{{image_path}}}
    \caption{{Second subfigure}}
  \end{{subfigure}}
  \caption{{Combined figure}}
  \label{{fig:combined}}
\end{{figure}}
\end{{document}}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_tex = temp_path / "figures.tex"
            output_docx = temp_path / "figures.docx"
            reference_docx = temp_path / "reference.docx"
            input_tex.write_text(tex, encoding="utf-8")
            shutil.copy2(REFERENCE_DOCX, reference_docx)

            subprocess.run(
                [sys.executable, str(STYLE_NORMALIZER_PATH), str(reference_docx)],
                check=True,
                capture_output=True,
                text=True,
            )
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
            subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-File",
                    str(TABLE_STYLE_SCRIPT),
                    "-DocxFile",
                    str(output_docx),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [sys.executable, str(STYLE_NORMALIZER_PATH), str(output_docx)],
                check=True,
                capture_output=True,
                text=True,
            )

            styles = read_styles(output_docx)
            paragraphs = read_paragraphs(output_docx)
            tables = read_tables(output_docx)

        image_styles = [
            paragraph_style(paragraph)
            for paragraph in paragraphs
            if paragraph.find(f".//{{{WORD_NS}}}drawing") is not None
        ]
        caption_styles = {
            paragraph_text(paragraph): paragraph_style(paragraph)
            for paragraph in paragraphs
            if paragraph_text(paragraph)
        }

        figure_tables = [
            table for table in tables if table_style(table) == "FigureTable"
        ]
        self.assertEqual(len(figure_tables), 2)
        self.assertEqual(image_styles, ["LptFigure"] * 4)
        self.assertEqual(caption_styles.get("(a) First subfigure"), "LptSubfigureCaption")
        self.assertEqual(caption_styles.get("(b) Second subfigure"), "LptSubfigureCaption")
        self.assertEqual(caption_styles.get("图 1 Ordinary figure"), "LptFigureCaption")
        self.assertEqual(caption_styles.get("图 2 Centered figure"), "LptFigureCaption")
        self.assertEqual(caption_styles.get("图 3 Combined figure"), "LptFigureCaption")
        self.assertIn("LptFigure", styles)
        self.assertIn("LptSubfigureCaption", styles)

        figure_style = styles["LptFigure"]
        self.assertEqual(
            figure_style.find(f"{{{WORD_NS}}}basedOn").get(VAL),
            "Figure",
        )
        self.assertIsNotNone(
            figure_style.find(f"{{{WORD_NS}}}pPr/{{{WORD_NS}}}keepNext")
        )
        self.assertEqual(
            figure_style.find(f"{{{WORD_NS}}}pPr/{{{WORD_NS}}}jc").get(VAL),
            "center",
        )
        self.assertEqual(
            styles["LptSubfigureCaption"].find(f"{{{WORD_NS}}}basedOn").get(VAL),
            "ac",
        )


if __name__ == "__main__":
    unittest.main()
