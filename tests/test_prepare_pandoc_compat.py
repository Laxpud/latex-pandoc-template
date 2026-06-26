import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "prepare-pandoc-compat.py"


def load_module():
    spec = importlib.util.spec_from_file_location("prepare_pandoc_compat", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PreparePandocCompatTests(unittest.TestCase):
    def test_expands_glossaries_siunitx_and_bm_macros(self):
        module = load_module()
        tex = r"""
\newacronym{IWSGE}{IWSGE}{In Water Surface Ground Effect}
\newacronym{HAUV}{HAUV}{Hybrid Aerial-underwater Vehicle}
\glsxtrnewsymbol[description={Rotor radius, \si{m}}]{rotorRadius}{\ensuremath{R}}
\begin{document}
The \gls{IWSGE} case uses two \glspl{HAUV}, radius \gls{rotorRadius},
speed \SI{450}{Hz}, band \SIrange{450}{700}{Hz}, angle \ang{-2},
unit \si{m}, and vector $\bm{x}$.
\printunsrtglossary[type=symbols]
\printunsrtglossary[type=acronym]
\end{document}
"""

        with tempfile.TemporaryDirectory() as tmp:
            result = module.prepare_tex_text(
                tex,
                input_dir=ROOT,
                equation_cache_dir=Path(tmp),
                render_equation_svg=lambda equation, cache_dir: Path("unused.svg"),
            )

        self.assertNotIn(r"\gls", result.text)
        self.assertNotIn(r"\SI", result.text)
        self.assertNotIn(r"\SIrange", result.text)
        self.assertNotIn(r"\ang", result.text)
        self.assertNotIn(r"\bm", result.text)
        self.assertNotIn(r"\begin{description}", result.text)
        self.assertNotIn(r"\item", result.text)
        self.assertIn(r"\begin{tabular}{ll}", result.text)
        self.assertIn(r"\textbf{R} & Rotor radius, m", result.text)
        self.assertIn(r"\textbf{IWSGE} & In Water Surface Ground Effect", result.text)
        self.assertIn("IWSGE", result.text)
        self.assertIn("HAUVs", result.text)
        self.assertIn("radius R", result.text)
        self.assertIn("450 Hz", result.text)
        self.assertIn("450--700 Hz", result.text)
        self.assertIn("-2°", result.text)
        self.assertIn(r"$\boldsymbol{x}$", result.text)

    def test_keeps_labeled_equation_on_native_pandoc_path(self):
        module = load_module()
        rendered = []

        def fake_render(equation, cache_dir):
            rendered.append(equation)
            return cache_dir / "eq-sample.svg"

        tex = r"""
\begin{document}
Equation~\ref{eq:sample} is important.
\begin{equation}
\begin{aligned}
  \label{eq:sample}
  a &= b + c \\
  d &= e + f
\end{aligned}
\end{equation}
\end{document}
"""

        with tempfile.TemporaryDirectory() as tmp:
            result = module.prepare_tex_text(
                tex,
                input_dir=ROOT,
                equation_cache_dir=Path(tmp),
                render_equation_svg=fake_render,
            )

        self.assertEqual(result.equations_rendered, 0)
        self.assertEqual(rendered, [])
        self.assertIn(r"\begin{equation}", result.text)
        self.assertIn(r"\label{eq:sample}", result.text)
        self.assertNotIn(r"\hypertarget{eq:sample}", result.text)
        self.assertNotIn(r"\includegraphics", result.text)
        self.assertIn(r"Equation~\ref{eq:sample}", result.text)


if __name__ == "__main__":
    unittest.main()
