param(
    [Parameter(Mandatory = $true)]
    [string]$DocxFile,
    [string]$HeaderStyle = "LptTableHeader",
    [string]$BodyStyle = "LptTableBody",
    [string]$FigureStyle = "LptFigure"
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

    function Set-TableAutoFitAndCenter {
        param(
            [System.Xml.XmlElement]$Table,
            [xml]$Document
        )

        $TblPr = Ensure-ChildElement -Parent $Table -LocalName "tblPr" -Document $Document -Prepend

        $TblJc = Ensure-ChildElement -Parent $TblPr -LocalName "jc" -Document $Document
        [void]$TblJc.SetAttribute("val", $script:WordNs, "center")

        $TblW = Ensure-ChildElement -Parent $TblPr -LocalName "tblW" -Document $Document
        [void]$TblW.SetAttribute("type", $script:WordNs, "auto")
        [void]$TblW.SetAttribute("w", $script:WordNs, "0")

        $TblLayout = Ensure-ChildElement -Parent $TblPr -LocalName "tblLayout" -Document $Document
        [void]$TblLayout.SetAttribute("type", $script:WordNs, "autofit")
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
        # Pandoc 会用 FigureTable 承载 subfigure 等复合图片布局。该表格只负责排列图片与题注，
        # 不属于论文数据表；若继续执行三线表和段落样式处理，图片外侧就会出现可见边框，
        # 同时原有的 CaptionedFigure / ImageCaption 样式也会被表头样式覆盖。
        $TableStyle = $Table.SelectSingleNode("./w:tblPr/w:tblStyle", $Ns)
        $TableStyleId = if ($TableStyle) {
            $TableStyle.GetAttribute("val", $WordNs)
        } else {
            ""
        }

        if ($TableStyleId -eq "FigureTable") {
            continue
        }
        Set-TableAutoFitAndCenter -Table $Table -Document $Xml
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

    # Pandoc 会根据 Figure 的复杂程度选择 CaptionedFigure、Compact 等默认段落样式。
    # 这里在 DOCX 结构已经确定后统一图片段落，既覆盖普通 figure、center 和 subfigure，
    # 又不会因 AST 包装而额外生成 FigureTable。公式图片保留专用的编号公式样式。
    $ImageParagraphs = $Xml.SelectNodes("//w:p[.//w:drawing]", $Ns)
    foreach ($Paragraph in $ImageParagraphs) {
        $ParagraphStyle = $Paragraph.SelectSingleNode("./w:pPr/w:pStyle", $Ns)
        $ParagraphStyleId = if ($ParagraphStyle) {
            $ParagraphStyle.GetAttribute("val", $WordNs)
        } else {
            ""
        }

        if ($ParagraphStyleId -ne "LptEquationNumbered") {
            Set-ParagraphStyle -Paragraph $Paragraph -StyleName $FigureStyle -Document $Xml
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
