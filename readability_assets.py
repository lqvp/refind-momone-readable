#!/usr/bin/env python3
"""Assets and image effects for the readable rEFInd preview variants."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_BOLD = Path("/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf")
THEME_ICONS = Path("/boot/EFI/refind/themes/MomoneChinoi-hires/icons")
PANEL_BOX = (840, 600, 1720, 980)
VARIANTS = {
    "a1": {"overall_blur": 1.4, "panel_blur": 10, "panel_alpha": 72},
    "a2": {"overall_blur": 1.4, "panel_blur": 16, "panel_alpha": 128},
    "a3": {"overall_blur": 3.0, "panel_blur": 0, "panel_alpha": 0},
}


def make_kernel_icon(base_path: Path, label: str, accent: tuple[int, int, int], output_path: Path) -> None:
    """Keep the base icon recognizable while adding a kernel-specific bottom label."""
    with Image.open(base_path) as source:
        image = source.convert("RGBA")
    if image.size != (128, 128):
        image = image.resize((128, 128), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (4, 102, 124, 126),
        radius=8,
        fill=(255, 255, 255, 235),
        outline=accent + (255,),
        width=2,
    )
    font = ImageFont.truetype(str(FONT_BOLD), 20 if label == "linux" else 24)
    draw.text((64, 114), label, font=font, fill=accent + (255,), anchor="mm")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def create_kernel_icons(output_dir: Path) -> dict[str, Path]:
    """Create icons whose labels travel with the kernels, independent of scan order."""
    specifications = {
        "linux": (Path("/boot/vmlinuz-linux.png"), "linux", (23, 147, 190)),
        "lts": (THEME_ICONS / "os_arch.png", "LTS", (128, 105, 190)),
        "pf": (Path("/boot/vmlinuz-linux-pf.png"), "pf", (220, 110, 150)),
    }
    filenames = {
        "linux": "vmlinuz-linux.png",
        "lts": "vmlinuz-linux-lts.png",
        "pf": "vmlinuz-linux-pf.png",
    }
    outputs: dict[str, Path] = {}
    for key, (base, label, accent) in specifications.items():
        output = output_dir / filenames[key]
        make_kernel_icon(base, label, accent, output)
        outputs[key] = output
    return outputs


def apply_background_effects(image: Image.Image, variant: str) -> Image.Image:
    """Blur the artwork and add a fixed frosted panel behind the menu."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown readability variant: {variant}")
    settings = VARIANTS[variant]
    result = image.convert("RGBA").filter(ImageFilter.GaussianBlur(settings["overall_blur"]))

    if settings["panel_alpha"] > 0:
        x0, y0, x1, y1 = PANEL_BOX
        frosted = result.crop(PANEL_BOX).filter(ImageFilter.GaussianBlur(settings["panel_blur"]))
        result.paste(frosted, (x0, y0))
        overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rounded_rectangle(
            PANEL_BOX,
            radius=36,
            fill=(255, 255, 255, settings["panel_alpha"]),
            outline=(238, 174, 202, min(255, settings["panel_alpha"] + 60)),
            width=2,
        )
        result = Image.alpha_composite(result, overlay)
    else:
        overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rounded_rectangle(
            (840, 896, 1720, 944),
            radius=20,
            fill=(255, 255, 255, 82),
            outline=(238, 174, 202, 100),
            width=2,
        )
        result = Image.alpha_composite(result, overlay)
    return result
