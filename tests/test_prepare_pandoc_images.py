import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "prepare-pandoc-images.py"


def load_module():
    spec = importlib.util.spec_from_file_location("prepare_pandoc_images", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PreparePandocImagesTests(unittest.TestCase):
    def test_base_dir_keeps_graphicspath_relative_to_project_root(self):
        module = load_module()
        tex_dir = ROOT / ".pandoc-cache" / "compat"
        base_dir = ROOT
        source_dir = ROOT / "manuscript"

        search_dirs = module.image_search_dirs(
            tex_text=r"\graphicspath{{fig/}{refference/fig/}}",
            tex_dir=tex_dir,
            base_dir=base_dir,
            source_dir=source_dir,
        )

        self.assertEqual(search_dirs[0], source_dir)
        self.assertIn(base_dir, search_dirs)
        self.assertIn(base_dir / "fig", search_dirs)
        self.assertIn(base_dir / "refference" / "fig", search_dirs)
        self.assertNotIn(tex_dir / "fig", search_dirs)

    def test_project_root_resolves_explicit_relative_image_path(self):
        module = load_module()
        search_dirs = module.image_search_dirs(
            tex_text="",
            tex_dir=ROOT / ".pandoc-cache" / "runs" / "example",
            base_dir=ROOT,
        )

        candidates = module.candidate_paths(
            "fig/example-fig-2.png",
            ROOT / ".pandoc-cache" / "runs" / "example",
            search_dirs,
        )

        self.assertIn(ROOT / "fig" / "example-fig-2.png", candidates)


if __name__ == "__main__":
    unittest.main()
