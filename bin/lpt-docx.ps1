$ErrorActionPreference = "Stop"

# 入口位于 bin/；仅定位工具环境，不切换当前论文目录。
$Root = Split-Path -Parent $PSScriptRoot

& uv run --project $Root python -m lpt_docx @args
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
