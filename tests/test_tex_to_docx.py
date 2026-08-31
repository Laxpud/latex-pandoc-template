import importlib.util
import argparse
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


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

    def test_core_runs_outside_repository_with_space_in_output_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_docx = temp_path / "Word review draft.docx"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--output",
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
