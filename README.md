# nvim-autotheme

_\*README generated with AI_
Automatically sync your Neovim colorscheme with your wallpaper using **matugen + systemd**.

## ✨ Features

- 🎨 Colors generated from your current wallpaper
- 🔄 Automatic updates via systemd user service
- 🧠 Separate UI + syntax color layers
- ⚡ Works seamlessly with Neovim colorschemes

## ⚠️ Requirements

- Linux (systemd user services required)
- Neovim
- matugen
- **End-4 dotfiles** (this setup is designed specifically for them)

## 📦 Installation

```bash
git clone https://github.com/yourname/matugen-nvim
cd matugen-nvim
./install.sh
```

This will:

- Install scripts to `~/.local/bin`
- Install systemd user units
- Enable automatic color regeneration
- Install the `matugen` Neovim colorscheme

## 🧠 How it works

1. Your wallpaper changes
2. matugen generates a new palette
3. systemd detects the change
4. `derive-nvim-syntax-colors` runs
5. Neovim colors are regenerated
6. Next time Neovim loads the colorscheme → it's updated

## 🎯 Usage

In Neovim:

```vim
:colorscheme matugen
```

## ⚡ Recommended (optional)

Auto-reload colors when returning to Neovim:

```lua
vim.api.nvim_create_autocmd("FocusGained", {
  callback = function()
    vim.cmd("checktime")
  end,
})
```

Manual reload command:

```lua
vim.api.nvim_create_user_command("MatugenReload", function()
  vim.cmd.colorscheme("matugen")
end, {})
```

## 📁 Structure

```
bin/        → scripts
systemd/    → user services
nvim/       → colorscheme
```

## 🚧 Notes

This setup is tightly coupled to **End-4 dotfiles** and may not work out-of-the-box with other configurations.

## 📜 License

MIT

```

```
