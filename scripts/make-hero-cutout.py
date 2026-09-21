"""Cut outer studio black from the hero portrait; keep navy, hair, globe, table."""
from pathlib import Path
import shutil
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = Path(r"D:\personal web\Henok Demelash")
PHOTOS = ROOT / "public" / "assets" / "photos"
PUBLIC = ROOT / "public"
SRC = PHOTOS / "henok-hero-source.jpg"


def main() -> None:
    im = Image.open(SRC).convert("RGB")
    rgb = np.asarray(im).astype(np.int16)
    h, w = rgb.shape[:2]
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    mx = rgb.max(axis=2)

    navy = (b >= r + 6) & (b >= g + 2) & (b >= 12)
    warm = (r >= b + 2) & (r >= g) & (mx >= 8)
    strict_black = (mx <= 12) & ~navy & ~warm

    structure = np.ones((3, 3), dtype=np.uint8)
    labels, nlab = ndimage.label(strict_black, structure=structure)

    border = np.unique(
        np.concatenate(
            [labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]]
        )
    )
    border = set(int(x) for x in border if x != 0)

    trans = np.zeros((h, w), dtype=bool)
    hair_y, hair_x0, hair_x1 = 250, 170, 400

    if nlab:
        sizes = ndimage.sum(strict_black, labels, index=np.arange(1, nlab + 1))
        ys = ndimage.minimum(np.indices((h, w))[0], labels, index=np.arange(1, nlab + 1))
        xs0 = ndimage.minimum(np.indices((h, w))[1], labels, index=np.arange(1, nlab + 1))
        xs1 = ndimage.maximum(np.indices((h, w))[1], labels, index=np.arange(1, nlab + 1))
        ye = ndimage.maximum(np.indices((h, w))[0], labels, index=np.arange(1, nlab + 1))

        keep_labels = []
        for i in range(1, nlab + 1):
            sz = int(sizes[i - 1])
            hairish = ye[i - 1] < hair_y and xs0[i - 1] > hair_x0 and xs1[i - 1] < hair_x1
            if i in border:
                keep_labels.append(i)
            elif sz >= 3500 and not hairish:
                keep_labels.append(i)
        if keep_labels:
            trans = np.isin(labels, keep_labels)

        # leftover silhouette fluff (not hair): remaining black that touches trans
        remaining = strict_black & ~trans
        rlab, rn = ndimage.label(remaining, structure=structure)
        if rn:
            dilated_t = ndimage.binary_dilation(trans, structure=structure)
            for i in range(1, rn + 1):
                comp = rlab == i
                if not np.any(comp & dilated_t):
                    continue
                yy, xx = np.where(comp)
                if yy.max() < hair_y and xx.min() > hair_x0 and xx.max() < hair_x1:
                    continue
                if comp.sum() >= 8:
                    trans[comp] = True

    keep = ~trans
    hair_mask = np.zeros((h, w), dtype=bool)
    hair_mask[:hair_y, hair_x0:hair_x1] = True

    # Open only the lower-left (hip/trouser splatters), not globe posts or hair.
    hip = np.zeros((h, w), dtype=bool)
    hip[620:, :380] = True
    opened = ndimage.binary_opening(keep, structure=np.ones((5, 5), dtype=np.uint8))
    keep = np.where(hip, opened, keep)

    keep_u8 = keep.astype(np.uint8) * 255
    smooth = ndimage.median_filter(keep_u8, size=15)
    smooth = np.where(hair_mask, (~trans).astype(np.uint8) * 255, smooth)

    alpha_img = Image.fromarray(smooth, mode="L")
    alpha_soft = alpha_img.filter(ImageFilter.GaussianBlur(radius=1.2))
    alpha_erode = alpha_img.filter(ImageFilter.MinFilter(3))
    keep_dilated = alpha_img.filter(ImageFilter.MaxFilter(3))

    a = np.array(alpha_soft, dtype=np.uint16)
    a_in = np.array(alpha_erode)
    a_out = np.array(keep_dilated)
    a = np.where(a_in == 255, 255, a)
    a = np.where(a_out == 0, 0, a)
    a = a.astype(np.uint8)

    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = np.asarray(im)
    rgba[:, :, 3] = a

    # Un-blend black fringe
    fringe = (a > 3) & (a < 250)
    if np.any(fringe):
        scale = 255.0 / np.maximum(a[fringe].astype(np.float32), 1)
        rgb_f = rgba[:, :, :3].astype(np.float32)
        rgb_f[fringe] = np.clip(rgb_f[fringe] * scale[:, None], 0, 255)
        rgba[:, :, :3] = rgb_f.astype(np.uint8)
        rgba[a <= 3] = 0

    out = Image.fromarray(rgba, "RGBA")
    png_path = PHOTOS / "henok-hero.png"
    webp_path = PHOTOS / "henok-hero.webp"
    out.save(png_path, "PNG", optimize=True)
    out.save(webp_path, "WEBP", lossless=True, quality=100, method=6)
    shutil.copy2(webp_path, PUBLIC / "henok-black-portrait.webp")

    field = Image.new("RGBA", (w, h), (11, 31, 46, 255))
    comp = Image.alpha_composite(field, out)
    comp.convert("RGB").save(PHOTOS / "_hero-cutout-preview.png", "PNG")
    rgb_comp = comp.convert("RGB")
    rgb_comp.crop((0, 250, 220, 620)).save(PHOTOS / "_crop-sleeve.png")
    rgb_comp.crop((280, 380, 560, 620)).save(PHOTOS / "_crop-arm.png")
    rgb_comp.crop((100, 620, 360, 980)).save(PHOTOS / "_crop-hip.png")
    rgb_comp.crop((200, 40, 420, 260)).save(PHOTOS / "_crop-hair.png")

    extrema = out.getextrema()[3]
    print("true_alpha", out.mode == "RGBA" and extrema[0] == 0, extrema)
    print("bbox", out.split()[-1].getbbox())
    print("opaque", int((a == 255).sum()), "partial", int(((a > 3) & (a < 255)).sum()), "trans", int((a <= 3).sum()))
    print("png", png_path.stat().st_size, "webp", webp_path.stat().st_size)


if __name__ == "__main__":
    main()
