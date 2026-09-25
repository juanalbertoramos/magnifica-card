"""Generates every Wallet pass image at its exact size from the approved artwork (front A, "Illuminated Icon").

Run: python3 build/make-wallet-images.py [artwork.png]
Writes wallet/images/{artwork,primaryLogo,logo,icon,thumbnail}{,@2x,@3x}.png and prints the lapis colour for pass.json.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageStat

DEFAULT_ART = (Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/AI/Media Gen"
               / "2026-09-25-magnifica-wallet-a3-illuminated-icon/image-01.png")
ART = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ART
OUT = Path(__file__).resolve().parent.parent / "wallet" / "images"
GOLD = (236, 220, 166)
SCALES = ((1, ""), (2, "@2x"), (3, "@3x"))


def cover(im, w, h):
    """Scale to cover w x h, then crop the centre (no stretching)."""
    s = max(w / im.width, h / im.height)
    r = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    left, top = (r.width - w) // 2, (r.height - h) // 2
    return r.crop((left, top, left + w, top + h))


def small_png(im, path):
    """256-colour dithered PNG: Apple asks for small pass images; the illustration survives it cleanly."""
    im.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                               dither=Image.Dither.FLOYDSTEINBERG).save(path, optimize=True)


def cross(size, background=None):
    """A gold Latin cross with a soft glow on a size x size canvas (transparent unless a background is given)."""
    k = 4  # draw large, then downsample for smooth edges
    S = size * k
    bar, top, arm_y, arm = round(S * 0.13), round(S * 0.06), round(S * 0.30), round(S * 0.62)
    shape = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(shape)
    d.rectangle([S // 2 - bar // 2, top, S // 2 + bar // 2, S - top], fill=255)
    d.rectangle([S // 2 - arm // 2, arm_y - bar // 2, S // 2 + arm // 2, arm_y + bar // 2], fill=255)
    glow = shape.filter(ImageFilter.GaussianBlur(S * 0.03)).point(lambda v: v * 0.55)
    base = Image.new("RGBA", (S, S), background + (255,) if background else (0, 0, 0, 0))
    base.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (S, S), c) for c in GOLD], glow)))
    base.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (S, S), c) for c in GOLD], shape)))
    return base.resize((size, size), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    art = Image.open(ART).convert("RGB")
    lapis = tuple(round(v) for v in ImageStat.Stat(art.crop((0, int(art.height * 0.82), art.width, art.height))).mean)

    for scale, suffix in SCALES:
        small_png(cover(art, 358 * scale, 448 * scale), OUT / f"artwork{suffix}.png")
        cross(30 * scale).save(OUT / f"primaryLogo{suffix}.png", optimize=True)
        cross(50 * scale).save(OUT / f"logo{suffix}.png", optimize=True)
        cross(38 * scale, background=lapis).convert("RGB").save(OUT / f"icon{suffix}.png", optimize=True)
        # thumbnail: a square around the cross and its halo (the cross sits between 12% and 48% of the height)
        side = int(art.height * 0.45)
        cx, cy = art.width // 2, int(art.height * 0.30)
        thumb = art.crop((cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2))
        thumb.resize((90 * scale, 90 * scale), Image.LANCZOS).save(OUT / f"thumbnail{suffix}.png", optimize=True)

    total = sum(p.stat().st_size for p in OUT.glob("*.png"))
    print(f"wrote {len(list(OUT.glob('*.png')))} images, {total / 1e6:.2f} MB; lapis background rgb{lapis}")


if __name__ == "__main__":
    main()
