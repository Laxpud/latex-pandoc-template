"""以 ``python -m lpt_docx`` 调用统一的论文转换入口。"""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
