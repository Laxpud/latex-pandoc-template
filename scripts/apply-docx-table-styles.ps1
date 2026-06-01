param(
    [Parameter(Mandatory = $true)]
    [string]$DocxFile,
    [string]$HeaderStyle = "TableHeader",
    [string]$BodyStyle = "TableBody"
)

$ErrorActionPreference = "Stop"

$ResolvedDocx = Resolve-Path $DocxFile
$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString("N"))
$TempDocx = Join-Path $TempDir "styled.docx"

New-Item -ItemType Directory -Path $TempDir | Out-Null
Copy-Item -LiteralPath $ResolvedDocx -Destination $TempDocx

Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$Zip = [System.IO.Compression.ZipFile]::Open($TempDocx, [System.IO.Compression.ZipArchiveMode]::Update)
try {
    $Entry = $Zip.GetEntry("word/document.xml")
    if (-not $Entry) {
        throw "word/document.xml not found in $DocxFile"
    }

    $Reader = [System.IO.StreamReader]::new($Entry.Open())
    $XmlText = $Reader.ReadToEnd()
    $Reader.Close()

    $Xml = [xml]$XmlText
    $Xml.PreserveWhitespace = $true

    $Ns = [System.Xml.XmlNamespaceManager]::new($Xml.NameTable)
    $Ns.AddNamespace("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")

    function Set-ParagraphStyle {
        param(
            [System.Xml.XmlElement]$Paragraph,
            [string]$StyleName,
            [xml]$Document
        )

        $WordNs = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        $PPr = $Paragraph.SelectSingleNode("w:pPr", $script:Ns)
        if (-not $PPr) {
            $PPr = $Document.CreateElement("w", "pPr", $WordNs)
            if ($Paragraph.FirstChild) {
                [void]$Paragraph.InsertBefore($PPr, $Paragraph.FirstChild)
            } else {
                [void]$Paragraph.AppendChild($PPr)
            }
        }

        $PStyle = $PPr.SelectSingleNode("w:pStyle", $script:Ns)
        if (-not $PStyle) {
            $PStyle = $Document.CreateElement("w", "pStyle", $WordNs)
            if ($PPr.FirstChild) {
                [void]$PPr.InsertBefore($PStyle, $PPr.FirstChild)
            } else {
                [void]$PPr.AppendChild($PStyle)
            }
        }

        [void]$PStyle.SetAttribute("val", $WordNs, $StyleName)
    }

    $Tables = $Xml.SelectNodes("//w:tbl", $Ns)
    foreach ($Table in $Tables) {
        $Rows = $Table.SelectNodes("./w:tr", $Ns)
        for ($RowIndex = 0; $RowIndex -lt $Rows.Count; $RowIndex++) {
            $Style = if ($RowIndex -eq 0) { $HeaderStyle } else { $BodyStyle }
            $Cells = $Rows[$RowIndex].SelectNodes("./w:tc", $Ns)

            foreach ($Cell in $Cells) {
                $Paragraphs = $Cell.SelectNodes(".//w:p", $Ns)
                foreach ($Paragraph in $Paragraphs) {
                    Set-ParagraphStyle -Paragraph $Paragraph -StyleName $Style -Document $Xml
                }
            }
        }
    }

    $Entry.Delete()
    $NewEntry = $Zip.CreateEntry("word/document.xml")
    $Writer = [System.IO.StreamWriter]::new($NewEntry.Open())
    $Xml.Save($Writer)
    $Writer.Close()
}
finally {
    $Zip.Dispose()
}

Copy-Item -LiteralPath $TempDocx -Destination $ResolvedDocx -Force
Remove-Item -LiteralPath $TempDir -Recurse -Force
