return {
	"nvim-lualine/lualine.nvim",
	opts = function(_, opts)
		opts.options = opts.options or {}
		opts.options.section_separators = { left = "", right = "" }
		opts.options.component_separators = { left = "", right = "" }
		opts.options.globalstatus = true

		-- Use a function so lualine theme reloads dynamically
		opts.options.theme = function()
			local c = require("matugen.syntax_colors") -- auto-generated colors

			-- Backgrounds for the bar
			local bg = c.bg -- main editor background
			local gap_bg = c.surface_1 -- edge/gap sections
			local b_bg = c.surface_2 -- middle sections, slightly lighter

			return {
				normal = {
					a = { fg = bg, bg = c.constant, gui = "bold" },
					b = { fg = c.fg, bg = b_bg },
					c = { fg = c.fg, bg = gap_bg },
					x = { fg = c.fg, bg = gap_bg },
					y = { fg = c.fg, bg = b_bg },
					z = { fg = bg, bg = c.constant, gui = "bold" },
				},
				insert = {
					a = { fg = bg, bg = c.func, gui = "bold" },
					b = { fg = c.fg, bg = b_bg },
					c = { fg = c.fg, bg = gap_bg },
					x = { fg = c.fg, bg = gap_bg },
					y = { fg = c.fg, bg = b_bg },
					z = { fg = bg, bg = c.func, gui = "bold" },
				},
				visual = {
					a = { fg = bg, bg = c.keyword, gui = "bold" },
					b = { fg = c.fg, bg = b_bg },
					c = { fg = c.fg, bg = gap_bg },
					x = { fg = c.fg, bg = gap_bg },
					y = { fg = c.fg, bg = b_bg },
					z = { fg = bg, bg = c.keyword, gui = "bold" },
				},
				replace = {
					a = { fg = bg, bg = c.error, gui = "bold" },
					b = { fg = c.fg, bg = b_bg },
					c = { fg = c.fg, bg = gap_bg },
					x = { fg = c.fg, bg = gap_bg },
					y = { fg = c.fg, bg = b_bg },
					z = { fg = bg, bg = c.error, gui = "bold" },
				},
				command = {
					a = { fg = bg, bg = c.warning, gui = "bold" },
					b = { fg = c.fg, bg = b_bg },
					c = { fg = c.fg, bg = gap_bg },
					x = { fg = c.fg, bg = gap_bg },
					y = { fg = c.fg, bg = b_bg },
					z = { fg = bg, bg = c.warning, gui = "bold" },
				},
				inactive = {
					a = { fg = c.comment, bg = gap_bg },
					b = { fg = c.comment, bg = gap_bg },
					c = { fg = c.comment, bg = gap_bg },
					x = { fg = c.comment, bg = gap_bg },
					y = { fg = c.comment, bg = gap_bg },
					z = { fg = c.comment, bg = gap_bg },
				},
			}
		end

		return opts
	end,
}
