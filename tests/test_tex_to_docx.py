import importlib.util
import argparse
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import pymupdf as fitz


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "tex-to-docx.py"


def load_module():
    spec = importlib.util.spec_from_file_location("tex_to_docx", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TexToDocxTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_positive_image_dpi_validation(self):
        self.assertEqual(self.module.positive_int("300"), 300)
        with self.assertRaises(argparse.ArgumentTypeError):
            self.module.positive_int("0")

    def test_relative_cli_paths_use_invocation_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            invocation_dir = Path(temp_dir).resolve()
            self.assertEqual(
                self.module.resolve_cli_path(Path("draft.tex"), invocation_dir),
                invocation_dir / "draft.tex",
            )

    def test_default_project_paths_follow_input_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir).resolve()
            args = self.module.parse_args(["paper.tex"])
            paths = self.module.resolve_project_paths(
                args,
                self.module.load_tool_resources(),
                invocation_dir=project_dir,
            )

            self.assertEqual(paths.input_file, project_dir / "paper.tex")
            self.assertEqual(paths.output_file, project_dir / "paper.docx")
            self.assertEqual(paths.project_root, project_dir)
            self.assertEqual(
                paths.bibliographies,
                (project_dir / "reference.bib",),
            )
            self.assertEqual(paths.cache_dir, project_dir / ".pandoc-cache")

    def test_bundled_tool_resources_are_available(self):
        resources = self.module.load_tool_resources()

        for path in (
            resources.lua_filter,
            resources.csl,
            resources.reference_doc,
            resources.compat_script,
            resources.image_script,
            resources.table_style_script,
            resources.style_normalizer_script,
        ):
            self.assertTrue(path.is_file(), path)

    def test_core_converts_external_project_with_local_assets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "External paper project"
            assets_dir = temp_path / "assets"
            assets_dir.mkdir(parents=True)
            shutil.copyfile(
                ROOT / "fig" / "example-fig-2.png",
                assets_dir / "raster.png",
            )
            with fitz.open() as pdf:
                page = pdf.new_page(width=180, height=100)
                page.draw_rect(fitz.Rect(20, 20, 160, 80), color=(0, 0, 0))
                pdf.save(assets_dir / "vector.pdf")

            (temp_path / "temp.tex").write_text(
                """\\documentclass{article}
\\usepackage{graphicx}
\\graphicspath{{assets/}}
\\title{External project}
\\author{Test Author}
\\begin{document}
\\maketitle
External citation \\cite{external2026}.
\\begin{figure}
\\includegraphics[width=0.4\\linewidth]{raster.png}
\\caption{Raster asset}
\\label{fig:raster}
\\end{figure}
\\begin{figure}
\\includegraphics[width=0.4\\linewidth]{vector.pdf}
\\caption{PDF asset}
\\label{fig:vector}
\\end{figure}
\\bibliography{reference}
\\end{document}
""",
                encoding="utf-8",
            )
            (temp_path / "reference.bib").write_text(
                """@article{external2026,
  author = {Doe, Jane},
  title = {External Project Test},
  journal = {Testing Journal},
  year = {2026}
}
""",
                encoding="utf-8",
            )
            output_docx = temp_path / "Word review draft.docx"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "-o",
                    str(output_docx),
                ],
                cwd=temp_path,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output_docx) as docx:
                self.assertIn("word/document.xml", docx.namelist())
            image_cache = temp_path / ".pandoc-cache" / "images"
            self.assertEqual(len(list(image_cache.glob("vector-*-300dpi.png"))), 1)
            self.assertEqual(list((temp_path / ".pandoc-cache" / "runs").iterdir()), [])

    def test_missing_input_keeps_existing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_docx = temp_path / "existing.docx"
            output_docx.write_bytes(b"existing output")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--input",
                    str(temp_path / "missing.tex"),
                    "--output",
                    str(output_docx),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Input TeX file does not exist", result.stderr)
            self.assertEqual(output_docx.read_bytes(), b"existing output")


if __name__ == "__main__":
    unittest.main()
