$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Push-Location $Root
try {
    & ".\scripts\tex-to-docx.ps1" `
        -InputFile "temp.tex" `
        -OutputFile "temp.docx" `
        -Bibliography "reference.bib" `
        -Csl "gbt7714.csl" `
        -ReferenceDoc "reference.docx"
}
finally {
    Pop-Location
}
