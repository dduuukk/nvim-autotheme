#!/usr/bin/env bash

set -e

echo "Installing matugen-nvim..."

# scripts
mkdir -p ~/.local/bin
cp bin/* ~/.local/bin/
chmod +x ~/.local/bin/derive-nvim-syntax-colors

# systemd
mkdir -p ~/.config/systemd/user
cp systemd/* ~/.config/systemd/user/

systemctl --user daemon-reload
systemctl --user enable --now nvim-syntax-colors.path

# nvim
mkdir -p ~/.config/nvim/colors
cp nvim/colors/matugen.lua ~/.config/nvim/colors/

echo "Done!"
