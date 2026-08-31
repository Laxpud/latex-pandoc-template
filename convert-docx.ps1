$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

& uv run --project $Root lpt-docx @args
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
