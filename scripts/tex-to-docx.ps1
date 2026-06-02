param(
    [string]$InputFile = "temp.tex",
    [string]$OutputFile = "temp-crossref.docx",
    [string]$Bibliography = "temp-ref.bib",
    [string]$Csl = "temp-ref.csl",
    [string]$ReferenceDoc = "",
    [int]$ImageDpi = 300
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Filter = Join-Path $Root "filters\latex-crossref-cn.lua"
$PandocCache = Join-Path $Root ".pandoc-cache"
$PandocImageCache = Join-Path $PandocCache "images"
$PandocInput = Join-Path $PandocCache "temp-pandoc.tex"
$ImagePrepScript = Join-Path $PSScriptRoot "prepare-pandoc-images.py"
$ResourcePath = ".;fig;refference/fig;$PandocImageCache"

Write-Host "Preparing images for Pandoc..."
uv run python $ImagePrepScript `
    --input $InputFile `
    --output $PandocInput `
    --cache-dir $PandocImageCache `
    --dpi $ImageDpi

$PandocArgs = @(
    $PandocInput,
    "-o", $OutputFile,
    "--citeproc",
    "--lua-filter=$Filter",
    "--bibliography=$Bibliography",
    "--csl=$Csl",
    "--resource-path=$ResourcePath"
)

if ($ReferenceDoc) {
    $PandocArgs += "--reference-doc=$ReferenceDoc"
}

Write-Host "Running Pandoc..."
pandoc @PandocArgs

$TableStyleScript = Join-Path $PSScriptRoot "apply-docx-table-styles.ps1"
Write-Host "Applying Word table styles..."
& $TableStyleScript -DocxFile $OutputFile

$StyleNormalizeScript = Join-Path $PSScriptRoot "namespace-reference-docx-styles.py"
Write-Host "Normalizing Word styles..."
uv run python $StyleNormalizeScript $OutputFile

Write-Host "Wrote $OutputFile"
