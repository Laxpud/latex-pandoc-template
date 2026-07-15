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
    $Ns.AddNamespace("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing")
    $Ns.AddNamespace("a", "http://schemas.openxmlformats.org/drawingml/2006/main")
    $Ns.AddNamespace("pic", "http://schemas.openxmlformats.org/drawingml/2006/picture")
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

    function Get-SubfigureLayoutMarker {
        param([System.Xml.XmlElement]$Cell)

        $Pattern = "LPTSUBFIGWIDTH:(?<Subfigure>[0-9]+(?:\.[0-9]+)?)(?:;LPTIMAGEWIDTH:(?<Image>[0-9]+(?:\.[0-9]+)?))?"
        $DrawingProperties = @($Cell.SelectNodes(".//wp:docPr", $script:Ns))
        foreach ($DrawingProperty in $DrawingProperties) {
            $Match = [regex]::Match($DrawingProperty.GetAttribute("descr"), $Pattern)
            if (-not $Match.Success) {
                continue
            }

            $Culture = [System.Globalization.CultureInfo]::InvariantCulture
            $SubfigureWidth = [double]::Parse($Match.Groups["Subfigure"].Value, $Culture)
            $ImageWidth = $null
            if ($Match.Groups["Image"].Success) {
                $ImageWidth = [double]::Parse($Match.Groups["Image"].Value, $Culture)
            }

            return [pscustomobject]@{
                SubfigureWidth = $SubfigureWidth
                ImageWidth = $ImageWidth
            }
        }

        return $null
    }

    function Remove-SubfigureLayoutMarker {
        param([System.Xml.XmlElement]$Cell)

        $Pattern = "LPTSUBFIGWIDTH:[0-9]+(?:\.[0-9]+)?(?:;LPTIMAGEWIDTH:[0-9]+(?:\.[0-9]+)?)?"
        $DrawingProperties = @($Cell.SelectNodes(".//wp:docPr", $script:Ns))
        foreach ($DrawingProperty in $DrawingProperties) {
            $Description = $DrawingProperty.GetAttribute("descr")
            if ($Description -notmatch "LPTSUBFIGWIDTH:") {
                continue
            }

            # 标记附加在用户 alt 文本末尾。删除内部字段时同时清理分隔符，
            # 但保留用户原有的图片替代文本，避免损害 DOCX 可访问性。
            $Cleaned = [regex]::Replace($Description, "\s*\|\s*$Pattern", "").Trim()
            if ($Cleaned -eq $Description) {
                $Cleaned = [regex]::Replace($Description, $Pattern, "").Trim()
            }
            if ($Cleaned) {
                [void]$DrawingProperty.SetAttribute("descr", $Cleaned)
            } else {
                [void]$DrawingProperty.RemoveAttribute("descr")
            }
        }
    }

    function Set-CellGridSpanAndWidth {
        param(
            [System.Xml.XmlElement]$Cell,
            [int]$GridSpan,
            [int]$WidthTwips,
            [xml]$Document
        )

        $TcPr = Ensure-ChildElement -Parent $Cell -LocalName "tcPr" -Document $Document -Prepend
        $TcW = Ensure-ChildElement -Parent $TcPr -LocalName "tcW" -Document $Document
        [void]$TcW.SetAttribute("type", $script:WordNs, "dxa")
        [void]$TcW.SetAttribute("w", $script:WordNs, [string]$WidthTwips)

        $ExistingSpan = $TcPr.SelectSingleNode("w:gridSpan", $script:Ns)
        if ($GridSpan -le 1) {
            if ($ExistingSpan) {
                [void]$TcPr.RemoveChild($ExistingSpan)
            }
            return
        }

        $GridSpanElement = Ensure-ChildElement -Parent $TcPr -LocalName "gridSpan" -Document $Document
        [void]$GridSpanElement.SetAttribute("val", $script:WordNs, [string]$GridSpan)
    }

    function Set-CellDrawingWidth {
        param(
            [System.Xml.XmlElement]$Cell,
            [long]$TargetWidthEmu
        )

        if ($TargetWidthEmu -le 0) {
            return
        }

        $InlineExtents = @($Cell.SelectNodes(".//wp:extent", $script:Ns))
        foreach ($Extent in $InlineExtents) {
            $OldWidth = [long]$Extent.GetAttribute("cx")
            $OldHeight = [long]$Extent.GetAttribute("cy")
            if ($OldWidth -le 0 -or $OldHeight -le 0) {
                continue
            }

            $TargetHeightEmu = [long][Math]::Round($OldHeight * $TargetWidthEmu / $OldWidth)
            [void]$Extent.SetAttribute("cx", [string]$TargetWidthEmu)
            [void]$Extent.SetAttribute("cy", [string]$TargetHeightEmu)

            # Word 同时在 inline extent 与 picture transform 中保存尺寸。两处
            # 必须同步，否则 Word 打开时可能采用其中一处并重新改写图片大小。
            $ShapeExtents = @($Cell.SelectNodes(".//pic:spPr/a:xfrm/a:ext", $script:Ns))
            foreach ($ShapeExtent in $ShapeExtents) {
                [void]$ShapeExtent.SetAttribute("cx", [string]$TargetWidthEmu)
                [void]$ShapeExtent.SetAttribute("cy", [string]$TargetHeightEmu)
            }
        }
    }

    function Set-SubfigureTableLayout {
        param(
            [System.Xml.XmlElement]$Table,
            [xml]$Document
        )

        $Cells = @($Table.SelectNodes("./w:tr/w:tc", $script:Ns))
        if ($Cells.Count -lt 2) {
            return $false
        }

        $GridColumns = @($Table.SelectNodes("./w:tblGrid/w:gridCol", $script:Ns))
        $TotalWidthTwips = 0
        foreach ($GridColumn in $GridColumns) {
            $TotalWidthTwips += [int]$GridColumn.GetAttribute("w", $script:WordNs)
        }
        if ($TotalWidthTwips -le 0) {
            return $false
        }

        $Items = [System.Collections.Generic.List[object]]::new()
        $OriginalCellWidthTwips = $TotalWidthTwips / $Cells.Count
        foreach ($Cell in $Cells) {
            $Marker = Get-SubfigureLayoutMarker -Cell $Cell
            if (-not $Marker) {
                # 只要有一个单元格不是预处理标记的子图，就保留 Pandoc 原布局，
                # 避免把普通 center 图片或未知 FigureTable 错当成子图重排。
                return $false
            }
            $Items.Add([pscustomobject]@{
                Cell = $Cell
                Width = $Marker.SubfigureWidth
                ImageWidth = $Marker.ImageWidth
                OriginalCellWidthTwips = $OriginalCellWidthTwips
            })
        }

        # 1. 按 LaTeX 的盒子宽度顺序累计；加入下一项超过一行宽度时换行。
        $LayoutRows = [System.Collections.Generic.List[object]]::new()
        $CurrentItems = [System.Collections.Generic.List[object]]::new()
        $CurrentWidth = 0.0
        foreach ($Item in $Items) {
            if ($CurrentItems.Count -gt 0 -and ($CurrentWidth + $Item.Width) -gt 1.000001) {
                $LayoutRows.Add([pscustomobject]@{
                    Items = @($CurrentItems)
                    Width = $CurrentWidth
                })
                $CurrentItems = [System.Collections.Generic.List[object]]::new()
                $CurrentWidth = 0.0
            }
            $CurrentItems.Add($Item)
            $CurrentWidth += $Item.Width
        }
        if ($CurrentItems.Count -gt 0) {
            $LayoutRows.Add([pscustomobject]@{
                Items = @($CurrentItems)
                Width = $CurrentWidth
            })
        }

        # 2. 汇总每行归一化后的单元格边界，建立能同时表达不同列数的 Word
        # 表格网格。最后一行只有一个子图时，它会跨越全部网格列并保持图片居中。
        $BoundarySet = [System.Collections.Generic.HashSet[int]]::new()
        [void]$BoundarySet.Add(0)
        [void]$BoundarySet.Add(1000000)
        foreach ($LayoutRow in $LayoutRows) {
            $Cumulative = 0.0
            for ($Index = 0; $Index -lt $LayoutRow.Items.Count - 1; $Index++) {
                $Cumulative += $LayoutRow.Items[$Index].Width / $LayoutRow.Width
                [void]$BoundarySet.Add([int][Math]::Round($Cumulative * 1000000))
            }
        }
        [int[]]$Boundaries = @($BoundarySet | Sort-Object)

        $TblGrid = $Table.SelectSingleNode("./w:tblGrid", $script:Ns)
        while ($TblGrid.FirstChild) {
            [void]$TblGrid.RemoveChild($TblGrid.FirstChild)
        }
        for ($Index = 0; $Index -lt $Boundaries.Count - 1; $Index++) {
            $GridWidth = [int][Math]::Round(
                $TotalWidthTwips * ($Boundaries[$Index + 1] - $Boundaries[$Index]) / 1000000
            )
            $GridColumn = $Document.CreateElement("w", "gridCol", $script:WordNs)
            [void]$GridColumn.SetAttribute("w", $script:WordNs, [string]$GridWidth)
            [void]$TblGrid.AppendChild($GridColumn)
        }

        $TblPr = Ensure-ChildElement -Parent $Table -LocalName "tblPr" -Document $Document -Prepend
        $TblJc = Ensure-ChildElement -Parent $TblPr -LocalName "jc" -Document $Document
        [void]$TblJc.SetAttribute("val", $script:WordNs, "center")
        $TblW = Ensure-ChildElement -Parent $TblPr -LocalName "tblW" -Document $Document
        [void]$TblW.SetAttribute("type", $script:WordNs, "dxa")
        [void]$TblW.SetAttribute("w", $script:WordNs, [string]$TotalWidthTwips)
        $TblLayout = Ensure-ChildElement -Parent $TblPr -LocalName "tblLayout" -Document $Document
        [void]$TblLayout.SetAttribute("type", $script:WordNs, "fixed")

        $OriginalRows = @($Table.SelectNodes("./w:tr", $script:Ns))
        $RowProperties = $OriginalRows[0].SelectSingleNode("./w:trPr", $script:Ns)
        foreach ($OriginalRow in $OriginalRows) {
            [void]$Table.RemoveChild($OriginalRow)
        }

        # 3. 复用 Pandoc 已生成的单元格、题注和关系，只重建行结构及宽度。
        foreach ($LayoutRow in $LayoutRows) {
            $NewRow = $Document.CreateElement("w", "tr", $script:WordNs)
            if ($RowProperties) {
                [void]$NewRow.AppendChild($RowProperties.CloneNode($true))
            }

            $StartBoundary = 0
            $Cumulative = 0.0
            for ($Index = 0; $Index -lt $LayoutRow.Items.Count; $Index++) {
                $Item = $LayoutRow.Items[$Index]
                if ($Index -eq $LayoutRow.Items.Count - 1) {
                    $EndBoundary = 1000000
                } else {
                    $Cumulative += $Item.Width / $LayoutRow.Width
                    $EndBoundary = [int][Math]::Round($Cumulative * 1000000)
                }

                $StartGridIndex = [Array]::IndexOf($Boundaries, [int]$StartBoundary)
                $EndGridIndex = [Array]::IndexOf($Boundaries, [int]$EndBoundary)
                $GridSpan = $EndGridIndex - $StartGridIndex
                $CellWidthTwips = [int][Math]::Round(
                    $TotalWidthTwips * ($EndBoundary - $StartBoundary) / 1000000
                )
                Set-CellGridSpanAndWidth `
                    -Cell $Item.Cell `
                    -GridSpan $GridSpan `
                    -WidthTwips $CellWidthTwips `
                    -Document $Document

                if ($null -ne $Item.ImageWidth) {
                    $TargetWidthEmu = [long][Math]::Round(
                        $TotalWidthTwips * 635 * $Item.Width * $Item.ImageWidth
                    )
                } else {
                    $Scale = $CellWidthTwips / $Item.OriginalCellWidthTwips
                    $CurrentExtent = $Item.Cell.SelectSingleNode(".//wp:extent", $script:Ns)
                    $TargetWidthEmu = if ($CurrentExtent) {
                        [long][Math]::Round([long]$CurrentExtent.GetAttribute("cx") * $Scale)
                    } else {
                        0
                    }
                }
                Set-CellDrawingWidth -Cell $Item.Cell -TargetWidthEmu $TargetWidthEmu
                Remove-SubfigureLayoutMarker -Cell $Item.Cell
                [void]$NewRow.AppendChild($Item.Cell)
                $StartBoundary = $EndBoundary
            }
            [void]$Table.AppendChild($NewRow)
        }

        return $true
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
            [void](Set-SubfigureTableLayout -Table $Table -Document $Xml)
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
