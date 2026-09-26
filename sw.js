// Offline support: the card (and its QR) must open with no signal.
// Bump CACHE whenever a precached file changes, so phones pick up the new copy.
const CACHE = 'magnifica-card-v6';
const ASSETS = [
  './',
  'index.html',
  'bg.jpg',
  'qr.svg',
  'add-to-apple-wallet.svg',
  'manifest.webmanifest',
  'apple-touch-icon.png',
  'icon-512.png',
  'fonts/cinzel-decorative-700.woff2',
  'fonts/cormorant-garamond-italic.woff2',
  'fonts/inter.woff2',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

// The loop video and the Wallet pass are left to the browser: Safari streams the video with Range requests,
// which a cache-first worker would break, and hands the pass straight to Wallet. Offline, the cached poster
// frame shows in the video's place.
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET' || /\.(mp4|pkpass)$/.test(new URL(req.url).pathname)) return;
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).catch(() => caches.match('index.html')));
    return;
  }
  event.respondWith(caches.match(req, { ignoreSearch: true }).then((hit) => hit || fetch(req)));
});
