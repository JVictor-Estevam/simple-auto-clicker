"""Prepare Windows icon assets in simple_autoclicker/files/."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
FILES_DIR = ROOT / "simple_autoclicker" / "files"
PNG_PATH = FILES_DIR / "autoclicker_v5_256.png"
ICO_PATH = FILES_DIR / "autoclicker_pro_v5.ico"

# Matches BG_APP in constants.py — opaque background for Windows icon surfaces.
ICON_BG = (15, 17, 23)

# Win11 taskbar commonly uses 24px; tray and title bar use 16/32.
ICO_DIMENSIONS = (16, 20, 24, 32, 40, 48, 64, 128, 256)
REQUIRED_ICO_SIZES = {(16, 16), (24, 24), (32, 32), (256, 256)}


def _prepare_master(source: Image.Image) -> Image.Image:
    """Crop transparent padding, square the artwork, and flatten to an opaque tile."""
    rgba = source.convert("RGBA")
    bbox = rgba.getbbox()
    if bbox is None:
        raise ValueError("PNG has no visible pixels.")

    cropped = rgba.crop(bbox)
    width, height = cropped.size
    side = max(width, height)
    margin = max(4, int(side * 0.06))
    canvas_side = side + margin * 2

    canvas = Image.new("RGBA", (canvas_side, canvas_side), (0, 0, 0, 0))
    offset_x = (canvas_side - width) // 2
    offset_y = (canvas_side - height) // 2
    canvas.paste(cropped, (offset_x, offset_y), cropped)

    opaque = Image.new("RGBA", (canvas_side, canvas_side), (*ICON_BG, 255))
    opaque.alpha_composite(canvas)
    return opaque.resize((256, 256), Image.Resampling.LANCZOS).convert("RGB")


def _resize_for_icon(master: Image.Image, size: int) -> Image.Image:
    if master.size == (size, size):
        return master.copy()

    current = master
    while current.width // 2 > size:
        next_size = current.width // 2
        current = current.resize((next_size, next_size), Image.Resampling.LANCZOS)

    resized = current.resize((size, size), Image.Resampling.LANCZOS)
    if size <= 48:
        resized = resized.filter(
            ImageFilter.UnsharpMask(radius=0.5, percent=130, threshold=2),
        )
    return resized


def build_ico_from_png() -> Image.Image:
    if not PNG_PATH.is_file():
        raise FileNotFoundError(f"PNG source not found: {PNG_PATH}")

    with Image.open(PNG_PATH) as opened:
        master = _prepare_master(opened)

    master.save(PNG_PATH, format="PNG", optimize=True)

    frames = [_resize_for_icon(master, dim) for dim in ICO_DIMENSIONS]
    frames[-1].save(
        ICO_PATH,
        format="ICO",
        sizes=[(dim, dim) for dim in ICO_DIMENSIONS],
        append_images=frames[:-1],
    )
    return master


def _ico_entries(path: Path) -> set[tuple[int, int]]:
    with Image.open(path) as ico:
        sizes = ico.info.get("sizes")
        if sizes:
            return set(sizes)
    return set()


def verify_icons() -> None:
    master = build_ico_from_png()

    entries = _ico_entries(ICO_PATH)
    missing = REQUIRED_ICO_SIZES - entries
    if missing:
        print(f"ICO missing required sizes: {sorted(missing)}", file=sys.stderr)
        raise SystemExit(1)

    print("Icon assets OK:")
    print(f"  {PNG_PATH} ({master.size[0]}x{master.size[1]}, opaque)")
    print(f"  {ICO_PATH} ({len(entries)} sizes: {', '.join(f'{w}x{h}' for w, h in sorted(entries))})")


if __name__ == "__main__":
    verify_icons()
