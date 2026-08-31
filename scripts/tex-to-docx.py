#!/usr/bin/env python
"""Backward-compatible script wrapper for the installable ``lpt-docx`` CLI."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "src"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

from lpt_docx.cli import (  # noqa: E402,F401
    PipelineError,
    ToolResources,
    build_parser,
    cache_key,
    convert,
    load_tool_resources,
    main,
    pandoc_resource_dirs,
    parse_args,
    positive_int,
    resolve_cli_path,
    resolve_project_paths,
)


if __name__ == "__main__":
    raise SystemExit(main())
