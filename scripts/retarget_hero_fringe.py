"""Retint leftover cyan/black hero fringe to navy. Keep alpha and navy cloth."""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = ROOT / "public" / "assets" / "photos"
PUBLIC = ROOT / "public"
NAVY = (0x0B, 0x1F, 0x2E)


def luma(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def chroma(r: int, g: int, b: int) -> int:
    return max(r, g, b) - min(r, g, b)


def is_navy_cloth(r: int, g: int, b: int) -> bool:
    lv = luma(r, g, b)
    return b >= r + 6 and b >= g + 2 and b >= 12 and lv <= 90 and g < 90


def is_warm(r: int, g: int, b: int) -> bool:
    return r >= b + 2 and r >= g and max(r, g, b) >= 8


def is_cyan_field(r: int, g: int, b: int) -> bool:
    return g >= 90 and b >= 120 and r <= 90 and g >= r + 40


def is_near_black(r: int, g: int, b: int) -> bool:
    return luma(r, g, b) <= 16 and chroma(r, g, b) <= 14 and not is_navy_cloth(r, g, b)


def adjacent_transparent(pix, x: int, y: int, w: int, h: int) -> bool:
    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if 0 <= nx < w and 0 <= ny < h and pix[nx, ny][3] == 0:
            return True
    return False


def retarget(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    pix = im.load()
    cyan_n = 0
    black_n = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            if a == 0:
                continue
            if is_warm(r, g, b) or is_navy_cloth(r, g, b):
                continue
            if is_cyan_field(r, g, b):
                pix[x, y] = (*NAVY, a)
                cyan_n += 1
                continue
            if is_near_black(r, g, b) and (a < 250 or adjacent_transparent(pix, x, y, w, h)):
                pix[x, y] = (*NAVY, a)
                black_n += 1
    print(f"{path.name}: cyan->{cyan_n} black-fringe->{black_n} alpha kept, size {w}x{h}")
    return im


def main() -> None:
    src = PHOTOS / "henok-hero.webp"
    if not src.exists():
        src = PHOTOS / "henok-hero.png"
    cut = retarget(src)

    png_path = PHOTOS / "henok-hero.png"
    webp_path = PHOTOS / "henok-hero.webp"
    cut.save(png_path, "PNG", optimize=True)
    cut.save(webp_path, "WEBP", lossless=True, quality=100, method=6)
    shutil.copy2(webp_path, PUBLIC / "henok-black-portrait.webp")
    public_hero = PUBLIC / "henok-hero.webp"
    if public_hero.exists():
        shutil.copy2(webp_path, public_hero)
    print("wrote", png_path.name, webp_path.name)


if __name__ == "__main__":
    main()
