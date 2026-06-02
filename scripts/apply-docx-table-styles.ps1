param(
    [Parameter(Mandatory = $true)]
    [string]$DocxFile,
    [string]$HeaderStyle = "LptTableHeader",
    [string]$BodyStyle = "LptTableBody"
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
    $WordNs = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    function Ensure-ChildElement {
        param(
            [System.Xml.XmlElement]$Parent,
            [string]$LocalName,
            [xml]$Document,
            [switch]$Prepend
        )

        $Child = $Parent.SelectSingleNode("w:$LocalName", $script:Ns)
        if ($Child) {
            return $Child
        }

        $Child = $Document.CreateElement("w", $LocalName, $script:WordNs)
        if ($Prepend -and $Parent.FirstChild) {
            [void]$Parent.InsertBefore($Child, $Parent.FirstChild)
        } else {
            [void]$Parent.AppendChild($Child)
        }

        return $Child
    }

    function Clear-Border {
        param(
            [System.Xml.XmlElement]$Borders,
            [string]$LocalName,
            [xml]$Document
        )

        $Border = Ensure-ChildElement -Parent $Borders -LocalName $LocalName -Document $Document
        [void]$Border.RemoveAllAttributes()
        [void]$Border.SetAttribute("val", $script:WordNs, "nil")
    }

    function Set-Border {
        param(
            [System.Xml.XmlElement]$Borders,
            [string]$LocalName,
            [xml]$Document,
            [string]$Size
        )

        $Border = Ensure-ChildElement -Parent $Borders -LocalName $LocalName -Document $Document
        [void]$Border.RemoveAllAttributes()
        [void]$Border.SetAttribute("val", $script:WordNs, "single")
        [void]$Border.SetAttribute("sz", $script:WordNs, $Size)
        [void]$Border.SetAttribute("space", $script:WordNs, "0")
        [void]$Border.SetAttribute("color", $script:WordNs, "000000")
    }

    function Set-ThreeLineTableBorders {
        param(
            [System.Xml.XmlElement]$Table,
            [xml]$Document
        )

        $TblPr = Ensure-ChildElement -Parent $Table -LocalName "tblPr" -Document $Document -Prepend
        $TblBorders = Ensure-ChildElement -Parent $TblPr -LocalName "tblBorders" -Document $Document

        Set-Border -Borders $TblBorders -LocalName "top" -Document $Document -Size "12"
        Set-Border -Borders $TblBorders -LocalName "bottom" -Document $Document -Size "12"
        Clear-Border -Borders $TblBorders -LocalName "left" -Document $Document
        Clear-Border -Borders $TblBorders -LocalName "right" -Document $Document
        Clear-Border -Borders $TblBorders -LocalName "insideH" -Document $Document
        Clear-Border -Borders $TblBorders -LocalName "insideV" -Document $Document

        $Rows = $Table.SelectNodes("./w:tr", $script:Ns)
        for ($RowIndex = 0; $RowIndex -lt $Rows.Count; $RowIndex++) {
            $Cells = $Rows[$RowIndex].SelectNodes("./w:tc", $script:Ns)
            $IsFirstRow = $RowIndex -eq 0
            $IsLastRow = $RowIndex -eq ($Rows.Count - 1)

            foreach ($Cell in $Cells) {
                $TcPr = Ensure-ChildElement -Parent $Cell -LocalName "tcPr" -Document $Document -Prepend
                $TcBorders = Ensure-ChildElement -Parent $TcPr -LocalName "tcBorders" -Document $Document

                Clear-Border -Borders $TcBorders -LocalName "left" -Document $Document
                Clear-Border -Borders $TcBorders -LocalName "right" -Document $Document
                Clear-Border -Borders $TcBorders -LocalName "insideH" -Document $Document
                Clear-Border -Borders $TcBorders -LocalName "insideV" -Document $Document

                if ($IsFirstRow) {
                    Set-Border -Borders $TcBorders -LocalName "top" -Document $Document -Size "12"
                    Set-Border -Borders $TcBorders -LocalName "bottom" -Document $Document -Size "8"
                } elseif ($IsLastRow) {
                    Clear-Border -Borders $TcBorders -LocalName "top" -Document $Document
                    Set-Border -Borders $TcBorders -LocalName "bottom" -Document $Document -Size "12"
                } else {
                    Clear-Border -Borders $TcBorders -LocalName "top" -Document $Document
                    Clear-Border -Borders $TcBorders -LocalName "bottom" -Document $Document
                }
            }
        }
    }

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
        Set-ThreeLineTableBorders -Table $Table -Document $Xml

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
