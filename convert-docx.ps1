$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonEntry = Join-Path $Root "scripts\tex-to-docx.py"

& uv run python $PythonEntry @args
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
