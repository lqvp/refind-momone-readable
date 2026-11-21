#!/usr/bin/env python3
"""Render rEFInd's confirmed main-menu layout over one or more backgrounds."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat

from readability_assets import apply_background_effects, create_kernel_icons

WIDTH, HEIGHT = 2560, 1440
SMALL_WIDTH = 1280
RESAMPLING = Image.Resampling.LANCZOS

THEME_DIR = Path("/boot/EFI/refind/themes/MomoneChinoi-hires")
ICONS_DIR = THEME_DIR / "icons"
BASE_ICON_DIR = Path(__file__).resolve().parent / "base-icons"
FONT_PATH = Path("/usr/share/fonts/TTF/DejaVuSansMono.ttf")
OUTPUT_DIR = Path(__file__).resolve().parent / "renders"

TILE_XSPACING = 8
TILE_YSPACING = 16
BIG_ICON_SIZE = 128
SMALL_ICON_SIZE = 64
TILE_SIZES = (BIG_ICON_SIZE * 9 // 8, SMALL_ICON_SIZE * 4 // 3)
ROW0_Y = HEIGHT // 2 - TILE_SIZES[0] // 2
ROW1_Y = ROW0_Y + TILE_SIZES[0] + TILE_YSPACING

OS_ICON_PATHS = (
    # Frozen copies taken from the ESP before the A1 staged icons were installed.
    BASE_ICON_DIR / "vmlinuz-linux.png",
    ICONS_DIR / "os_arch.png",
    BASE_ICON_DIR / "vmlinuz-linux-pf.png",
    ICONS_DIR / "os_windows.png",
)
TOOL_ICON_PATHS = (
    ICONS_DIR / "func_shutdown.png",
    ICONS_DIR / "func_reset.png",
    ICONS_DIR / "func_firmware.png",
    ICONS_DIR / "func_exit.png",
)

HINTS = (
    (1356, "Use arrow keys to move cursor; Enter to boot;"),
    (1384, "Insert, Tab, or F2 for more options; Esc or Backspace to refresh"),
)


def row_x(tile_size: int) -> tuple[int, ...]:
    start = (WIDTH + TILE_XSPACING - (tile_size + TILE_XSPACING) * 4) // 2
    return tuple(start + index * (tile_size + TILE_XSPACING) for index in range(4))


def load_rgba(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    with Image.open(path) as source:
        image = source.convert("RGBA")
    if size is not None and image.size != size:
        image = image.resize(size, RESAMPLING)
    return image


def load_background(path: Path) -> Image.Image:
    source = load_rgba(path)
    white = Image.new("RGBA", source.size, (255, 255, 255, 255))
    white.alpha_composite(source)
    return white.resize((WIDTH, HEIGHT), RESAMPLING)


def draw_hints(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(str(FONT_PATH), 28)
    for y, text in HINTS:
        background = canvas.crop((0, y, WIDTH, y + 32)).convert("RGB")
        red, green, blue = ImageStat.Stat(background).mean
        brightness = (red + green + blue) / 3
        color = (0, 0, 0, 255) if brightness >= 128 else (255, 255, 255, 255)
        draw.text((WIDTH // 2, y), text, font=font, fill=color, anchor="mt")


def label_font_for_width(text: str, max_width: int = 880) -> ImageFont.FreeTypeFont:
    """Shrink long auto-detected entry names only as much as needed."""
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for size in range(28, 17, -1):
        font = ImageFont.truetype(str(FONT_PATH), size)
        if probe.textlength(text, font=font) <= max_width:
            return font
    return ImageFont.truetype(str(FONT_PATH), 18)


def draw_selected_label(canvas: Image.Image, text: str) -> None:
    draw = ImageDraw.Draw(canvas)
    font = label_font_for_width(text)
    background = canvas.crop((0, 909, WIDTH, 909 + 32)).convert("RGB")
    red, green, blue = ImageStat.Stat(background).mean
    brightness = (red + green + blue) / 3
    color = (0, 0, 0, 255) if brightness >= 128 else (255, 255, 255, 255)
    draw.text((WIDTH // 2, 909), text, font=font, fill=color, anchor="mt")


def render_menu(
    background_path: Path,
    *,
    variant: str = "original",
    assets_dir: Path | None = None,
    label_text: str = "Boot vmlinuz-linux-pf",
) -> Image.Image:
    canvas = load_background(background_path)
    os_icon_paths = OS_ICON_PATHS
    if variant != "original":
        canvas = apply_background_effects(canvas, variant)
        icon_output_dir = assets_dir or (Path(__file__).resolve().parent / "improved/icons")
        kernel_icons = create_kernel_icons(icon_output_dir)
        os_icon_paths = (
            kernel_icons["linux"],
            kernel_icons["lts"],
            kernel_icons["pf"],
            ICONS_DIR / "os_windows.png",
        )
    selections = (
        load_rgba(THEME_DIR / "selection_big.png", (TILE_SIZES[0], TILE_SIZES[0])),
        load_rgba(THEME_DIR / "selection_small.png", (TILE_SIZES[1], TILE_SIZES[1])),
    )
    badge = load_rgba(ICONS_DIR / "vol_internal.png", (32, 32))

    rows = (
        (os_icon_paths, row_x(TILE_SIZES[0]), ROW0_Y, TILE_SIZES[0], BIG_ICON_SIZE),
        (TOOL_ICON_PATHS, row_x(TILE_SIZES[1]), ROW1_Y, TILE_SIZES[1], SMALL_ICON_SIZE),
    )
    for row_index, (paths, xs, y, tile_size, icon_size) in enumerate(rows):
        offset = (tile_size - icon_size) // 2
        for index, (path, x) in enumerate(zip(paths, xs, strict=True)):
            if row_index == 0 and index == 2:
                canvas.alpha_composite(selections[row_index], (x, y))

            icon = load_rgba(path, (icon_size, icon_size))
            canvas.alpha_composite(icon, (x + offset, y + offset))

            if row_index == 0:
                badge_position = (x + tile_size - 8 - 32, y + tile_size - 8 - 32)
                canvas.alpha_composite(badge, badge_position)

    if variant != "original":
        draw_selected_label(canvas, label_text)
    draw_hints(canvas)
    return canvas.convert("RGB")


def render_and_save(
    background_path: Path,
    *,
    variant: str = "original",
    assets_dir: Path | None = None,
) -> tuple[Path, Path]:
    rendered = render_menu(background_path, variant=variant, assets_dir=assets_dir)
    suffix = "" if variant == "original" else f"_{variant}"
    full_path = OUTPUT_DIR / f"{background_path.stem}{suffix}.png"
    small_path = OUTPUT_DIR / f"{background_path.stem}{suffix}_1280.png"
    rendered.save(full_path)
    rendered.resize((SMALL_WIDTH, HEIGHT * SMALL_WIDTH // WIDTH), RESAMPLING).save(small_path)
    return full_path, small_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backgrounds", nargs="+", type=Path, help="background image(s)")
    parser.add_argument("--variant", choices=("original", "a1", "a2", "a3"), default="original")
    parser.add_argument("--assets-dir", type=Path, default=None)
    args = parser.parse_args()

    for background in args.backgrounds:
        if not background.is_file():
            parser.error(f"background is not a file: {background}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for background in args.backgrounds:
        for output_path in render_and_save(background, variant=args.variant, assets_dir=args.assets_dir):
            with Image.open(output_path) as output:
                dimensions = f"{output.width}x{output.height}"
            print(f"{output_path} ({dimensions}, {output_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
