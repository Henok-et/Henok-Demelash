"""Retarget leftover studio/cyan fringes to navy without flattening alpha cutouts."""
from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BRAND = (0x0B, 0x1F, 0x2E, 255)  # #0b1f2e
OLD_CYAN = (0x25, 0x96, 0xBE)


def luma(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def chroma(r: int, g: int, b: int) -> int:
    return max(r, g, b) - min(r, g, b)


def is_navy(r: int, g: int, b: int) -> bool:
    """Keep navy cloth, including deep suit folds."""
    return b >= r + 6 and b >= g + 3 and b >= 10 and chroma(r, g, b) >= 6


def is_warm(r: int, g: int, b: int) -> bool:
    lv = luma(r, g, b)
    ch = chroma(r, g, b)
    if r >= b + 2 and lv >= 7 and ch >= 3:
        return True
    if r >= g and g >= b and ch >= 8 and lv >= 8:
        return True
    return False


def is_table_gray(r: int, g: int, b: int) -> bool:
    lv = luma(r, g, b)
    ch = chroma(r, g, b)
    return lv >= 22 and ch <= 16 and abs(r - g) <= 8 and abs(g - b) <= 12


def is_old_cyan(r: int, g: int, b: int) -> bool:
    dr, dg, db = r - OLD_CYAN[0], g - OLD_CYAN[1], b - OLD_CYAN[2]
    if dr * dr + dg * dg + db * db <= 48 * 48:
        return True
    lv = luma(r, g, b)
    return lv >= 55 and b >= 110 and g >= 70 and b >= r + 30 and g >= r + 15


def is_backdrop(r: int, g: int, b: int, a: int, luma_cut: float, chroma_cut: int) -> bool:
    if a < 10:
        return True
    if is_navy(r, g, b):
        return False
    return luma(r, g, b) <= luma_cut and chroma(r, g, b) <= chroma_cut


def flood_mask(img: Image.Image, luma_cut: float, chroma_cut: int) -> bytearray:
    img = img.convert("RGBA")
    w, h = img.size
    pix = img.load()
    seen = bytearray(w * h)
    q: deque[tuple[int, int]] = deque()

    def consider(x: int, y: int) -> None:
        i = y * w + x
        if seen[i]:
            return
        r, g, b, a = pix[x, y]
        if not is_backdrop(r, g, b, a, luma_cut, chroma_cut):
            return
        seen[i] = 1
        q.append((x, y))

    for x in range(w):
        consider(x, 0)
        consider(x, h - 1)
    for y in range(h):
        consider(0, y)
        consider(w - 1, y)

    while q:
        x, y = q.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                consider(nx, ny)
    return seen


def apply_flood(
    path: Path,
    *,
    mode: str,
    luma_cut: float = 22,
    chroma_cut: int = 18,
    fringe: float = 48,
    save_as: Path | None = None,
) -> None:
    src = Image.open(path).convert("RGBA")
    w, h = src.size
    pix = src.load()
    mask = flood_mask(src, luma_cut, chroma_cut)
    flooded = 0

    for y in range(h):
        for x in range(w):
            if mask[y * w + x]:
                r, g, b, a = pix[x, y]
                if mode == "brand":
                    pix[x, y] = BRAND
                else:
                    pix[x, y] = (r, g, b, 0)
                flooded += 1

    if fringe:
        for y in range(h):
            for x in range(w):
                if mask[y * w + x]:
                    continue
                r, g, b, a = pix[x, y]
                if a < 10 or is_navy(r, g, b):
                    continue
                lv = luma(r, g, b)
                if lv > fringe or chroma(r, g, b) > 55:
                    continue
                adjacent = False
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny * w + nx]:
                        adjacent = True
                        break
                if not adjacent:
                    continue
                t = 1.0 - (lv / fringe)
                if mode == "brand":
                    pix[x, y] = (
                        int(r + (BRAND[0] - r) * t),
                        int(g + (BRAND[1] - g) * t),
                        int(b + (BRAND[2] - b) * t),
                        255,
                    )
                else:
                    pix[x, y] = (r, g, b, max(0, int(a * (1.0 - t))))

    out = save_as or path
    if out.suffix.lower() == ".webp":
        src.save(out, "WEBP", quality=92, method=6)
    else:
        src.save(out, "PNG")
    print(f"{path.name}: flooded {flooded} px -> {out.name} ({mode})")


def retarget_cutout_fringes(path: Path, extras: list[Path] | None = None) -> None:
    """Recolor leftover cyan/black edge pixels to navy. Preserve real alpha holes."""
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    pix = img.load()
    alpha_range = img.getextrema()[3]
    cyan_n = 0
    black_n = 0

    def touches_hole(x: int, y: int) -> bool:
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and pix[nx, ny][3] < 12:
                return True
        return False

    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            if a < 8:
                continue
            if is_navy(r, g, b) or is_warm(r, g, b) or is_table_gray(r, g, b):
                continue
            if is_old_cyan(r, g, b):
                pix[x, y] = (BRAND[0], BRAND[1], BRAND[2], a)
                cyan_n += 1
                continue
            dark = luma(r, g, b) <= 18 and chroma(r, g, b) <= 16
            if dark and (a < 250 or touches_hole(x, y)):
                pix[x, y] = (BRAND[0], BRAND[1], BRAND[2], a)
                black_n += 1

    png_path = path.with_suffix(".png")
    img.save(png_path, "PNG")
    img.save(path, "WEBP", quality=94, method=6)
    for extra in extras or []:
        extra.parent.mkdir(parents=True, exist_ok=True)
        img.save(extra, "WEBP", quality=94, method=6)
    print(
        f"{path.name}: cyan->{cyan_n} black-fringe->{black_n} "
        f"alpha={alpha_range} kept_holes={alpha_range[0] == 0}"
    )


def knockout_outside_circle(path: Path, luma_cut: float = 28, chroma_cut: int = 22) -> None:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    pix = img.load()
    cx, cy = (w - 1) / 2, (h - 1) / 2
    radius = min(w, h) / 2 * 0.98
    r2 = radius * radius
    n = 0
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= r2:
                continue
            r, g, b, a = pix[x, y]
            if is_backdrop(r, g, b, a, luma_cut, chroma_cut):
                pix[x, y] = (r, g, b, 0)
                n += 1
    img.save(path, "PNG")
    print(f"{path.name}: knocked out {n} px outside circle")


def main() -> None:
    hero = ROOT / "public" / "assets" / "photos" / "henok-hero.webp"
    logos = ROOT / "public" / "logos"
    public = ROOT / "public"

    # Keep the cutout's real alpha. Only retarget leftover cyan/black fringes.
    if hero.exists():
        retarget_cutout_fringes(
            hero,
            extras=[
                public / "henok-hero.webp",
                public / "henok-black-portrait.webp",
            ],
        )

    # ACYDEAI is restored separately (restore_acydeai_logo.py). Flooding dark
    # pixels to alpha would wipe the Africa silhouette and wordmark.
    for name in ("yalda.png", "abrehot.png", "insa.png"):
        p = logos / name
        if p.exists():
            apply_flood(p, mode="alpha", luma_cut=24, chroma_cut=20, fringe=36)

    for name in ("mofa.png", "icoyaca.png"):
        p = logos / name
        if p.exists():
            knockout_outside_circle(p)


if __name__ == "__main__":
    main()
