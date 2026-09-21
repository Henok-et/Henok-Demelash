"""Edge-flood studio black from the hero JPEG into a true alpha cutout."""
from __future__ import annotations

import shutil
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
SRC_JPEG = Path(
    r"C:\Users\Joys\.cursor\projects\d-personal-web-Henok-Demelash\assets"
    r"\c__Users_Joys_AppData_Roaming_Cursor_User_workspaceStorage"
    r"_b8b32753d64d400a27e8dbd933e98ca9_images"
    r"_ChatGPT_Image_Sep_18__2026__10_42_50_AM-81fb82d7-3c75-472f-a36d-63d35f5e98cc.jpg"
)
PHOTOS = ROOT / "public" / "assets" / "photos"
PUBLIC = ROOT / "public"
NAVY = (0x0B, 0x1F, 0x2E, 255)


def luma(r: int, g: int, b: int) -> float:
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def chroma(r: int, g: int, b: int) -> int:
    return max(r, g, b) - min(r, g, b)


def is_navy(r: int, g: int, b: int) -> bool:
    """Keep navy cloth, including deep shadow. Skip JPEG-blue near-black."""
    lv = luma(r, g, b)
    if lv > 78:
        return False
    # Suit shadows stay blue-dominant even at luma 4-10. Studio JPEG is neutral.
    if b >= r + 6 and b >= g + 2 and b >= 10:
        return True
    if b >= r + 8 and b >= g + 3 and b >= 14:
        return True
    return False


def is_warm(r: int, g: int, b: int) -> bool:
    """Keep hair, skin, wood, globe browns."""
    lv = luma(r, g, b)
    ch = chroma(r, g, b)
    if r >= b + 2 and lv >= 5 and ch >= 3:
        return True
    if r >= g and g >= b and ch >= 8 and lv >= 6:
        return True
    return False


def is_table_gray(r: int, g: int, b: int) -> bool:
    """Keep the round table, including the darker underside rim."""
    lv = luma(r, g, b)
    ch = chroma(r, g, b)
    return lv >= 22 and ch <= 16 and abs(r - g) <= 8 and abs(g - b) <= 12


def is_studio_black(r: int, g: int, b: int) -> bool:
    if is_navy(r, g, b) or is_warm(r, g, b) or is_table_gray(r, g, b):
        return False
    lv = luma(r, g, b)
    ch = chroma(r, g, b)
    # Blue-shifted dark is cloth, not backdrop.
    if b >= r + 6 and b >= 10:
        return False
    return lv <= 12 and ch <= 14


def _flood(img: Image.Image, seeds: list[tuple[int, int]], mask: bytearray) -> int:
    w, h = img.size
    pix = img.load()
    q: deque[tuple[int, int]] = deque()

    def consider(x: int, y: int) -> None:
        i = y * w + x
        if mask[i]:
            return
        r, g, b, _a = pix[x, y]
        if not is_studio_black(r, g, b):
            return
        mask[i] = 1
        q.append((x, y))

    for x, y in seeds:
        consider(x, y)
    added = 0
    while q:
        x, y = q.popleft()
        added += 1
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                consider(nx, ny)
    return added


def flood_backdrop(img: Image.Image) -> bytearray:
    """Remove outer studio black plus large enclosed backdrop pockets.

    Small interior components stay so navy folds and hair are not punched.
    """
    w, h = img.size
    pix = img.load()
    mask = bytearray(w * h)

    seeds = [(x, 0) for x in range(w)]
    seeds += [(x, h - 1) for x in range(w)]
    seeds += [(0, y) for y in range(h)]
    seeds += [(w - 1, y) for y in range(h)]
    edge_n = _flood(img, seeds, mask)
    print(f"edge flood: {edge_n} px")

    # Interior studio-black components. Knock out only large backdrop pockets
    # (arm/globe gap). Leave small islands (suit shadow, hair).
    visited = bytearray(mask)
    extra = 0
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if visited[i]:
                continue
            r, g, b, _a = pix[x, y]
            if not is_studio_black(r, g, b):
                visited[i] = 1
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            visited[i] = 1
            cells = [(x, y)]
            while q:
                cx, cy = q.popleft()
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if not (0 <= nx < w and 0 <= ny < h):
                        continue
                    ni = ny * w + nx
                    if visited[ni]:
                        continue
                    rr, gg, bb, _aa = pix[nx, ny]
                    if is_studio_black(rr, gg, bb):
                        visited[ni] = 1
                        q.append((nx, ny))
                        cells.append((nx, ny))
                    else:
                        visited[ni] = 1
            n = len(cells)
            minx = min(p[0] for p in cells)
            maxx = max(p[0] for p in cells)
            miny = min(p[1] for p in cells)
            maxy = max(p[1] for p in cells)
            # Large closed studio between figure, arm, globe, table.
            large_pocket = n >= 12000
            # See-through gap between wooden globe shelves.
            stand_gap = n >= 400 and miny >= 820 and minx >= 500 and (maxy - miny) <= 40
            # Enclosed studio between right sleeve and globe only.
            arm_globe = (
                n >= 400
                and minx >= 340
                and maxx <= 580
                and miny >= 340
                and maxy <= 620
            )
            if large_pocket or stand_gap or arm_globe:
                for cx, cy in cells:
                    mask[cy * w + cx] = 1
                extra += n
    # Absorb remaining studio-black that now touches the knockout, without
    # entering navy / wood / table.
    leaked = 0
    for _ in range(3):
        grow = []
        for y in range(h):
            for x in range(w):
                i = y * w + x
                if mask[i]:
                    continue
                r, g, b, _a = pix[x, y]
                if not is_studio_black(r, g, b):
                    continue
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny * w + nx]:
                        grow.append(i)
                        break
        if not grow:
            break
        for i in grow:
            if not mask[i]:
                mask[i] = 1
                leaked += 1
    print(f"interior pockets: {extra} px; leaked {leaked} px")
    return cleanup_silhouette(img, mask)


def cleanup_silhouette(img: Image.Image, mask: bytearray) -> bytearray:
    """Smooth the left cloth silhouette: fill bites, drop JPEG-black spikes."""
    w, h = img.size
    pix = img.load()
    keep = np.ones((h, w), dtype=bool)
    navy_m = np.zeros((h, w), dtype=bool)
    warm_m = np.zeros((h, w), dtype=bool)
    table_m = np.zeros((h, w), dtype=bool)
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            r, g, b, _a = pix[x, y]
            rgb[y, x] = (r, g, b)
            navy_m[y, x] = is_navy(r, g, b)
            warm_m[y, x] = is_warm(r, g, b)
            table_m[y, x] = is_table_gray(r, g, b)
            if mask[y * w + x]:
                keep[y, x] = False

    lv = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    protect = navy_m | warm_m | table_m

    flooded = ~keep
    navy_keep = navy_m & keep
    dilated_navy = ndimage.binary_dilation(navy_keep, iterations=3)
    recover = flooded & navy_m & dilated_navy
    keep |= recover
    print(f"recovered navy: {int(recover.sum())} px")

    # Core cloth: skip JPEG-blue near-black (luma < 11) that clings to the edge.
    core = ((navy_m & (lv >= 11)) | warm_m | table_m | (lv >= 32)) & keep
    core = ndimage.binary_closing(core, structure=np.ones((11, 11), dtype=np.uint8))
    core = ndimage.binary_opening(core, structure=np.ones((7, 7), dtype=np.uint8))
    core = ndimage.binary_dilation(core, iterations=2)
    # Reattach shirt cuff / skin / real navy that opening may have trimmed.
    core |= (keep & ((navy_m & (lv >= 14)) | warm_m | table_m | (lv >= 40)))

    left = np.zeros((h, w), dtype=bool)
    left[250:, :290] = True
    before = keep.copy()
    keep = np.where(left, core, keep)
    # Sleeve-hip studio gap stays empty (not in core).
    print(f"left-body reshape: kept {int((keep & left).sum())} dropped {int((before & ~keep & left).sum())} added {int((keep & ~before & left).sum())}")

    # Studio leftover between trousers and table only — do not open the pant leg.
    drop_n = 0
    for y in range(800, h):
        xs = np.where((navy_m[y, 90:255] | (lv[y, 90:255] >= 14)) & keep[y, 90:255])[0]
        if xs.size == 0:
            continue
        edge = int(xs.max()) + 90 + 6
        for x in range(edge, 420):
            if not keep[y, x] or table_m[y, x] or warm_m[y, x] or lv[y, x] >= 40:
                continue
            if lv[y, x] <= 16:
                keep[y, x] = False
                drop_n += 1
    print(f"pants-table smear: {drop_n} px")

    labels, nlab = ndimage.label(keep)
    speck_n = 0
    if nlab:
        sizes = ndimage.sum(keep, labels, index=np.arange(1, nlab + 1))
        for i, sz in enumerate(sizes, start=1):
            if sz >= 180:
                continue
            comp = labels == i
            dark = (lv <= 22) & ~protect & comp
            if int(dark.sum()) >= max(1, int(0.7 * sz)):
                keep[comp] = False
                speck_n += int(sz)
    print(f"dropped dark specks: {speck_n} px")

    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if not keep[y, x]:
                out[y * w + x] = 1
    return out


def soften_fringe(img: Image.Image, mask: bytearray, radius: int = 2) -> Image.Image:
    """Feather only pixels that touch flooded studio black; do not punch holes."""
    w, h = img.size
    pix = img.load()
    alpha = Image.new("L", (w, h), 255)
    ap = alpha.load()
    for y in range(h):
        for x in range(w):
            if mask[y * w + x]:
                ap[x, y] = 0

    # 1px dilate of background into non-navy dark fringe to kill JPEG halo.
    extra = []
    for y in range(h):
        for x in range(w):
            if mask[y * w + x]:
                continue
            r, g, b, _a = pix[x, y]
            if is_navy(r, g, b) or is_warm(r, g, b) or is_table_gray(r, g, b):
                continue
            if luma(r, g, b) > 12 or chroma(r, g, b) > 8:
                continue
            touch = False
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and mask[ny * w + nx]:
                    touch = True
                    break
            if touch:
                extra.append((x, y))
    for x, y in extra:
        ap[x, y] = 0
        mask[y * w + x] = 1

    blur = alpha.filter(ImageFilter.GaussianBlur(radius=radius))
    bp = blur.load()
    out = img.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, _a = pix[x, y]
            a = bp[x, y]
            if mask[y * w + x]:
                op[x, y] = (r, g, b, 0)
                continue
            # Extra luma-based fade on remaining dark fringe next to holes.
            if a < 250 and not is_navy(r, g, b) and not is_table_gray(r, g, b):
                lv = luma(r, g, b)
                if lv < 36:
                    fade = max(0.0, min(1.0, lv / 36.0))
                    a = int(a * (0.35 + 0.65 * fade))
            op[x, y] = (r, g, b, a)
    return out


def stats(img: Image.Image, label: str) -> None:
    w, h = img.size
    pix = img.load()
    zero = 0
    opaque = 0
    near_black_opaque = 0
    edge_black = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            if a == 0:
                zero += 1
            elif a >= 250:
                opaque += 1
                if luma(r, g, b) <= 12 and chroma(r, g, b) <= 12:
                    near_black_opaque += 1
                    if x < 4 or y < 4 or x >= w - 4 or y >= h - 4:
                        edge_black += 1
    print(
        f"{label}: {w}x{h} transparent={zero} ({100 * zero / (w * h):.1f}%) "
        f"opaque={opaque} near-black-opaque={near_black_opaque} "
        f"edge-near-black={edge_black} alpha={img.mode}"
    )


def composite_navy(img: Image.Image, dest: Path) -> None:
    bg = Image.new("RGBA", img.size, NAVY)
    bg.alpha_composite(img)
    bg.convert("RGB").save(dest, "PNG")
    print(f"preview -> {dest}")


def main() -> None:
    PHOTOS.mkdir(parents=True, exist_ok=True)
    if not SRC_JPEG.exists():
        raise SystemExit(f"missing source: {SRC_JPEG}")

    source_dest = PHOTOS / "henok-hero-source.jpg"
    shutil.copy2(SRC_JPEG, source_dest)
    print(f"copied source -> {source_dest} ({source_dest.stat().st_size} bytes)")

    src = Image.open(source_dest).convert("RGBA")
    print(f"inspect: mode was JPEG RGB, now RGBA {src.size}")
    mask = flood_backdrop(src)
    flooded = sum(mask)
    print(f"flooded studio black: {flooded} px ({100 * flooded / (src.size[0] * src.size[1]):.1f}%)")
    cut = soften_fringe(src, mask, radius=1.6)
    stats(cut, "cutout")

    png_path = PHOTOS / "henok-hero.png"
    webp_path = PHOTOS / "henok-hero.webp"
    cut.save(png_path, "PNG")
    cut.save(webp_path, "WEBP", lossless=True, quality=100, method=6)
    print(f"png {png_path.stat().st_size} webp {webp_path.stat().st_size}")
    extrema = cut.getextrema()[3]
    print(f"true_alpha {cut.mode == 'RGBA' and extrema[0] == 0} extrema={extrema}")

    # Keep older <img> roots working.
    cut.save(PUBLIC / "henok-hero.webp", "WEBP", lossless=True, quality=100, method=6)
    cut.save(PUBLIC / "henok-black-portrait.webp", "WEBP", lossless=True, quality=100, method=6)

    preview_dir = ROOT / "tmp_screens"
    preview_dir.mkdir(exist_ok=True)
    composite_navy(cut, preview_dir / "hero-cutout-navy.png")

    # Tight crop preview of suit left edge / hair / globe
    w, h = cut.size
    composite_navy(cut.crop((0, 40, 360, 280)), preview_dir / "hero-cutout-hair.png")
    composite_navy(cut.crop((0, 300, 280, 820)), preview_dir / "hero-cutout-suit.png")
    composite_navy(cut.crop((420, 430, w, h)), preview_dir / "hero-cutout-globe.png")
    composite_navy(cut.crop((100, 780, 420, h)), preview_dir / "hero-cutout-pants.png")


if __name__ == "__main__":
    main()
