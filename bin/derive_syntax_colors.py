#!/usr/bin/env python3
"""
derive_syntax_colors.py

Reads a Quickshell-generated kitty-theme.conf, extracts hue identity from the
ANSI color palette, then derives a perceptually-uniform syntax color palette
suitable for Neovim syntax highlighting.

Pipeline: kitty-theme.conf → parse ANSI colors → OKLCH decomposition →
          re-project at uniform lightness/chroma → emit Lua table

Color space chain:  sRGB hex → linear RGB → CIE XYZ D65 → Oklab → OKLCH

Why OKLCH?
  OKLCH separates lightness (L), colorfulness (C), and hue (H) in a way that
  matches human perception. Two colors at the same L actually *look* equally
  bright — unlike HSL where L=50% yellow is blinding but L=50% blue is dim.
  This is what lets us stamp out syntax colors that are all equally readable.
"""

import json
import math
import sys
import os
import re

# ═══════════════════════════════════════════════════════════════════════════
# Color space math
# ═══════════════════════════════════════════════════════════════════════════


def hex_to_srgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def srgb_to_linear(c):
    """sRGB gamma decode. sRGB uses ~gamma 2.2 with a linear segment near 0.
    Must undo this before matrix transforms — XYZ/Oklab are linear spaces."""
    return tuple(
        (x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c
    )


def linear_to_srgb(c):
    return tuple(
        (12.92 * x) if x <= 0.0031308 else (1.055 * x ** (1 / 2.4) - 0.055) for x in c
    )


def linear_rgb_to_xyz(rgb):
    r, g, b = rgb
    return (
        0.4124564 * r + 0.3575761 * g + 0.1804375 * b,
        0.2126729 * r + 0.7151522 * g + 0.0721750 * b,
        0.0193339 * r + 0.1191920 * g + 0.9503041 * b,
    )


def xyz_to_oklab(xyz):
    x, y, z = xyz
    l_ = 0.8189330101 * x + 0.3618667424 * y - 0.1288597137 * z
    m_ = 0.0329845436 * x + 0.9293118715 * y + 0.0361456387 * z
    s_ = 0.0482003018 * x + 0.2643662691 * y + 0.6338517070 * z
    l_ = math.copysign(abs(l_) ** (1 / 3), l_) if l_ != 0 else 0
    m_ = math.copysign(abs(m_) ** (1 / 3), m_) if m_ != 0 else 0
    s_ = math.copysign(abs(s_) ** (1 / 3), s_) if s_ != 0 else 0
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def oklab_to_xyz(lab):
    L, a, b = lab
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    return (
        1.2270138511 * (l_**3) - 0.5577999807 * (m_**3) + 0.2812561490 * (s_**3),
        -0.0405801784 * (l_**3) + 1.1122568696 * (m_**3) - 0.0716766787 * (s_**3),
        -0.0763812845 * (l_**3) - 0.4214819784 * (m_**3) + 1.5861632204 * (s_**3),
    )


def xyz_to_linear_rgb(xyz):
    x, y, z = xyz
    return (
        3.2404542 * x - 1.5371385 * y - 0.4985314 * z,
        -0.9692660 * x + 1.8760108 * y + 0.0415560 * z,
        0.0556434 * x - 0.2040259 * y + 1.0572252 * z,
    )


def hex_to_oklch(h):
    return oklab_to_oklch(
        xyz_to_oklab(linear_rgb_to_xyz(srgb_to_linear(hex_to_srgb(h))))
    )


def oklab_to_oklch(lab):
    L, a, b = lab
    return (L, math.sqrt(a * a + b * b), math.degrees(math.atan2(b, a)) % 360)


def oklch_to_oklab(lch):
    L, C, H = lch
    return (L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H)))


def oklch_to_hex(lch):
    """OKLCH → hex with gamut mapping. If the color falls outside sRGB,
    progressively reduce chroma (saturation) while keeping L and H fixed.
    This is the correct way to gamut-map: you never shift the hue or brightness,
    you just desaturate until it fits the display."""
    L, C, H = lch
    for _ in range(64):
        lab = oklch_to_oklab((L, C, H))
        xyz = oklab_to_xyz(lab)
        lin = xyz_to_linear_rgb(xyz)
        if all(-0.002 <= x <= 1.002 for x in lin):
            srgb = linear_to_srgb(tuple(max(0.0, min(1.0, x)) for x in lin))
            return "#{:02x}{:02x}{:02x}".format(*(int(round(x * 255)) for x in srgb))
        C *= 0.95
    # Fallback: achromatic
    lab = oklch_to_oklab((L, 0, 0))
    xyz = oklab_to_xyz(lab)
    lin = xyz_to_linear_rgb(xyz)
    srgb = linear_to_srgb(tuple(max(0.0, min(1.0, x)) for x in lin))
    return "#{:02x}{:02x}{:02x}".format(*(int(round(x * 255)) for x in srgb))


# ═══════════════════════════════════════════════════════════════════════════
# Kitty config parser
# ═══════════════════════════════════════════════════════════════════════════


def parse_kitty_conf(path):
    """Parse key-value pairs from a kitty theme conf file.
    Kitty uses '#' for both hex colors and line comments.
    A comment '#' only appears after the value or at line start."""
    colors = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Split into tokens, find key and hex value
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0]
                val = parts[1]
                if val.startswith("#") and len(val) == 7:
                    colors[key] = val.upper()
    return colors


# ═══════════════════════════════════════════════════════════════════════════
# Hue extraction and gap-filling
# ═══════════════════════════════════════════════════════════════════════════


def angular_distance(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def fill_hue_gaps(hues, target_count=10, min_gap=28):
    """Bisect the largest arc on the hue wheel until we have enough colors.
    Keeps the original 'identity' hues as anchors and fills in between."""
    hues = sorted(set(round(h, 1) for h in hues))

    for _ in range(20):
        if len(hues) >= target_count:
            break
        sorted_h = sorted(hues)
        # Compute gaps (including the wrap-around gap)
        gaps = []
        for i in range(len(sorted_h)):
            a = sorted_h[i]
            b = sorted_h[(i + 1) % len(sorted_h)]
            gap = (b - a) % 360
            mid = (a + gap / 2) % 360
            gaps.append((gap, mid))
        gaps.sort(key=lambda x: -x[0])
        best_gap, best_mid = gaps[0]
        if best_gap < min_gap * 2:
            break
        if all(angular_distance(best_mid, h) >= min_gap for h in hues):
            hues.append(round(best_mid, 1))
            hues = sorted(hues)
    return hues


# ═══════════════════════════════════════════════════════════════════════════
# Palette derivation
# ═══════════════════════════════════════════════════════════════════════════


def derive_palette(kitty_colors):
    """Core algorithm:
    1. Read bg/fg from kitty for base colors
    2. Decompose ANSI colors 1-6 (the chromatic ones) into OKLCH
    3. Extract their hue angles — these define the theme's color identity
    4. Fill gaps on the hue wheel to get enough distinct syntax hues
    5. Re-project each hue at multiple lightness levels:
       - 'normal':  L ≈ 0.78, C ≈ 0.10  (most syntax tokens)
       - 'bright':  L ≈ 0.84, C ≈ 0.12  (keywords, emphasis)
       - 'dim':     L ≈ 0.62, C ≈ 0.06  (comments, punctuation)
       - 'vivid':   L ≈ 0.72, C ≈ 0.18  (strings, numbers — need to pop)
    """
    bg_hex = kitty_colors.get("background", "#1D191F")
    fg_hex = kitty_colors.get("foreground", "#ECD1D7")
    bg_L, _, _ = hex_to_oklch(bg_hex)

    # ── Step 1: Extract hues from the chromatic ANSI colors ──
    # color0 = black (bg), color7 = white (fg) — skip those
    # color1-6 are the actual chromatic colors
    ansi_sources = {}
    for i in range(1, 7):
        key = f"color{i}"
        if key in kitty_colors:
            L, C, H = hex_to_oklch(kitty_colors[key])
            ansi_sources[key] = {"hex": kitty_colors[key], "L": L, "C": C, "H": H}

    print(f"\n{'=' * 60}")
    print(f"Background: {bg_hex}  (OKLCH L={bg_L:.3f})")
    print(f"Foreground: {fg_hex}")
    print(f"\nANSI color analysis:")
    print(f"{'color':<10} {'hex':<10} {'L':>6} {'C':>6} {'H':>7}")
    print(f"{'-' * 45}")

    source_hues = []
    for name, info in sorted(ansi_sources.items()):
        print(
            f"{name:<10} {info['hex']:<10} {info['L']:6.3f} {info['C']:6.3f} {info['H']:7.1f}°"
        )
        # Only use colors with meaningful chroma (skip near-greys)
        if info["C"] > 0.03:
            source_hues.append(info["H"])

    # ── Step 2: Fill hue gaps ──
    all_hues = fill_hue_gaps(source_hues, target_count=10)

    print(f"\nSource hues: {[f'{h:.0f}°' for h in sorted(source_hues)]}")
    print(f"Filled hues: {[f'{h:.0f}°' for h in all_hues]}")

    # ── Step 3: Determine lightness targets based on background ──
    # Adaptive: if bg is very dark (L < 0.22), push syntax colors brighter.
    # If bg is medium-dark (0.22-0.35), pull them down slightly.
    if bg_L < 0.22:
        targets = {
            "bright": (0.84, 0.13),  # keywords, function defs
            "normal": (0.78, 0.10),  # types, variables
            "muted": (0.72, 0.08),  # params, properties, operators
            "vivid": (0.74, 0.17),  # strings, numbers (high chroma = pop)
            "dim": (0.58, 0.05),  # comments, punctuation
        }
    else:
        # Slightly pulled down for lighter dark themes
        targets = {
            "bright": (0.80, 0.12),
            "normal": (0.74, 0.09),
            "muted": (0.68, 0.07),
            "vivid": (0.70, 0.16),
            "dim": (0.54, 0.04),
        }

    # ── Step 4: Assign hues to semantic roles ──
    # Strategy: pick the closest available hue to the original ANSI color's
    # semantic meaning, then assign remaining hues to fill roles.

    # Find which of our filled hues is closest to each ANSI source hue
    def closest_hue(target_h, hue_list):
        return min(hue_list, key=lambda h: angular_distance(h, target_h))

    # Map ANSI semantics to our hue pool
    # color1=red/magenta, color2=green(ish), color4=blue, color5=magenta, color6=cyan
    ansi_hue_map = {}
    for name, info in ansi_sources.items():
        if info["C"] > 0.03:
            ansi_hue_map[name] = closest_hue(info["H"], all_hues)

    # Now build the semantic syntax palette
    # We need hues for: keyword, function, string, number, type, variable,
    #                    param, comment, constant, preproc, error

    # Sort hues for deterministic assignment
    available = sorted(all_hues)

    def pick_hue_near(target_angle):
        """Pick the available hue nearest to a target angle."""
        return min(available, key=lambda h: angular_distance(h, target_angle))

    # Use ANSI hues to anchor the most important roles
    # color4 (blue-ish) → keywords (typically blue in most themes)
    # color1 (red/magenta) → functions
    # color2 (warm) → strings
    # color5 (purple) → types
    # color6 (cyan) → constants

    c4_h = ansi_sources.get("color4", {}).get("H", 230)
    c1_h = ansi_sources.get("color1", {}).get("H", 330)
    c2_h = ansi_sources.get("color2", {}).get("H", 15)
    c5_h = ansi_sources.get("color5", {}).get("H", 300)
    c6_h = ansi_sources.get("color6", {}).get("H", 210)

    # Build the palette
    palette = {}

    # -- Background and foreground from kitty directly --
    palette["bg"] = bg_hex.lower()
    palette["fg"] = fg_hex.lower()

    # -- Generate a subtle surface hierarchy from the bg --
    # Lift the bg lightness slightly for surfaces, keeping the same hue/chroma
    bg_full = hex_to_oklch(bg_hex)
    palette["surface_0"] = oklch_to_hex((bg_full[0], bg_full[1], bg_full[2]))
    palette["surface_1"] = oklch_to_hex(
        (bg_full[0] + 0.02, bg_full[1] + 0.003, bg_full[2])
    )
    palette["surface_2"] = oklch_to_hex(
        (bg_full[0] + 0.04, bg_full[1] + 0.005, bg_full[2])
    )
    palette["surface_3"] = oklch_to_hex(
        (bg_full[0] + 0.07, bg_full[1] + 0.007, bg_full[2])
    )
    palette["surface_sel"] = oklch_to_hex(
        (bg_full[0] + 0.10, bg_full[1] + 0.015, bg_full[2])
    )

    # -- Syntax colors: hue from kitty ANSI, L/C from our perceptual targets --
    kw_hue = pick_hue_near(c4_h)  # keyword → blue family
    fn_hue = pick_hue_near(c1_h)  # function → magenta/pink family
    str_hue = pick_hue_near(c2_h)  # string → warm (red/salmon/orange)
    typ_hue = pick_hue_near(c5_h)  # type → purple family
    cst_hue = pick_hue_near(c6_h)  # constant → cyan family

    # Find hues NOT yet used for number and preproc
    used = {kw_hue, fn_hue, str_hue, typ_hue, cst_hue}
    remaining = [h for h in available if all(angular_distance(h, u) > 20 for u in used)]

    # number → pick something that contrasts with string (ideally opposite-ish)
    if remaining:
        num_hue = max(remaining, key=lambda h: angular_distance(h, str_hue))
        remaining = [h for h in remaining if angular_distance(h, num_hue) > 20]
    else:
        num_hue = (str_hue + 180) % 360  # complement

    # preproc → whatever's left, or offset from keyword
    if remaining:
        pre_hue = remaining[0]
    else:
        pre_hue = (kw_hue + 60) % 360

    # Generate the actual hex values
    palette["keyword"] = oklch_to_hex(
        (targets["bright"][0], targets["bright"][1], kw_hue)
    )
    palette["keyword_dim"] = oklch_to_hex(
        (targets["muted"][0], targets["muted"][1], kw_hue)
    )

    palette["func"] = oklch_to_hex((targets["bright"][0], targets["bright"][1], fn_hue))
    palette["func_call"] = oklch_to_hex(
        (targets["normal"][0], targets["normal"][1], fn_hue)
    )

    palette["string"] = oklch_to_hex(
        (targets["vivid"][0], targets["vivid"][1], str_hue)
    )
    palette["number"] = oklch_to_hex(
        (targets["vivid"][0], targets["vivid"][1], num_hue)
    )

    palette["type"] = oklch_to_hex(
        (targets["normal"][0], targets["normal"][1], typ_hue)
    )
    palette["constant"] = oklch_to_hex(
        (targets["normal"][0], targets["normal"][1], cst_hue)
    )

    palette["variable"] = fg_hex.lower()  # foreground IS the variable color
    palette["param"] = oklch_to_hex(
        (targets["muted"][0], targets["muted"][1], pick_hue_near(c5_h))
    )
    palette["field"] = oklch_to_hex(
        (targets["normal"][0], targets["normal"][1] * 0.5, pick_hue_near(c5_h))
    )
    palette["operator"] = oklch_to_hex(
        (targets["muted"][0], targets["muted"][1] * 0.4, 0)
    )

    palette["comment"] = oklch_to_hex(
        (targets["dim"][0], targets["dim"][1], pick_hue_near(c5_h))
    )
    palette["punctuation"] = oklch_to_hex(
        (targets["dim"][0] + 0.05, targets["dim"][1] * 0.6, 0)
    )

    palette["preproc"] = oklch_to_hex(
        (targets["muted"][0], targets["muted"][1], pre_hue)
    )

    palette["error"] = kitty_colors.get(
        "color1", "#ff5555"
    ).lower()  # keep kitty's red as-is for errors
    palette["warning"] = oklch_to_hex(
        (targets["vivid"][0], targets["vivid"][1], pick_hue_near(60))
    )  # yellow-ish
    palette["info"] = palette["keyword"]
    palette["hint"] = palette["param"]

    # Selection colors from kitty
    palette["sel_bg"] = kitty_colors.get(
        "selection_background", palette["surface_sel"]
    ).lower()
    palette["sel_fg"] = kitty_colors.get("selection_foreground", palette["bg"]).lower()

    # Cursor
    palette["cursor"] = kitty_colors.get("cursor", palette["fg"]).lower()

    # ── Debug: show the generated palette with OKLCH values ──
    print(f"\n{'=' * 60}")
    print("Generated syntax palette:")
    print(f"{'role':<14} {'hex':<10} {'L':>6} {'C':>6} {'H':>7}")
    print(f"{'-' * 50}")
    for name in [
        "keyword",
        "func",
        "func_call",
        "string",
        "number",
        "type",
        "constant",
        "variable",
        "param",
        "field",
        "operator",
        "comment",
        "punctuation",
        "preproc",
        "error",
        "warning",
    ]:
        L, C, H = hex_to_oklch(palette[name])
        print(f"{name:<14} {palette[name]:<10} {L:6.3f} {C:6.3f} {H:7.1f}°")

    # Show the contrast: L difference between syntax colors and background
    print(f"\nContrast check (ΔL from bg L={bg_L:.3f}):")
    for name in [
        "keyword",
        "func",
        "string",
        "number",
        "type",
        "comment",
        "punctuation",
    ]:
        L, _, _ = hex_to_oklch(palette[name])
        delta = L - bg_L
        bar = "█" * int(delta * 50)
        print(f"  {name:<14} ΔL={delta:.3f}  {bar}")

    return palette


def emit_lua(palette, output_path):
    """Write the palette as a Lua module that nvim can require()."""
    lines = [
        "-- Auto-generated by derive_syntax_colors.py",
        "-- from Quickshell kitty-theme.conf — DO NOT EDIT",
        "return {",
    ]
    for key in sorted(palette.keys()):
        lines.append(f'  {key} = "{palette[key]}",')
    lines.append("}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    kitty_conf_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.expanduser(
            "~/.local/state/quickshell/user/generated/terminal/kitty-theme.conf"
        )
    )
    output_path = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.expanduser("~/.config/nvim/lua/matugen/syntax_colors.lua")
    )

    print(f"Reading: {kitty_conf_path}")
    kitty_colors = parse_kitty_conf(kitty_conf_path)
    palette = derive_palette(kitty_colors)
    emit_lua(palette, output_path)
