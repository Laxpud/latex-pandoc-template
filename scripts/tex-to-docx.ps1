param(
    [string]$InputFile = "temp.tex",
    [string]$OutputFile = "temp-crossref.docx",
    [string]$Bibliography = "temp-ref.bib",
    [string]$Csl = "temp-ref.csl",
    [string]$ReferenceDoc = "",
    [int]$ImageDpi = 300
)

$ErrorActionPreference = "Stop"

function Assert-NativeSuccess {
    param([string]$StepName)

    if ($LASTEXITCODE -ne 0) {
        throw "$StepName failed with exit code $LASTEXITCODE"
    }
}

$Root = Split-Path -Parent $PSScriptRoot
$Filter = Join-Path $Root "filters\latex-crossref-cn.lua"
$PandocCache = Join-Path $Root ".pandoc-cache"
$PandocImageCache = Join-Path $PandocCache "images"
$PandocCompatCache = Join-Path $PandocCache "compat"
$PandocEquationCache = Join-Path $PandocCache "equations"
$PandocCompatInput = Join-Path $PandocCompatCache "temp-compat.tex"
$PandocInput = Join-Path $PandocCache "temp-pandoc.tex"
$CompatPrepScript = Join-Path $PSScriptRoot "prepare-pandoc-compat.py"
$ImagePrepScript = Join-Path $PSScriptRoot "prepare-pandoc-images.py"
$ResourcePath = ".;fig;refference/fig;$PandocImageCache;$PandocEquationCache"

Write-Host "Preparing LaTeX compatibility input for Pandoc..."
uv run python $CompatPrepScript `
    --input $InputFile `
    --output $PandocCompatInput `
    --equation-cache-dir $PandocEquationCache
Assert-NativeSuccess "Preparing LaTeX compatibility input"

Write-Host "Preparing images for Pandoc..."
uv run python $ImagePrepScript `
    --input $PandocCompatInput `
    --output $PandocInput `
    --cache-dir $PandocImageCache `
    --base-dir $Root `
    --dpi $ImageDpi
Assert-NativeSuccess "Preparing images"

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
Assert-NativeSuccess "Running Pandoc"

$TableStyleScript = Join-Path $PSScriptRoot "apply-docx-table-styles.ps1"
Write-Host "Applying Word table styles..."
& $TableStyleScript -DocxFile $OutputFile

$StyleNormalizeScript = Join-Path $PSScriptRoot "namespace-reference-docx-styles.py"
Write-Host "Normalizing Word styles..."
uv run python $StyleNormalizeScript $OutputFile
Assert-NativeSuccess "Normalizing Word styles"

Write-Host "Wrote $OutputFile"
