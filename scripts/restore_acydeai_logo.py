"""Rebuild ACYDEAI logo for the navy field.

Source is the original white-background JPG. Outer paper becomes transparent,
the orange continent is kept, and near-black silhouette + wordmark are recolored
to cream (#f7f4ec). Black is never painted to navy.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "public" / "assets" / "brand" / "acydeai.jpg"
OUT_LOGOS = ROOT / "public" / "logos" / "acydeai.png"
OUT_BRAND = ROOT / "public" / "assets" / "brand" / "acydeai.png"
PREVIEW = ROOT / "tmp_screens" / "acydeai-preview-navy.png"

CREAM = (0xF7, 0xF4, 0xEC)  # #f7f4ec — matches --color-light
NAVY = (0x0B, 0x1F, 0x2E, 255)


def luma(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def chroma(r: int, g: int, b: int) -> int:
    return max(r, g, b) - min(r, g, b)


def clamp8(v: float) -> int:
    return max(0, min(255, int(round(v))))


def unpremultiply(c: int, a: int) -> int:
    if a <= 0:
        return c
    return clamp8(255 + (c - 255) * 255 / a)


def is_orange(r: int, g: int, b: int, lv: float, ch: int) -> bool:
    """Warm orange of the NW African continent, including pale AA fringes."""
    warm = r - b
    if warm < 18 or r < g - 6:
        return False
    if r < 90:
        return False
    # Solid continent
    if warm >= 40 and ch >= 35 and lv <= 210:
        return True
    # Edge AA: still distinctly warm vs paper/ink
    if warm >= 22 and ch >= 18 and r >= 140:
        return True
    return False


def process() -> Image.Image:
    src_im = Image.open(SRC).convert("RGB")
    w, h = src_im.size
    src = src_im.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()

    orange_n = ink_n = paper_n = 0

    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            lv = luma(r, g, b)
            ch = chroma(r, g, b)

            # Paper / JPEG wash → transparent
            if lv >= 238 and ch <= 24:
                paper_n += 1
                continue
            if lv >= 228 and ch <= 10:
                paper_n += 1
                continue

            if is_orange(r, g, b, lv, ch):
                orange_n += 1
                # Interior continent stays fully opaque in original orange
                if lv <= 185 and ch >= 45:
                    dst[x, y] = (r, g, b, 255)
                    continue
                # Fringe: lift off white, keep hue
                a = clamp8((255.0 - lv) / 70.0 * 255.0)
                a = max(a, clamp8((255 - min(r, g, b)) * 1.15))
                if a < 12:
                    paper_n += 1
                    continue
                a = min(255, a)
                dst[x, y] = (unpremultiply(r, a), unpremultiply(g, a), unpremultiply(b, a), a)
                continue

            # Near-black silhouette, Madagascar, wordmark → cream
            # Coverage against white; do not emit navy.
            if lv <= 58:
                coverage = 1.0
            else:
                # Boost mid-gray serif AA so thin wordmark strokes stay cream
                t = max(0.0, (225.0 - lv) / 225.0)
                coverage = min(1.0, t ** 0.42)
            if ch <= 36:
                coverage = min(1.0, coverage * 1.12)
            else:
                # leftover warm-gray JPEG noise around orange — keep faint
                coverage *= 0.35
            if coverage < 0.06:
                paper_n += 1
                continue
            a = 255 if lv <= 58 else clamp8(coverage * 255)
            dst[x, y] = (CREAM[0], CREAM[1], CREAM[2], a)
            ink_n += 1

    # Crop to content with modest padding so the mark fills the collage tile
    bbox = out.getbbox()
    if bbox:
        pad = 28
        l, t, rgt, btm = bbox
        l = max(0, l - pad)
        t = max(0, t - pad)
        rgt = min(w, rgt + pad)
        btm = min(h, btm + pad)
        out = out.crop((l, t, rgt, btm))

    print(f"paper={paper_n} orange={orange_n} ink->cream={ink_n} size={out.size}")
    return out


def save_all(img: Image.Image) -> None:
    for path in (OUT_LOGOS, OUT_BRAND):
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path, "PNG", optimize=True)
        print(f"wrote {path} ({path.stat().st_size} bytes)")

    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    navy = Image.new("RGBA", img.size, NAVY)
    Image.alpha_composite(navy, img).convert("RGB").save(PREVIEW, "PNG")
    print(f"preview {PREVIEW}")


if __name__ == "__main__":
    save_all(process())
