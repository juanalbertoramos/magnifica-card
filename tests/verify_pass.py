"""Checks for the Magnifica Apple Wallet pass.

Run: python3 tests/verify_pass.py   (exit 0 = every check passed)
Needs: Python with Pillow, openssl, and the signing assets in ~/.config/magnifica-card/pass/ (never in the repo).
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PKPASS = ROOT / "magnifica.pkpass"
KEYS = Path.home() / ".config" / "magnifica-card" / "pass"
READER = "https://juanalbertoramos.github.io/magnifica-humanitas/"
EXACT = {"artwork": (358, 448), "icon": (38, 38), "thumbnail": (90, 90)}  # points
LOGOS = {"primaryLogo": (30, 30, 126), "logo": (50, 50, 160)}  # height, min width, max width (points)
SCALES = ((1, ""), (2, "@2x"), (3, "@3x"))
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))


def run(*args):
    return subprocess.run(list(args), capture_output=True, text=True)


check("magnifica.pkpass exists", PKPASS.exists())
if PKPASS.exists():
    work = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(PKPASS) as z:
        names = z.namelist()
        z.extractall(work)
    check("bundle is flat (no folders)", all("/" not in n for n in names))

    required = ["pass.json", "manifest.json", "signature"]
    required += [f"{base}{suffix}.png" for base in (*EXACT, *LOGOS) for _, suffix in SCALES]
    missing = [f for f in required if f not in names]
    check("all required files present", not missing, f"missing {missing}" if missing else f"{len(names)} files")

    for base, (w, h) in EXACT.items():
        for scale, suffix in SCALES:
            p = work / f"{base}{suffix}.png"
            if p.exists():
                size = Image.open(p).size
                check(f"{base}{suffix}.png is {w * scale}x{h * scale}", size == (w * scale, h * scale), str(size))
    for base, (h, wmin, wmax) in LOGOS.items():
        for scale, suffix in SCALES:
            p = work / f"{base}{suffix}.png"
            if p.exists():
                W, H = Image.open(p).size
                check(f"{base}{suffix}.png height {h * scale}, width {wmin * scale}-{wmax * scale}",
                      H == h * scale and wmin * scale <= W <= wmax * scale, f"{W}x{H}")

    manifest = json.loads((work / "manifest.json").read_text())
    files = [n for n in names if n not in ("manifest.json", "signature")]
    wrong = [n for n in files if manifest.get(n) != hashlib.sha1((work / n).read_bytes()).hexdigest()]
    extra = [k for k in manifest if k not in files]
    check("manifest.json has the SHA-1 of every file", not wrong and not extra, f"wrong {wrong} extra {extra}")

    certs = run("openssl", "pkcs7", "-inform", "DER", "-in", str(work / "signature"), "-print_certs").stdout
    check("signature carries the signer and Apple WWDR certificates", certs.count("BEGIN CERTIFICATE") >= 2,
          f"{certs.count('BEGIN CERTIFICATE')} certificates")
    signer_pem = work / "signer.pem"
    blocks = re.findall(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", certs, re.S)
    signer = next((b for b, s in zip(blocks, re.findall(r"subject=.*", certs)) if "Pass Type ID" in s), None)
    check("signer is the Pass Type ID certificate", signer is not None)
    if signer:
        signer_pem.write_text(signer + "\n")
        chain = run("openssl", "verify", "-partial_chain", "-CAfile", str(KEYS / "wwdr.pem"), str(signer_pem))
        check("signer certificate chains to Apple WWDR G4", chain.returncode == 0, chain.stdout.strip()[-80:])
    sig = run("openssl", "smime", "-verify", "-binary", "-noverify", "-inform", "DER", "-in", str(work / "signature"),
              "-content", str(work / "manifest.json"), "-out", "/dev/null")
    check("signature over manifest.json is valid", sig.returncode == 0, (sig.stderr or sig.stdout).strip()[-120:])

    pj = json.loads((work / "pass.json").read_text())
    subject = run("openssl", "x509", "-in", str(KEYS / "pass.pem"), "-noout", "-subject").stdout
    uid = re.search(r"UID\s*=\s*([^,\n]+)", subject)
    ou = re.search(r"OU\s*=\s*([^,\n]+)", subject)
    check("formatVersion is 1", pj.get("formatVersion") == 1)
    check("passTypeIdentifier matches the certificate",
          uid is not None and pj.get("passTypeIdentifier") == uid.group(1).strip(), str(pj.get("passTypeIdentifier")))
    check("teamIdentifier matches the certificate",
          ou is not None and pj.get("teamIdentifier") == ou.group(1).strip(), str(pj.get("teamIdentifier")))
    barcode = (pj.get("barcodes") or [{}])[0]
    check("QR code opens the reader", barcode.get("format") == "PKBarcodeFormatQR" and barcode.get("message") == READER,
          str(barcode.get("message")))
    check("Poster Generic with a generic fallback", "posterGeneric" in pj and "generic" in pj)
    for style in ("posterGeneric", "generic"):
        labels = [f.get("label") for f in pj.get(style, {}).get("backFields", [])]
        check(f"{style} back: About / Read it / This card / Note", labels == ["About", "Read it", "This card", "Note"],
              str(labels))
    check("pass can be shared", pj.get("sharingProhibited") is not True)

html = (ROOT / "index.html").read_text(encoding="utf-8")
start, end = html.find('id="qrOverlay"'), html.find('<div class="toast"')
check("full-screen QR view links to magnifica.pkpass", start != -1 and 'href="magnifica.pkpass"' in html[start:end])
# Apple's license allows its badge only as provided: US-UK RGB SVG from the Add to Apple Wallet kit (2021-10-14)
BADGE, BADGE_SHA256 = ROOT / "add-to-apple-wallet.svg", "052b3b446860fd2f9b49c2f0336038947623a5a9433ee3583585b8552ff6f506"
check("the link shows Apple's official badge, unmodified",
      'src="add-to-apple-wallet.svg"' in html[start:end] and BADGE.exists()
      and hashlib.sha256(BADGE.read_bytes()).hexdigest() == BADGE_SHA256)

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
