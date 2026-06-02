$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Push-Location $Root
try {
    & ".\scripts\tex-to-docx.ps1" `
        -InputFile "temp.tex" `
        -OutputFile "temp.docx" `
        -Bibliography "temp-ref.bib" `
        -Csl "temp-ref.csl" `
        -ReferenceDoc "reference.docx"
}
finally {
    Pop-Location
}
