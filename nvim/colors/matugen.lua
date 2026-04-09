-- ~/.config/nvim/colors/matugen.lua
--
-- Two-layer color scheme:
--   Syntax highlighting → derived from kitty ANSI palette (perceptually uniform)
--   UI chrome           → MD3 tokens from matugen (surface/container hierarchy)
--
-- Requires:
--   matugen/colors.lua         (MD3 tokens, written by matugen template)
--   matugen/syntax_colors.lua  (derived palette, written by derive_syntax_colors.py)

local M = {}

function M.load()
	-- Load MD3 tokens for UI chrome (surfaces, containers, borders)
	local ok_md3, md3 = pcall(require, "matugen.colors")
	if not ok_md3 then
		vim.notify("[matugen] colors.lua not found — run matugen first", vim.log.levels.WARN)
		return false
	end

	-- Load derived syntax palette (from kitty-theme.conf)
	local ok_syn, syn = pcall(require, "matugen.syntax_colors")
	if not ok_syn then
		vim.notify("[matugen] syntax_colors.lua not found — run derive-nvim-syntax-colors", vim.log.levels.WARN)
		return false
	end

	-- Force re-read on next colorscheme load (so hot-reload works)
	package.loaded["matugen.colors"] = nil
	package.loaded["matugen.syntax_colors"] = nil

	vim.cmd("highlight clear")
	if vim.fn.exists("syntax_on") == 1 then
		vim.cmd("syntax reset")
	end
	vim.g.colors_name = "matugen"

	local hl = function(group, opts)
		vim.api.nvim_set_hl(0, group, opts)
	end

	-- ── Design rules ────────────────────────────────────────────────────────
	-- ONLY comments are italic
	-- bold = structural importance (keywords, function defs)
	-- Syntax colors come from `syn` (perceptually uniform, derived from kitty)
	-- UI colors come from `md3` (Material Design surface hierarchy)

	-- ── Base ────────────────────────────────────────────────────────────────
	-- Background/foreground from kitty (so nvim matches the terminal exactly)
	hl("Normal", { fg = syn.fg, bg = syn.bg })
	hl("NormalNC", { fg = syn.param, bg = syn.surface_1 })
	hl("NormalFloat", { fg = syn.fg, bg = syn.surface_2 })

	hl("LineNr", { fg = syn.comment })
	hl("CursorLineNr", { fg = syn.keyword, bold = true })
	hl("CursorLine", { bg = syn.surface_3 })
	hl("ColorColumn", { bg = syn.surface_1 })
	hl("SignColumn", { fg = syn.comment, bg = syn.bg })

	hl("Visual", { bg = syn.sel_bg, fg = syn.sel_fg })
	hl("Search", { fg = syn.bg, bg = syn.keyword })
	hl("IncSearch", { fg = syn.bg, bg = syn.func, bold = true })
	hl("Substitute", { fg = syn.bg, bg = syn.string })

	hl("Comment", { fg = syn.comment, italic = true })
	hl("Conceal", { fg = syn.punctuation })
	hl("MatchParen", { fg = syn.func, bold = true, underline = true })

	-- ── Syntax ──────────────────────────────────────────────────────────────
	hl("Keyword", { fg = syn.keyword, bold = true })
	hl("Conditional", { fg = syn.keyword, bold = true })
	hl("Repeat", { fg = syn.keyword, bold = true })
	hl("Statement", { fg = syn.keyword, bold = true })
	hl("Exception", { fg = syn.keyword, bold = true })
	hl("Operator", { fg = syn.operator })

	hl("Function", { fg = syn.func, bold = true })
	hl("Identifier", { fg = syn.variable })

	hl("String", { fg = syn.string })
	hl("Character", { fg = syn.string })

	hl("Number", { fg = syn.number })
	hl("Float", { fg = syn.number })
	hl("Boolean", { fg = syn.keyword })

	hl("Type", { fg = syn.type })
	hl("StorageClass", { fg = syn.keyword, bold = true })
	hl("Structure", { fg = syn.type })
	hl("Typedef", { fg = syn.type })

	hl("PreProc", { fg = syn.preproc })
	hl("Include", { fg = syn.preproc })
	hl("Define", { fg = syn.preproc })
	hl("Macro", { fg = syn.preproc })

	hl("Special", { fg = syn.func_call })
	hl("Delimiter", { fg = syn.punctuation })
	hl("Error", { fg = syn.error })
	hl("Todo", { fg = syn.bg, bg = syn.keyword, bold = true })

	-- ── Treesitter ──────────────────────────────────────────────────────────
	hl("@keyword", { fg = syn.keyword, bold = true })
	hl("@keyword.function", { fg = syn.keyword, bold = true })
	hl("@keyword.return", { fg = syn.keyword, bold = true })
	hl("@keyword.operator", { fg = syn.operator })
	hl("@keyword.import", { fg = syn.preproc })

	hl("@function", { fg = syn.func, bold = true })
	hl("@function.call", { fg = syn.func_call })
	hl("@function.builtin", { fg = syn.func_call })
	hl("@function.macro", { fg = syn.preproc })
	hl("@method", { fg = syn.func, bold = true })
	hl("@method.call", { fg = syn.func_call })
	hl("@constructor", { fg = syn.type })

	hl("@variable", { fg = syn.variable })
	hl("@variable.builtin", { fg = syn.keyword })
	hl("@parameter", { fg = syn.param })
	hl("@field", { fg = syn.field })
	hl("@property", { fg = syn.field })

	hl("@type", { fg = syn.type })
	hl("@type.builtin", { fg = syn.type })
	hl("@type.qualifier", { fg = syn.keyword, bold = true })

	hl("@string", { fg = syn.string })
	hl("@string.escape", { fg = syn.number })
	hl("@number", { fg = syn.number })
	hl("@float", { fg = syn.number })
	hl("@boolean", { fg = syn.keyword })

	hl("@comment", { fg = syn.comment, italic = true })
	hl("@operator", { fg = syn.operator })
	hl("@punctuation.delimiter", { fg = syn.punctuation })
	hl("@punctuation.bracket", { fg = syn.operator })

	hl("@namespace", { fg = syn.keyword_dim })
	hl("@include", { fg = syn.preproc })
	hl("@preproc", { fg = syn.preproc })
	hl("@attribute", { fg = syn.preproc })

	hl("@constant", { fg = syn.constant })
	hl("@constant.builtin", { fg = syn.keyword })
	hl("@constant.macro", { fg = syn.preproc })
	hl("@label", { fg = syn.keyword })

	-- ── LSP semantic tokens ─────────────────────────────────────────────────
	hl("@lsp.type.function", { fg = syn.func, bold = true })
	hl("@lsp.type.method", { fg = syn.func, bold = true })
	hl("@lsp.type.variable", { fg = syn.variable })
	hl("@lsp.type.parameter", { fg = syn.param })
	hl("@lsp.type.keyword", { fg = syn.keyword, bold = true })
	hl("@lsp.type.type", { fg = syn.type })
	hl("@lsp.type.class", { fg = syn.type })
	hl("@lsp.type.namespace", { fg = syn.keyword_dim })
	hl("@lsp.type.macro", { fg = syn.preproc })
	hl("@lsp.type.enumMember", { fg = syn.constant })
	hl("@lsp.type.struct", { fg = syn.type })
	hl("@lsp.type.interface", { fg = syn.type })
	hl("@lsp.type.typeParameter", { fg = syn.type })
	hl("@lsp.type.decorator", { fg = syn.preproc })
	hl("@lsp.type.property", { fg = syn.field })

	-- ── UI chrome (MD3 surfaces still make sense here) ──────────────────────
	hl("StatusLine", { fg = syn.param, bg = syn.bg })
	hl("StatusLineNC", { fg = syn.comment, bg = syn.bg })
	hl("WinSeparator", { fg = syn.surface_3 })

	hl("TabLine", { fg = syn.param, bg = syn.surface_1 })
	hl("TabLineSel", { fg = syn.bg, bg = syn.keyword, bold = true })
	hl("TabLineFill", { bg = syn.bg })

	hl("Pmenu", { fg = syn.fg, bg = syn.surface_2 })
	hl("PmenuSel", { fg = syn.bg, bg = syn.keyword })
	hl("PmenuSbar", { bg = syn.surface_1 })
	hl("PmenuThumb", { bg = syn.keyword })

	hl("FloatBorder", { fg = syn.surface_sel, bg = syn.surface_2 })
	hl("FloatTitle", { fg = syn.keyword, bold = true })

	hl("Folded", { fg = syn.param, bg = syn.surface_1 })
	hl("FoldColumn", { fg = syn.comment, bg = syn.bg })

	-- ── Diagnostics ─────────────────────────────────────────────────────────
	hl("DiagnosticError", { fg = syn.error })
	hl("DiagnosticWarn", { fg = syn.warning })
	hl("DiagnosticInfo", { fg = syn.info })
	hl("DiagnosticHint", { fg = syn.hint })
	hl("DiagnosticVirtualTextError", { fg = syn.error, italic = true })
	hl("DiagnosticVirtualTextWarn", { fg = syn.warning, italic = true })
	hl("DiagnosticVirtualTextInfo", { fg = syn.info, italic = true })
	hl("DiagnosticVirtualTextHint", { fg = syn.hint, italic = true })
	hl("DiagnosticUnderlineError", { undercurl = true, sp = syn.error })
	hl("DiagnosticUnderlineWarn", { undercurl = true, sp = syn.warning })
	hl("DiagnosticUnderlineInfo", { undercurl = true, sp = syn.info })
	hl("DiagnosticUnderlineHint", { undercurl = true, sp = syn.comment })

	-- ── Git / Diff ──────────────────────────────────────────────────────────
	-- Use MD3 containers here if available, fall back to derived surfaces
	local diff_add_bg = md3.secondary_container or syn.surface_2
	local diff_del_bg = md3.error_container or syn.surface_2

	hl("DiffAdd", { bg = diff_add_bg })
	hl("DiffChange", { bg = syn.surface_3 })
	hl("DiffDelete", { fg = syn.error, bg = diff_del_bg })
	hl("DiffText", { fg = syn.bg, bg = syn.keyword, bold = true })

	hl("GitSignsAdd", { fg = syn.constant })
	hl("GitSignsChange", { fg = syn.warning })
	hl("GitSignsDelete", { fg = syn.error })

	-- ── Navic (breadcrumbs) ─────────────────────────────────────────────────
	hl("NavicText", { fg = syn.param, bg = syn.bg })
	hl("NavicSeparator", { fg = syn.punctuation, bg = syn.bg })
	hl("NavicIconsFunction", { fg = syn.func, bg = syn.bg })
	hl("NavicIconsMethod", { fg = syn.func, bg = syn.bg })
	hl("NavicIconsClass", { fg = syn.type, bg = syn.bg })
	hl("NavicIconsStruct", { fg = syn.type, bg = syn.bg })
	hl("NavicIconsEnum", { fg = syn.type, bg = syn.bg })
	hl("NavicIconsInterface", { fg = syn.type, bg = syn.bg })
	hl("NavicIconsVariable", { fg = syn.variable, bg = syn.bg })
	hl("NavicIconsField", { fg = syn.field, bg = syn.bg })
	hl("NavicIconsProperty", { fg = syn.field, bg = syn.bg })
	hl("NavicIconsConstant", { fg = syn.constant, bg = syn.bg })
	hl("NavicIconsString", { fg = syn.string, bg = syn.bg })
	hl("NavicIconsNumber", { fg = syn.number, bg = syn.bg })
	hl("NavicIconsBoolean", { fg = syn.keyword, bg = syn.bg })
	hl("NavicIconsNamespace", { fg = syn.keyword_dim, bg = syn.bg })
	hl("NavicIconsModule", { fg = syn.keyword_dim, bg = syn.bg })
	hl("NavicIconsPackage", { fg = syn.keyword_dim, bg = syn.bg })
	hl("NavicIconsFile", { fg = syn.keyword_dim, bg = syn.bg })
	hl("NavicIconsConstructor", { fg = syn.type, bg = syn.bg })
	hl("NavicIconsParameter", { fg = syn.param, bg = syn.bg })
	hl("NavicIconsEvent", { fg = syn.func_call, bg = syn.bg })
	hl("NavicIconsOperator", { fg = syn.operator, bg = syn.bg })
	hl("NavicIconsKey", { fg = syn.keyword, bg = syn.bg })
	hl("NavicIconsNull", { fg = syn.comment, bg = syn.bg })
	hl("NavicIconsTypeParameter", { fg = syn.type, bg = syn.bg })
	hl("NavicIconsEnumMember", { fg = syn.constant, bg = syn.bg })
	hl("NavicIconsObject", { fg = syn.type, bg = syn.bg })
	hl("NavicIconsArray", { fg = syn.keyword, bg = syn.bg })

	return true
end

M.load()
return M
