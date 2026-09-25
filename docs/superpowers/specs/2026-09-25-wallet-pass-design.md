# Magnifica Wallet pass — design spec

**Date:** 2026-09-25 · **Status:** design approved (front A "Illuminated Icon", refined; back and QR approved); awaiting spec review

## Purpose

An Apple Wallet pass that sits alongside the web card. Juan double-clicks the side button, Wallet opens,
he shows the QR, and people scan it to reach the reader. The web card stays as it is for the animated
presentation and the Share sheet.

## Design (approved)

**Pass style:** `posterGeneric` (iOS 27+), with a `generic` fallback in the same `pass.json`. Wallet picks the
poster style when it can, and older iPhones get the classic layout.

**Front (Poster Generic)**

| Element | Content |
|---|---|
| Artwork (`artwork.png`, 358×448 pt) | Front A refined: a gold cross with a circuit-ring halo on lapis blue. The whole cross sits between 12% and 48% of the height, above the QR |
| Primary logo (`primaryLogo.png`, 30 pt tall) | A small gold cross glyph |
| Header field | Label "Encyclical", value "Pope Leo XIV" |
| Primary fields | A bold title "Magnifica Humanitas" (no label, which gives the bold style), plus "Dated · 15 May 2026" |
| Footer field | "Scan to read · The human person & AI" |
| Barcode | QR → `https://juanalbertoramos.github.io/magnifica-humanitas/` |

**Back** (approved):
- "About", a short description;
- "Read it", a link to the reader;
- "This card", a link to `https://juanalbertoramos.github.io/magnifica-card/`;
- "Note": "An unofficial reader's edition. Text © Libreria Editrice Vaticana."

**Fallback (generic, iOS 26 and earlier):**
- a logo (the gold cross) with the logo text "Magnifica Humanitas";
- a thumbnail (the cross, cut from the artwork);
- a primary field "Pope Leo XIV" (labelled "Encyclical"), and a secondary field "Dated · 15 May 2026";
- the same QR and back.

**Colours:** the background is sampled from the artwork's lapis, the foreground is white, and labels are gold `#ecdca6`.

**Other settings:**
- **No featured actions:** Apple only allows fixed types (schedule, music, maps, shop, bookings…) with system labels, and none honestly means "read".
- **Sharing is allowed** (`sharingProhibited: false`).

**Web card:** Apple's official **"Add to Apple Wallet"** badge sits in the full-screen QR view. It links to
`magnifica.pkpass`, which is hosted on the card site. The main card layout is unchanged, so the crossbar test still holds.

## Identity and signing

- **Pass fields:**
  - `passTypeIdentifier` is `pass.com.kaelumvisio.magnifica`, which is invisible to users and a reusable prefix for Kaelum Visio passes;
  - `serialNumber` is `magnifica-card-1`;
  - `organizationName` is "Magnifica Humanitas";
  - `teamIdentifier` is read from the certificate.
- **Private key:** generated on Juan's Mac in `~/.config/magnifica-card/pass/` (directory 0700, key 0600).
  **Never in iCloud and never in the public repo.** Only the signed `magnifica.pkpass` is published.
- **Certificate:** Juan creates a Pass Type ID certificate from our certificate request (CSR) in his developer
  account, then downloads `pass.cer`. It's used together with Apple's WWDR G4 intermediate certificate.
- **Signing:** `manifest.json` lists the SHA-1 of every file. It gets a detached PKCS#7 signature
  (`openssl smime`, which includes the WWDR certificate). The files are then zipped into `magnifica.pkpass`.

## Files

| Path | Role |
|---|---|
| `wallet/pass.json` | Pass definition (poster + generic fallback) |
| `wallet/images/` | `artwork`, `primaryLogo`, `logo`, `icon` and `thumbnail`, at @2x and @3x, generated at exact sizes |
| `build/make-wallet-images.py` | Produces every image from the approved artwork |
| `build/make-pass.sh` | Builds the manifest, signs and zips. It reads the key and certificate from `~/.config/magnifica-card/pass/` |
| `magnifica.pkpass` | The signed pass, published |
| `tests/verify_pass.py` | Pass checks (see below) |

## Verification

1. **Automated:** `tests/verify_pass.py` checks that:
   - the bundle has every required file;
   - each image is at its exact pixel size;
   - the manifest hashes match;
   - the signature verifies against Apple's WWDR chain;
   - the QR message is the reader URL;
   - `pass.json` is valid.

   The existing web-card suite still passes.
2. **Live:** GitHub Pages serves `magnifica.pkpass` as `application/vnd.apple.pkpass`.
3. **On Juan's iPhone:**
   - "Add to Apple Wallet" works from Safari;
   - the poster layout shows on iOS 27;
   - a second phone can scan the QR;
   - the pass can be shared.
4. **Optional:** an exact preview in Apple's Pass Designer (macOS 27).

## Out of scope

Server updates and push to installed passes, featured actions, Google Wallet, and location or time relevance.
