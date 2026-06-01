-- Add simple Chinese-style figure, table, and equation numbers when converting
-- this LaTeX manuscript template to Word with Pandoc.

local refs = {}
local counters = { fig = 0, tab = 0, eq = 0 }
local styles = {
  title = "PaperTitle",
  author = "AuthorBlock",
  date = "PaperDate",
  abstract = "Abstract",
  keywords = "Keywords",
  body = "BodyText",
  figure_caption = "FigureCaption",
  table_caption = "TableCaption",
  equation = "EquationNumbered",
  references_heading = "ReferencesHeading",
  reference_item = "ReferenceItem",
  table_header = "TableHeader",
  table_body = "TableBody"
}

local function stringify(inlines)
  return pandoc.utils.stringify(inlines or {})
end

local function has_custom_style(attr)
  return attr and attr.attributes and attr.attributes["custom-style"]
end

local function stringify_meta(meta_value)
  local text = pandoc.utils.stringify(meta_value)
  return text:gsub("^%s+", ""):gsub("%s+$", "")
end

local function styled_div(blocks, style_name, identifier, classes, attributes)
  local attr = pandoc.Attr(identifier or "", classes or {}, attributes or {})
  attr.attributes["custom-style"] = style_name
  return pandoc.Div(blocks, attr)
end

local function styled_para(inlines, style_name)
  return styled_div({ pandoc.Para(inlines) }, style_name)
end

local function style_plain_or_para(block, style_name)
  if block.t == "Plain" then
    return styled_para(block.content, style_name)
  end
  if block.t == "Para" then
    return styled_para(block.content, style_name)
  end
  return styled_div({ block }, style_name)
end

local function meta_blocks(meta_value)
  if not meta_value then
    return {}
  end

  if meta_value.t == "MetaBlocks" then
    if meta_value.blocks then
      return meta_value.blocks
    end
    local text = stringify_meta(meta_value)
    return text ~= "" and { pandoc.Para({ pandoc.Str(text) }) } or {}
  end
  if meta_value.t == "MetaInlines" then
    return { pandoc.Para(meta_value) }
  end
  if meta_value.t == "MetaString" then
    return { pandoc.Para({ pandoc.Str(tostring(meta_value)) }) }
  end
  return {}
end

local function meta_inlines(meta_value)
  if not meta_value then
    return {}
  end
  if meta_value.t == "MetaInlines" then
    return meta_value
  end
  if meta_value.t == "MetaString" then
    return { pandoc.Str(tostring(meta_value)) }
  end
  local text = stringify_meta(meta_value)
  return text ~= "" and { pandoc.Str(text) } or {}
end

local function author_inlines(author_meta)
  if not author_meta then
    return {}
  end

  if author_meta.t == "MetaList" then
    local result = {}
    for i, author in ipairs(author_meta) do
      if i > 1 then
        table.insert(result, pandoc.Str(";"))
        table.insert(result, pandoc.Space())
      end
      for _, inline in ipairs(meta_inlines(author)) do
        table.insert(result, inline)
      end
    end
    return result
  end

  return meta_inlines(author_meta)
end

local function is_keywords_para(block)
  if block.t ~= "Para" and block.t ~= "Plain" then
    return false
  end
  if #block.content == 0 then
    return false
  end

  local first = block.content[1]
  if first.t == "Strong" then
    return stringify(first.content):match("^关键词") ~= nil
  end
  if first.t == "Str" then
    return first.text:match("^关键词") ~= nil
  end
  return false
end

local function style_cell_blocks(cell, style_name)
  local styled = {}

  for _, block in ipairs(cell.contents) do
    if block.t == "Plain" then
      table.insert(styled, styled_div({ pandoc.Plain(block.content) }, style_name))
    elseif block.t == "Para" then
      table.insert(styled, styled_div({ pandoc.Para(block.content) }, style_name))
    else
      table.insert(styled, block)
    end
  end

  cell.contents = styled
  return cell
end

local function style_table_row(row, style_name)
  for i, cell in ipairs(row.cells) do
    row.cells[i] = style_cell_blocks(cell, style_name)
  end
  return row
end

local function style_table(table_block)
  if table_block.head and table_block.head.rows then
    for i, row in ipairs(table_block.head.rows) do
      table_block.head.rows[i] = style_table_row(row, styles.table_header)
    end
  end

  for _, body in ipairs(table_block.bodies or {}) do
    for i, row in ipairs(body.body or {}) do
      body.body[i] = style_table_row(row, styles.table_body)
    end
    for i, row in ipairs(body.head or {}) do
      body.head[i] = style_table_row(row, styles.table_header)
    end
  end

  if table_block.foot and table_block.foot.rows then
    for i, row in ipairs(table_block.foot.rows) do
      table_block.foot.rows[i] = style_table_row(row, styles.table_body)
    end
  end

  return table_block
end

local function front_matter_blocks(meta)
  local blocks = {}

  local title = meta_inlines(meta.title)
  if #title > 0 then
    table.insert(blocks, styled_para(title, styles.title))
  end

  local authors = author_inlines(meta.author)
  if #authors > 0 then
    table.insert(blocks, styled_para(authors, styles.author))
  end

  local date = meta_inlines(meta.date)
  if #date > 0 then
    table.insert(blocks, styled_para(date, styles.date))
  end

  local abstract = meta_blocks(meta.abstract)
  for _, block in ipairs(abstract) do
    table.insert(blocks, style_plain_or_para(block, styles.abstract))
  end

  return blocks
end

local function ref_kind(id)
  if id:match("^fig:") then
    return "fig"
  end
  if id:match("^tab:") then
    return "tab"
  end
  if id:match("^eq:") then
    return "eq"
  end
  if id:match("^sec:") or id:match("^subsec:") or id:match("^subsubsec:") then
    return "sec"
  end
  return nil
end

local function starts_with_caption(caption_text, prefix)
  return caption_text == prefix or caption_text:match("^" .. prefix .. "%s")
end

local function caption_blocks(caption)
  if caption and caption.long then
    return caption.long
  end
  return {}
end

local function styled_caption(caption, style_name)
  local blocks = caption_blocks(caption)
  local styled = {}

  for _, block in ipairs(blocks) do
    table.insert(styled, style_plain_or_para(block, style_name))
  end

  caption.long = styled
  return caption
end

local function prefix_caption(caption, prefix)
  local blocks = caption_blocks(caption)
  if #blocks == 0 then
    caption.long = { pandoc.Plain({ pandoc.Str(prefix) }) }
    return caption
  end

  local first = blocks[1]
  if first.t ~= "Plain" and first.t ~= "Para" then
    table.insert(blocks, 1, pandoc.Plain({ pandoc.Str(prefix) }))
    caption.long = blocks
    return caption
  end

  if starts_with_caption(stringify(first.content), prefix) then
    return caption
  end

  local new_content = { pandoc.Str(prefix), pandoc.Space() }
  for _, inline in ipairs(first.content) do
    table.insert(new_content, inline)
  end
  first.content = new_content
  caption.long = blocks
  return caption
end

local function strip_equation_latex(math_text)
  local label = math_text:match("\\label%s*{%s*([^}]+)%s*}")
  local cleaned = math_text
  cleaned = cleaned:gsub("\\begin%s*{%s*equation%*?%s*}", "")
  cleaned = cleaned:gsub("\\end%s*{%s*equation%*?%s*}", "")
  cleaned = cleaned:gsub("\\label%s*{%s*[^}]+%s*}", "")
  cleaned = cleaned:gsub("^%s+", ""):gsub("%s+$", "")
  return cleaned, label
end

local function collect_blocks(blocks)
  for _, block in ipairs(blocks) do
    if block.t == "Figure" and block.identifier and block.identifier ~= "" then
      counters.fig = counters.fig + 1
      refs[block.identifier] = tostring(counters.fig)
    elseif block.t == "Div" and block.identifier and block.identifier:match("^tab:") then
      counters.tab = counters.tab + 1
      refs[block.identifier] = tostring(counters.tab)
    elseif block.t == "Table" and block.identifier and block.identifier:match("^tab:") then
      counters.tab = counters.tab + 1
      refs[block.identifier] = tostring(counters.tab)
    elseif block.t == "Para" and #block.content == 1 and block.content[1].t == "Math" then
      local math = block.content[1]
      if math.mathtype == "DisplayMath" then
        local _, label = strip_equation_latex(math.text)
        if label then
          counters.eq = counters.eq + 1
          refs[label] = tostring(counters.eq)
        end
      end
    end
  end
end

local function replace_ref_link(link)
  local target = link.attributes and link.attributes.reference
  if not target or not refs[target] then
    return nil
  end

  local kind = ref_kind(target)
  if kind == "eq" then
    return pandoc.Str("(" .. refs[target] .. ")")
  end
  return pandoc.Str(refs[target])
end

local function number_table(table_block, id)
  if id and refs[id] then
    table_block.caption = prefix_caption(table_block.caption, "表 " .. refs[id])
  end
  table_block.caption = styled_caption(table_block.caption, styles.table_caption)
  table_block = style_table(table_block)
  return table_block
end

local function equation_paragraph(math_text, number)
  local one_line_math = math_text:gsub("[\r\n]+", " ")
  return styled_div(
    {
      pandoc.Para({
      pandoc.RawInline("openxml", "<w:tab/>"),
      pandoc.Math("InlineMath", one_line_math),
      pandoc.RawInline("openxml", "<w:tab/>"),
      pandoc.Str("(" .. number .. ")")
      })
    },
    styles.equation
  )
end

local function style_references(div)
  local styled = {}

  for _, block in ipairs(div.content) do
    if block.t == "Div" and block.classes:includes("csl-entry") then
      local entry_blocks = {}
      for _, entry_block in ipairs(block.content) do
        table.insert(entry_blocks, style_plain_or_para(entry_block, styles.reference_item))
      end
      block.content = entry_blocks
      table.insert(styled, block)
    else
      table.insert(styled, block)
    end
  end

  div.content = styled
  return div
end

local function rewrite_blocks(blocks)
  local rewritten = {}

  for _, block in ipairs(blocks) do
    if block.t == "Figure" and block.identifier and refs[block.identifier] then
      block.caption = prefix_caption(block.caption, "图 " .. refs[block.identifier])
      block.caption = styled_caption(block.caption, styles.figure_caption)
      table.insert(rewritten, block)
    elseif block.t == "Div" and block.identifier and block.identifier:match("^tab:") then
      block = block:walk({
        Table = function(tbl)
          return number_table(tbl, block.identifier)
        end
      })
      table.insert(rewritten, block)
    elseif block.t == "Div" and block.identifier == "refs" then
      table.insert(rewritten, styled_para({ pandoc.Str("参考文献") }, styles.references_heading))
      table.insert(rewritten, style_references(block))
    elseif block.t == "Table" and block.identifier and block.identifier:match("^tab:") then
      table.insert(rewritten, number_table(block, block.identifier))
    elseif block.t == "Para" and #block.content == 1 and block.content[1].t == "Math" then
      local math = block.content[1]
      if math.mathtype == "DisplayMath" then
        local cleaned, label = strip_equation_latex(math.text)
        if label and refs[label] then
          table.insert(rewritten, equation_paragraph(cleaned, refs[label]))
        else
          table.insert(rewritten, block)
        end
      else
        table.insert(rewritten, style_plain_or_para(block, styles.body))
      end
    elseif is_keywords_para(block) then
      table.insert(rewritten, style_plain_or_para(block, styles.keywords))
    elseif block.t == "Para" or block.t == "Plain" then
      table.insert(rewritten, style_plain_or_para(block, styles.body))
    else
      table.insert(rewritten, block)
    end
  end

  return rewritten
end

function Pandoc(doc)
  collect_blocks(doc.blocks)
  doc.blocks = rewrite_blocks(doc.blocks)
  local front = front_matter_blocks(doc.meta)
  if #front > 0 then
    for i = #front, 1, -1 do
      table.insert(doc.blocks, 1, front[i])
    end
  end
  return doc:walk({ Link = replace_ref_link })
end
