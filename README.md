# Magnifica Card

A share card for the [Magnifica Humanitas reader](https://juanalbertoramos.github.io/magnifica-humanitas/), Pope Leo XIV's
first encyclical, *On Safeguarding the Human Person in the Time of Artificial Intelligence*.

Open it on an iPhone in Safari and choose **Share → Add to Home Screen**. Then:
- in person, people scan the QR;
- anywhere else, tap **Share** to send the reader link by WhatsApp, Messages, Mail, AirDrop or Copy.

**Live:** https://juanalbertoramos.github.io/magnifica-card/

## Updating

- **Text, links or styling:** edit `index.html`.
- **Changing a cached file** (images, fonts, `qr.svg`, icons, `index.html`): bump `CACHE` in `sw.js` so installed phones fetch the new copy.
- **The background:** `zsh build/encode.sh` rebuilds `bg.mp4` and `bg.jpg` from the Kling source clip.
- **The QR:** `node build/make-qr.cjs` rewrites `qr.svg` for the reader URL.
- **The icons:** `python3 build/make-icons.py`.

## Verify

`python3 tests/verify.py`, which needs Google Chrome, Node 22+ and Python with OpenCV and numpy. It runs 58 checks:
- **Layout:** no sideways overflow at 390 and 320 px; the whole panel on screen on an iPhone SE; landscape scrolls.
- **Contrast:** the eyebrow, title and subtitle each keep **≥ 4.5:1** against the brightest nearby pixel. That's
  measured at 9 points, on 4 frames of the loop, at 2 phone sizes, with the text hidden.
- **QR:** the tile is ≥ 148 px and decodes to the reader URL. The full-screen QR (tap the code) also decodes, with
  focus moving to Close and back (Escape closes it).
- **Pause control (WCAG 2.2.2):** it pauses and resumes the loop, reports its state, and is remembered on the device.
- **Share:** the Share payload, and the clipboard fallback.
- **Offline:** the page renders through the service worker with the server cut.

## Video encodes

Both files are the same seamless 10 s loop at 1080 px wide. Each was scored with VMAF against a near-lossless reference:

| File | Codec | Size | VMAF |
|---|---|---|---|
| `bg-hevc.mp4` | HEVC (x265, CRF 28), listed first for Apple devices | 1.39 MB | 93.3 |
| `bg.mp4` | H.264 (x264, CRF 26), fallback for everyone else | 2.01 MB | 91.0 |

AV1 (SVT-AV1, CRF 38) scored 93.5 at 1.10 MB. It's left out because iPhones decode AV1 only from the iPhone 15 Pro onward.

## Credits

- **Background:** an engraved cross of light in a circuit board ("the light of the Gospel in the black box of AI").
  The still is by Nano Banana Pro and the animation by Kling 3.0 Pro (via fal.ai). It plays forward, then in reverse, as a seamless loop.
- **Fonts:** Cinzel Decorative, Cormorant Garamond and Inter, all under the SIL Open Font License.
- **QR generator:** [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) by Kazuhiko Arase (MIT), used at build time.
- **Text:** the encyclical text in the reader is © Libreria Editrice Vaticana; the reader is an unofficial reader's edition.
