"""Verification suite for the Magnifica Card.

Run: python3 tests/verify.py   (exit 0 = every check passed)
Needs: Google Chrome, Node 22+, Python with opencv-python.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
READER = "https://juanalbertoramos.github.io/magnifica-humanitas/"
STATIC_ASSETS = [
    "bg.jpg", "qr.svg", "manifest.webmanifest", "apple-touch-icon.png", "icon-512.png",
    "fonts/cinzel-decorative-700.woff2", "fonts/cormorant-garamond-italic.woff2", "fonts/inter.woff2",
]
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))


# --- static checks ---------------------------------------------------------
page = ROOT / "index.html"
check("index.html exists", page.exists())
html = page.read_text(encoding="utf-8") if page.exists() else ""

for f in ["bg.mp4", "sw.js", *STATIC_ASSETS]:
    check(f"asset {f}", (ROOT / f).exists())

video = ROOT / "bg.mp4"
if video.exists():
    size = video.stat().st_size
    check("bg.mp4 <= 3 MB", size <= 3_000_000, f"{size / 1e6:.2f} MB")

for snippet in [
    '<link rel="manifest" href="manifest.webmanifest">',
    '<link rel="apple-touch-icon" href="apple-touch-icon.png">',
    '<meta property="og:image" content="https://juanalbertoramos.github.io/magnifica-card/bg.jpg">',
    'poster="bg.jpg"', "playsinline", "muted",
]:
    check(f"html has {snippet[:48]}", snippet in html)
check("no og:url (keeps iMessage cache-busting possible)", "og:url" not in html)

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
    run = subprocess.run(["node", str(ROOT / "tests" / "browser.mjs")], capture_output=True, text=True, timeout=180)
    try:
        b = json.loads(run.stdout.strip().splitlines()[-1])
    except Exception:
        b = None
        check("browser run", False, (run.stderr or run.stdout)[-400:])
    if b:
        check("no horizontal overflow at 390px", b["vw"] == 390 and b["sw"] == 390, f"vw={b['vw']} sw={b['sw']}")
        check("QR image loaded", b["qrLoaded"])
        se = b["se"]
        check("panel fully visible on iPhone SE (375x667)", se["panelBottom"] <= se["vh"] and se["sw"] == 375,
              f"panelBottom={se['panelBottom']:.0f} vh={se['vh']}")
        shared = b.get("shared") or {}
        check("share url is the reader", shared.get("url") == READER, str(shared.get("url")))
        check("share text names the encyclical", "Magnifica Humanitas" in (shared.get("text") or ""))
        check("clipboard fallback includes the reader link", READER in (b.get("clipboard") or ""))
        check("service worker controls the page", b.get("controlled") is True)
        check("offline reload still renders the QR", b["offline"]["panel"] and b["offline"]["qrLoaded"])

        import cv2  # decode the QR from the rendered page, the way a phone camera would see it

        img = cv2.imread(str(ROOT / "tests" / "out" / "phone-390.png"))
        q = b["qr"]
        x, y, w, h = (int(round(v * 2)) for v in (q["x"], q["y"], q["w"], q["h"]))
        pad = 24
        crop = img[max(0, y - pad): y + h + pad, max(0, x - pad): x + w + pad]
        value, _, _ = cv2.QRCodeDetector().detectAndDecode(crop)
        check("QR decodes to the reader URL", value == READER, repr(value))

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
