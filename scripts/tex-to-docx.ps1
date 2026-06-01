param(
    [string]$InputFile = "temp.tex",
    [string]$OutputFile = "temp-crossref.docx",
    [string]$Bibliography = "temp-ref.bib",
    [string]$Csl = "temp-ref.csl",
    [string]$ReferenceDoc = ""
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Filter = Join-Path $Root "filters\latex-crossref-cn.lua"
$ResourcePath = ".;fig;refference/fig"
$PandocArgs = @(
    $InputFile,
    "-o", $OutputFile,
    "--lua-filter=$Filter",
    "--citeproc",
    "--bibliography=$Bibliography",
    "--csl=$Csl",
    "--resource-path=$ResourcePath"
)

if ($ReferenceDoc) {
    $PandocArgs += "--reference-doc=$ReferenceDoc"
}

pandoc @PandocArgs
