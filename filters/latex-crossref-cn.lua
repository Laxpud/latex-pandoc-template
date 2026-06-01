-- Add simple Chinese-style figure, table, and equation numbers when converting
-- this LaTeX manuscript template to Word with Pandoc.

local refs = {}
local counters = { fig = 0, tab = 0, eq = 0 }

local function stringify(inlines)
  return pandoc.utils.stringify(inlines or {})
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
  return table_block
end

local function equation_paragraph(math_text, number)
  local one_line_math = math_text:gsub("[\r\n]+", " ")
  return pandoc.Div(
    {
      pandoc.Para({
      pandoc.RawInline("openxml", "<w:tab/>"),
      pandoc.Math("InlineMath", one_line_math),
      pandoc.RawInline("openxml", "<w:tab/>"),
      pandoc.Str("(" .. number .. ")")
      })
    },
    pandoc.Attr("", {}, { ["custom-style"] = "EquationNumbered" })
  )
end

local function rewrite_blocks(blocks)
  local rewritten = {}

  for _, block in ipairs(blocks) do
    if block.t == "Figure" and block.identifier and refs[block.identifier] then
      block.caption = prefix_caption(block.caption, "图 " .. refs[block.identifier])
      table.insert(rewritten, block)
    elseif block.t == "Div" and block.identifier and block.identifier:match("^tab:") then
      block = block:walk({
        Table = function(tbl)
          return number_table(tbl, block.identifier)
        end
      })
      table.insert(rewritten, block)
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
        table.insert(rewritten, block)
      end
    else
      table.insert(rewritten, block)
    end
  end

  return rewritten
end

function Pandoc(doc)
  collect_blocks(doc.blocks)
  doc.blocks = rewrite_blocks(doc.blocks)
  return doc:walk({ Link = replace_ref_link })
end
