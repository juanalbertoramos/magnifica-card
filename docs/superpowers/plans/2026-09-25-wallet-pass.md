# Magnifica Wallet Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A signed `magnifica.pkpass`: iOS 27 Poster Generic with front A and a generic fallback. It's published on the card site, and an "Add to Apple Wallet" link sits in the card's full-screen QR view.

**Architecture:** Sources live in `wallet/` (`pass.json` plus images generated from the approved artwork). `build/make-pass.sh` builds `manifest.json` (SHA-1 of each file), signs it with a detached PKCS#7 signature (openssl smime, signer cert + WWDR G4 included), and zips the result into `magnifica.pkpass` at the repo root. `tests/verify_pass.py` checks the bundle, the image sizes, the manifest, the signature chain and the `pass.json` content.

**Tech Stack:** Python 3 + Pillow, openssl (LibreSSL), zip, GitHub Pages.

Spec: `docs/superpowers/specs/2026-09-25-wallet-pass-design.md`. Signing assets, outside the repo: `~/.config/magnifica-card/pass/`
(`pass.key`, `pass.pem`, `wwdr.pem`). Team `T76T3LTG9C`, Pass Type ID `pass.com.kaelumvisio.magnifica`.

## File map

| Path | Responsibility |
|---|---|
| `tests/verify_pass.py` | Checks for the pass; exit 0 means pass |
| `build/make-wallet-images.py` | Generates every pass image at its exact size from the approved artwork |
| `wallet/images/*.png` | The generated images: `artwork`, `primaryLogo`, `logo`, `icon` and `thumbnail`, each at @1x, @2x and @3x |
| `wallet/pass.json` | Pass content: `posterGeneric` + `generic` fallback, QR, back fields |
| `build/make-pass.sh` | Manifest → signature → `magnifica.pkpass` |
| `magnifica.pkpass` | The signed, published pass |
| `index.html` | "Add to Apple Wallet" link in the QR overlay |

## Image sizes

Sizes are in pt; @2x and @3x are pixel multiples.

| Image | Size | Rule |
|---|---|---|
| `artwork` (Poster Generic) | 358 × 448 | From the approved art A2; whole cross above the QR band |
| `primaryLogo` | 30 tall, 30–126 wide | A gold cross glyph on a transparent background, no padding |
| `logo` (generic fallback) | 50 tall, ≤ 160 wide | The same glyph |
| `icon` | 38 × 38 | The gold cross on lapis (Lock Screen and notifications) |
| `thumbnail` (generic fallback) | 90 × 90 | The cross cropped from the artwork |

---

### Task 1: The failing checks

- [ ] **Step 1:** Write `tests/verify_pass.py`. It checks:
  - `magnifica.pkpass` exists and unzips flat;
  - the required files are present (`pass.json`, `manifest.json`, `signature`, and every image at @1x/@2x/@3x);
  - each image has its exact pixel size (per the table);
  - the manifest has the SHA-1 of every file except `manifest.json` and `signature`, with nothing missing and nothing extra;
  - the signature holds at least 2 certificates (signer + WWDR), the signer is the pass certificate and verifies against `wwdr.pem`, and the signature over `manifest.json` checks out;
  - in `pass.json`: `formatVersion` is 1, `passTypeIdentifier` and `teamIdentifier` match the certificate (UID and OU), the barcode is a QR with the reader URL as its message, `posterGeneric` and `generic` are both present, the back labels are About / Read it / This card / Note, and `sharingProhibited` is not true;
  - `index.html` links to `magnifica.pkpass` inside `#qrOverlay`.
- [ ] **Step 2:** Run `python3 tests/verify_pass.py`. **Expected: FAIL** (no pass yet).

### Task 2: Images

- [ ] **Step 1:** `build/make-wallet-images.py` does the following:
  - loads the art;
  - saves `artwork` at 358×448, 716×896 and 1074×1344, with a center-cover fit;
  - draws the gold cross glyph (`#ecdca6` with a soft glow) for `primaryLogo` and `logo`;
  - makes `icon` by drawing the glyph on the lapis colour sampled from the art;
  - crops `thumbnail` as a square around the cross;
  - prints the sampled lapis RGB.
- [ ] **Step 2:** Run it, then look at the artwork and icon outputs.

### Task 3: `pass.json`

- [ ] **Step 1:** Write `wallet/pass.json` per the spec:
  - the fields and back text are as approved;
  - `backgroundColor` is the sampled lapis, `foregroundColor` is white, and `labelColor` is `rgb(236, 220, 166)`;
  - the barcode is QR `iso-8859-1` with the alt text "Scan to read";
  - `serialNumber` is `magnifica-card-1`.

### Task 4: Sign, then pass the checks

- [ ] **Step 1:** `build/make-pass.sh` does the following:
  - copies `wallet/` into a temporary folder;
  - writes `manifest.json` with Python `hashlib.sha1`;
  - runs `openssl smime -binary -sign -certfile wwdr.pem -signer pass.pem -inkey pass.key -in manifest.json -out signature -outform DER`;
  - runs `zip -X -q` into `magnifica.pkpass`, with every file flat at the root.
- [ ] **Step 2:** Run it, then `python3 tests/verify_pass.py`. Expected: all PASS.
- [ ] **Step 3 (if an iOS 27 simulator runtime exists):** open the pass in the Simulator and screenshot the real rendering.
- [ ] **Step 4:** Commit. The signed `.pkpass` is committed; keys never are.

### Task 5: Web card link

- [ ] **Step 1:** Ask Juan before downloading Apple's official "Add to Apple Wallet" badge artwork. If he says no, use a plain text link, and don't imitate the badge.
- [ ] **Step 2:** Add the link under the QR card in `#qrOverlay`. Stop propagation so tapping it doesn't also close the overlay.
- [ ] **Step 3:** Bump `CACHE` in `sw.js`, then run both suites (`tests/verify.py` and `tests/verify_pass.py`).

### Task 6: Publish and hand off

- [ ] **Step 1:** Push, and wait for Pages to rebuild.
- [ ] **Step 2:** Run `curl -sI .../magnifica.pkpass`. Expected: `200` and `content-type: application/vnd.apple.pkpass`.
- [ ] **Step 3:** Hand off to Juan: open the card in Safari, tap the QR, tap Add to Apple Wallet, and check the poster on iOS 27.
