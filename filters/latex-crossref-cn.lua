-- Add simple Chinese-style figure, table, and equation numbers when converting
-- this LaTeX manuscript template to Word with Pandoc.

local refs = {}
local counters = { fig = 0, tab = 0, eq = 0 }
local config = {
  normalize_cjk_ascii_spacing = false
}
local styles = {
  title = "LptPaperTitle",
  author = "LptAuthorBlock",
  date = "LptPaperDate",
  abstract = "LptAbstract",
  keywords = "LptKeywords",
  heading1 = "LptHeading1",
  heading2 = "LptHeading2",
  heading3 = "LptHeading3",
  body = "LptBodyText",
  figure_caption = "LptFigureCaption",
  table_caption = "LptTableCaption",
  equation = "LptEquationNumbered",
  references_heading = "LptReferencesHeading",
  reference_item = "LptReferenceItem",
  table_header = "LptTableHeader",
  table_body = "LptTableBody"
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

local function config_bool(meta, key, default)
  local value = meta and meta[key]
  if value == nil then
    return default
  end

  if type(value) == "boolean" then
    return value
  end

  local text = stringify_meta(value):lower()
  if text == "true" or text == "yes" or text == "1" or text == "on" then
    return true
  end
  if text == "false" or text == "no" or text == "0" or text == "off" then
    return false
  end

  return default
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

local function style_prefixed_plain_or_para(block, prefix, style_name)
  if block.t == "Plain" or block.t == "Para" then
    if stringify(block.content):match("^" .. prefix) then
      return style_plain_or_para(block, style_name)
    end

    local content = { pandoc.Strong({ pandoc.Str(prefix) }) }
    for _, inline in ipairs(block.content) do
      table.insert(content, inline)
    end
    return styled_para(content, style_name)
  end

  return styled_div({ block }, style_name)
end

local function style_header(block)
  local style_name = styles["heading" .. tostring(block.level)]
  if not style_name then
    return block
  end

  return styled_div(
    { pandoc.Para(block.content) },
    style_name,
    block.identifier,
    block.classes,
    block.attributes
  )
end

local function meta_blocks(meta_value)
  if not meta_value then
    return {}
  end

  local first = meta_value[1]
  if first and (first.t == "Plain" or first.t == "Para" or first.t == "Div") then
    return meta_value
  end
  if meta_value.t == "MetaBlocks" then
    return meta_value
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

local function author_separator()
  -- Pandoc's DOCX writer collapses ordinary CJK-adjacent spaces. NBSP keeps
  -- the visual author gap stable in Word.
  return pandoc.Str(string.rep("\194\160", 4))
end

local function author_inlines(author_meta)
  if not author_meta then
    return {}
  end

  if author_meta.t == "MetaList" or pandoc.utils.type(author_meta) == "List" then
    local result = {}
    for i, author in ipairs(author_meta) do
      if i > 1 then
        table.insert(result, author_separator())
      end
      for _, inline in ipairs(meta_inlines(author)) do
        table.insert(result, inline)
      end
    end
    return result
  end

  return meta_inlines(author_meta)
end

local function utf8_chars(text)
  local chars = {}
  local positions = {}

  for pos, codepoint in utf8.codes(text) do
    table.insert(positions, { pos = pos, codepoint = codepoint })
  end

  for i, item in ipairs(positions) do
    local next_pos = positions[i + 1] and positions[i + 1].pos or (#text + 1)
    table.insert(chars, {
      text = text:sub(item.pos, next_pos - 1),
      codepoint = item.codepoint
    })
  end

  return chars
end

local function is_spacing_codepoint(codepoint)
  return codepoint == 0x20 or codepoint == 0xA0
end

local function is_cjk_codepoint(codepoint)
  return
    (codepoint >= 0x3000 and codepoint <= 0x303F) or
    (codepoint >= 0x3400 and codepoint <= 0x4DBF) or
    (codepoint >= 0x4E00 and codepoint <= 0x9FFF) or
    (codepoint >= 0xF900 and codepoint <= 0xFAFF) or
    (codepoint >= 0xFF00 and codepoint <= 0xFFEF) or
    (codepoint >= 0x20000 and codepoint <= 0x2FA1F)
end

local function is_ascii_token_codepoint(codepoint)
  return codepoint > 0x20 and codepoint < 0x7F
end

local function boundary_kind_for_codepoint(codepoint)
  if is_cjk_codepoint(codepoint) then
    return "cjk"
  end
  if is_ascii_token_codepoint(codepoint) then
    return "ascii"
  end
  return nil
end

local function should_close_spacing(left_kind, right_kind)
  return
    (left_kind == "cjk" and right_kind == "ascii") or
    (left_kind == "ascii" and right_kind == "cjk")
end

local function first_text_boundary_kind(text)
  for _, char in ipairs(utf8_chars(text)) do
    if not is_spacing_codepoint(char.codepoint) then
      local kind = boundary_kind_for_codepoint(char.codepoint)
      if kind then
        return kind
      end
    end
  end
  return nil
end

local function last_text_boundary_kind(text)
  local chars = utf8_chars(text)

  for i = #chars, 1, -1 do
    local char = chars[i]
    if not is_spacing_codepoint(char.codepoint) then
      local kind = boundary_kind_for_codepoint(char.codepoint)
      if kind then
        return kind
      end
    end
  end
  return nil
end

local function normalize_cjk_text_spacing(text)
  local chars = utf8_chars(text)
  local kept = {}

  for i, char in ipairs(chars) do
    if is_spacing_codepoint(char.codepoint) then
      local left_kind = nil
      local right_kind = nil

      for j = i - 1, 1, -1 do
        if not is_spacing_codepoint(chars[j].codepoint) then
          left_kind = boundary_kind_for_codepoint(chars[j].codepoint)
          break
        end
      end

      for j = i + 1, #chars do
        if not is_spacing_codepoint(chars[j].codepoint) then
          right_kind = boundary_kind_for_codepoint(chars[j].codepoint)
          break
        end
      end

      if not should_close_spacing(left_kind, right_kind) then
        table.insert(kept, char.text)
      end
    else
      table.insert(kept, char.text)
    end
  end

  return table.concat(kept)
end

local function strip_leading_spacing(text)
  local chars = utf8_chars(text)
  local first_kept = 1

  while chars[first_kept] and is_spacing_codepoint(chars[first_kept].codepoint) do
    first_kept = first_kept + 1
  end

  local kept = {}
  for i = first_kept, #chars do
    table.insert(kept, chars[i].text)
  end
  return table.concat(kept)
end

local function strip_trailing_spacing(text)
  local chars = utf8_chars(text)
  local last_kept = #chars

  while chars[last_kept] and is_spacing_codepoint(chars[last_kept].codepoint) do
    last_kept = last_kept - 1
  end

  local kept = {}
  for i = 1, last_kept do
    table.insert(kept, chars[i].text)
  end
  return table.concat(kept)
end

local function inline_boundary_kind(inline, side)
  if inline.t == "Str" then
    if side == "first" then
      return first_text_boundary_kind(inline.text)
    end
    return last_text_boundary_kind(inline.text)
  end

  if inline.t == "Math" or inline.t == "Code" then
    return "ascii"
  end

  local text = pandoc.utils.stringify(inline)
  if side == "first" then
    return first_text_boundary_kind(text)
  end
  return last_text_boundary_kind(text)
end

local function is_spacing_inline(inline)
  if inline.t == "Space" then
    return true
  end

  if inline.t ~= "Str" then
    return false
  end

  local chars = utf8_chars(inline.text)
  if #chars == 0 then
    return false
  end

  for _, char in ipairs(chars) do
    if not is_spacing_codepoint(char.codepoint) then
      return false
    end
  end

  return true
end

local function adjacent_boundary_kind(inlines, index, step)
  local side = step > 0 and "first" or "last"
  local i = index + step

  while inlines[i] do
    local kind = inline_boundary_kind(inlines[i], side)
    if kind then
      return kind
    end
    i = i + step
  end

  return nil
end

local function trim_str_inline_boundary_spacing(inlines)
  for i, inline in ipairs(inlines) do
    if inline.t == "Str" then
      local first_kind = first_text_boundary_kind(inline.text)
      local last_kind = last_text_boundary_kind(inline.text)
      local prev_kind = adjacent_boundary_kind(inlines, i, -1)
      local next_kind = adjacent_boundary_kind(inlines, i, 1)

      if should_close_spacing(prev_kind, first_kind) then
        inline.text = strip_leading_spacing(inline.text)
      end
      if should_close_spacing(last_kind, next_kind) then
        inline.text = strip_trailing_spacing(inline.text)
      end
    end
  end

  return inlines
end

local function normalize_cjk_spacing(inlines)
  local normalized = {}

  for _, inline in ipairs(inlines) do
    if inline.t == "Str" then
      inline.text = normalize_cjk_text_spacing(inline.text)
      if inline.text ~= "" then
        table.insert(normalized, inline)
      end
    else
      table.insert(normalized, inline)
    end
  end

  normalized = trim_str_inline_boundary_spacing(normalized)

  local result = {}

  for i, inline in ipairs(normalized) do
    if is_spacing_inline(inline) then
      local left_kind = adjacent_boundary_kind(normalized, i, -1)
      local right_kind = adjacent_boundary_kind(normalized, i, 1)

      if not should_close_spacing(left_kind, right_kind) then
        table.insert(result, inline)
      end
    else
      table.insert(result, inline)
    end
  end

  return result
end

local function normalize_blocks_spacing(blocks)
  local normalized = {}

  for _, block in ipairs(blocks) do
    if block.t == "Div" and has_custom_style(block) == styles.author then
      table.insert(normalized, block)
    else
      table.insert(normalized, block:walk({ Inlines = normalize_cjk_spacing }))
    end
  end

  return normalized
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
  for i, block in ipairs(abstract) do
    if i == 1 then
      table.insert(blocks, style_prefixed_plain_or_para(block, "摘要：", styles.abstract))
    else
      table.insert(blocks, style_plain_or_para(block, styles.abstract))
    end
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
      pandoc.RawInline("openxml", "<w:r><w:tab/></w:r>"),
      pandoc.Math("InlineMath", one_line_math),
      pandoc.RawInline("openxml", "<w:r><w:tab/></w:r>"),
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
    elseif block.t == "Header" then
      table.insert(rewritten, style_header(block))
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
    doc.meta.title = nil
    doc.meta.author = nil
    doc.meta.date = nil
    doc.meta.abstract = nil
  end
  doc = doc:walk({ Link = replace_ref_link })
  if config_bool(doc.meta, "lpt-normalize-cjk-ascii-spacing", config.normalize_cjk_ascii_spacing) then
    doc.blocks = normalize_blocks_spacing(doc.blocks)
  end
  return doc
end
