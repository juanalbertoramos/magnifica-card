# Magnifica Card — design spec

**Date:** 2026-09-25 · **Status:** design approved in conversation (cross A chosen); awaiting spec review

## Purpose

A standalone, phone-first "share card" Juan keeps on his iPhone Home Screen to share the
*Magnifica Humanitas* e-reader. In person, people scan the QR. Remotely, Juan taps **Share** and
sends the link by WhatsApp, Messages, Mail, AirDrop or Copy. The deployed reader
(`juanalbertoramos.github.io/magnifica-humanitas/`) is **not modified**.

## Agreed design

- **One screen, English only.** No language switch, no flip.
- **Background:** a seamless ~10 s loop. It is a Kling 3.0 Pro clip of the engraved Latin cross
  of golden light in a dark circuit board, played forward then reversed. The idea is the light
  of the Gospel entering the "black box" of AI. The poster frame paints instantly, and the still
  shows in Low Power Mode and under `prefers-reduced-motion`.
- **Foreground, top to bottom:**
  - the kicker *Pope Leo XIV · First Encyclical*;
  - the title *Magnifica Humanitas* (Cinzel Decorative, gold gradient);
  - the official English subtitle;
  - a dark frosted-glass panel with the QR (dark on a white tile), the caption, "Open it here ›" and one gold **Share** button.
- **Share button:**
  - It calls `navigator.share({ title, text, url })`, which opens the iOS share sheet.
  - If Web Share isn't available, it copies the message and link to the clipboard and shows a toast.
  - The message reads: *Pope Leo XIV's first encyclical, Magnifica Humanitas, on safeguarding the
    human person in the time of artificial intelligence. A beautiful edition you can read or
    listen to on your phone:* followed by the reader URL.

## Files

| File | Role |
|---|---|
| `index.html` | The whole page, with CSS and JS inline. The QR is pre-rendered as inline SVG at build time, so there is no runtime QR library |
| `bg.mp4` | The loop: H.264, muted, target ≤ 3 MB |
| `bg.jpg` | The poster frame; also the `og:image` |
| `fonts/` | Cinzel Decorative, Cormorant Garamond italic and Inter (all SIL OFL), copied from the reader |
| `manifest.webmanifest`, `apple-touch-icon.png` | Home Screen app: standalone, dark theme |
| `sw.js` | Offline cache of everything above, so the QR still shows with no signal |
| `build/` | The QR generator script (Kazuhiko Arase's qrcode-generator, MIT, notice kept) and the video encode commands |

## Hosting

A new public GitHub repo, `magnifica-card`, served by GitHub Pages at
`https://juanalbertoramos.github.io/magnifica-card/`. It is published **only on Juan's explicit
go-ahead**.

## Verification

1. It renders at a true 390×844 phone width with no horizontal overflow (CDP render, `scrollWidth`).
2. The QR decodes to the reader URL (OpenCV) from the rendered page.
3. The Share payload is correct, and the clipboard fallback works in a desktop browser.
4. The service worker caches everything, and the page loads with the network off.
5. On Juan's iPhone:
   - Add to Home Screen;
   - share to WhatsApp and to Messages;
   - scan from a second phone;
   - in Low Power Mode, the poster shows.

## Out of scope

Changes to the reader, analytics, a custom domain, other languages, and a printed QR.
