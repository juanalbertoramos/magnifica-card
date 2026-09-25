"""Verification suite for the Magnifica Card.

Run: python3 tests/verify.py   (exit 0 = every check passed)
Needs: Google Chrome, Node 22+, Python with opencv-python and numpy.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "out"
READER = "https://juanalbertoramos.github.io/magnifica-humanitas/"
MIN_CONTRAST = 4.5  # text over imagery: >= 4.5:1 at every sample point (design-principles §10, WCAG 1.4.3)
STATIC_ASSETS = [
    "bg.jpg", "qr.svg", "manifest.webmanifest", "apple-touch-icon.png", "icon-512.png",
    "fonts/cinzel-decorative-700.woff2", "fonts/cormorant-garamond-italic.woff2", "fonts/inter.woff2",
]
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))


def luminance(rgb):
    def lin(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# --- static checks ---------------------------------------------------------
page = ROOT / "index.html"
check("index.html exists", page.exists())
html = page.read_text(encoding="utf-8") if page.exists() else ""

for f in ["bg-hevc.mp4", "bg.mp4", "sw.js", *STATIC_ASSETS]:
    check(f"asset {f}", (ROOT / f).exists())

for name, limit in (("bg-hevc.mp4", 1_600_000), ("bg.mp4", 3_000_000)):
    if (ROOT / name).exists():
        size = (ROOT / name).stat().st_size
        check(f"{name} <= {limit / 1e6:.1f} MB", size <= limit, f"{size / 1e6:.2f} MB")

for snippet in [
    '<link rel="manifest" href="manifest.webmanifest">',
    '<link rel="apple-touch-icon" href="apple-touch-icon.png">',
    '<meta property="og:image" content="https://juanalbertoramos.github.io/magnifica-card/bg.jpg">',
    'poster="bg.jpg"', "playsinline", "muted",
    '<source src="bg-hevc.mp4" type=\'video/mp4; codecs="hvc1"\'>',
    '<source src="bg.mp4" type="video/mp4">',
]:
    check(f"html has {snippet[:48]}", snippet in html)
check("HEVC source listed before the H.264 fallback", 0 <= html.find("bg-hevc.mp4") < html.find('src="bg.mp4"'))
check("no og:url (keeps iMessage cache-busting possible)", "og:url" not in html)
check("no redundant 'Open it here' link", "Open it here" not in html)
check("video tag autoplays and loops", "autoplay" in html and " loop " in html)
check("nothing swaps the loop for a still (always plays)", "prefers-reduced-motion" not in html)

sw = (ROOT / "sw.js").read_text(encoding="utf-8") if (ROOT / "sw.js").exists() else ""
for f in ["index.html", *STATIC_ASSETS]:
    check(f"sw precaches {f}", f"'{f}'" in sw)

try:
    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    check("manifest display is standalone", manifest.get("display") == "standalone")
    check("manifest icons exist", manifest.get("icons") and all((ROOT / i["src"]).exists() for i in manifest["icons"]))
except Exception as exc:  # missing or invalid manifest
    check("manifest parses", False, str(exc))

# --- browser checks --------------------------------------------------------
if page.exists():
    run = subprocess.run(["node", str(ROOT / "tests" / "browser.mjs")], capture_output=True, text=True, timeout=300)
    try:
        b = json.loads(run.stdout.strip().splitlines()[-1])
    except Exception:
        b = None
        check("browser run", False, (run.stderr or run.stdout)[-400:])
    if b:
        import cv2
        import numpy as np

        print(f"     (video source chosen by headless Chrome: {b.get('videoSrc')})")
        check("no horizontal overflow at 390px", b["vw"] == 390 and b["sw"] == 390, f"vw={b['vw']} sw={b['sw']}")
        check("no horizontal overflow at 320px", b["narrow"]["sw"] == 320, f"sw={b['narrow']['sw']}")
        check("QR image loaded", b["qrLoaded"])
        check("QR tile is at least 148 px", b["qr"]["w"] >= 148, f"{b['qr']['w']:.0f} px")
        se = b["se"]
        check("panel fully visible on iPhone SE (375x667)", se["panelBottom"] <= se["vh"] and se["sw"] == 375,
              f"panelBottom={se['panelBottom']:.0f} vh={se['vh']}")
        land = b["landscape"]
        check("landscape scrolls so the whole card is reachable",
              land["overflowY"] != "hidden" and land["panelBottom"] <= land["scrollHeight"] + 1,
              f"overflowY={land['overflowY']} panelBottom={land['panelBottom']:.0f} scrollHeight={land['scrollHeight']}")

        ap = b["autoplay"]
        check("the loop plays by itself (muted, looping)",
              not ap["paused"] and ap["advanced"] and ap["loop"] and ap["muted"], str(ap))
        check("no pause control", not ap["control"])
        op = b["afterOldPause"]
        check("a pause saved by the earlier version is ignored and cleared",
              not op["paused"] and op["advanced"] and op["saved"] is None, str(op))

        ov = b["overlay"]
        check("tapping the QR opens it full screen, focus on Close",
              ov["opened"]["visible"] and ov["opened"]["focus"] == "qrClose", str(ov["opened"]))
        check("Escape closes it and returns focus to the QR",
              ov["closed"]["hidden"] and ov["closed"]["focus"] == "qrBtn", str(ov["closed"]))
        big = cv2.imread(str(OUT / "qr-overlay.png"))
        value, _, _ = cv2.QRCodeDetector().detectAndDecode(big)
        check("full-screen QR decodes to the reader URL", value == READER, repr(value))

        shared = b.get("shared") or {}
        check("share url is the reader", shared.get("url") == READER, str(shared.get("url")))
        check("share text names the encyclical", "Magnifica Humanitas" in (shared.get("text") or ""))
        check("clipboard fallback includes the reader link", READER in (b.get("clipboard") or ""))
        check("service worker controls the page", b.get("controlled") is True)
        check("offline reload still renders the QR", b["offline"]["panel"] and b["offline"]["qrLoaded"])

        img = cv2.imread(str(OUT / "phone-390.png"))
        q = b["qr"]
        x, y, w, h = (int(round(v * 2)) for v in (q["x"], q["y"], q["w"], q["h"]))
        pad = 24
        crop = img[max(0, y - pad): y + h + pad, max(0, x - pad): x + w + pad]
        value, _, _ = cv2.QRCodeDetector().detectAndDecode(crop)
        check("QR decodes to the reader URL", value == READER, repr(value))

        # Contrast of each overlay text against the brightest nearby pixel behind it, 9 points x 4 frames x 2 phones
        worst = {}
        for cap in b["contrast"]:
            bgimg = cv2.cvtColor(cv2.imread(str(OUT / cap["file"])), cv2.COLOR_BGR2RGB)
            for key in ("kicker", "title", "sub"):
                r = cap[key]
                text_l = luminance(hex_rgb(b["tokens"][key]))
                for fx in (0.15, 0.5, 0.85):
                    for fy in (0.2, 0.5, 0.8):
                        px, py = int((r["x"] + r["w"] * fx) * 2), int((r["y"] + r["h"] * fy) * 2)
                        win = bgimg[max(0, py - 3): py + 4, max(0, px - 3): px + 4].reshape(-1, 3)
                        bg_l = max(luminance(p) for p in win.astype(float))
                        c = contrast(text_l, bg_l)
                        if c < worst.get(key, (99, ""))[0]:
                            worst[key] = (c, f"{cap['file']} @({fx},{fy})")
        for key in ("kicker", "title", "sub"):
            c, where = worst[key]
            check(f"{key} contrast >= {MIN_CONTRAST}:1 over the moving background", c >= MIN_CONTRAST,
                  f"worst {c:.1f}:1 at {where}")

        # The cross must stay clearly visible: its crossbar (the brightest wide band above the text) is bright
        # and ends at least 16 px above the eyebrow line, at every phone height and loop frame.
        min_gap, gap_where, dim = 999, "", []
        for cap in b["contrast"]:
            im = cv2.cvtColor(cv2.imread(str(OUT / cap["file"])), cv2.COLOR_BGR2RGB).astype(float) / 255
            bright = 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
            text_top = int(cap["kicker"]["y"] * 2)
            rows = bright[:text_top, int(bright.shape[1] * 0.25): int(bright.shape[1] * 0.75)].mean(axis=1)
            peak = int(rows.argmax())
            bottom = peak
            while bottom + 1 < len(rows) and rows[bottom + 1] >= 0.5 * rows[peak]:
                bottom += 1
            if rows[peak] < 0.5:
                dim.append(f"{cap['file']} peak {rows[peak]:.2f}")
            gap = cap["kicker"]["y"] - bottom / 2
            if gap < min_gap:
                min_gap, gap_where = gap, cap["file"]
        check("the crossbar is bright and clear of the title at every phone height",
              min_gap >= 16 and not dim, f"smallest gap {min_gap:.0f} px at {gap_where}" + (f"; dim: {dim}" if dim else ""))

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
