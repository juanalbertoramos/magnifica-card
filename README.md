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

`python3 tests/verify.py`, which needs Google Chrome, Node 22+ and Python with OpenCV. It checks:
- the page fits at 390px, and the panel fits on an iPhone SE;
- the Share payload and the clipboard fallback;
- offline rendering through the service worker;
- that the QR decodes to the reader URL.

## Credits

- **Background:** an engraved cross of light in a circuit board ("the light of the Gospel in the black box of AI").
  The still is by Nano Banana Pro and the animation by Kling 3.0 Pro (via fal.ai). It plays forward, then in reverse, as a seamless loop.
- **Fonts:** Cinzel Decorative, Cormorant Garamond and Inter, all under the SIL Open Font License.
- **QR generator:** [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) by Kazuhiko Arase (MIT), used at build time.
- **Text:** the encyclical text in the reader is © Libreria Editrice Vaticana; the reader is an unofficial reader's edition.
