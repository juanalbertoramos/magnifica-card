// Offline support: the card (and its QR) must open with no signal.
// Bump CACHE whenever a precached file changes, so phones pick up the new copy.
const CACHE = 'magnifica-card-v1';
const ASSETS = [
  './',
  'index.html',
  'bg.jpg',
  'qr.svg',
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

// The loop video is left to the browser: Safari streams it with Range requests, which a cache-first
// worker would break. Offline, the cached poster frame shows in its place.
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET' || new URL(req.url).pathname.endsWith('.mp4')) return;
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).catch(() => caches.match('index.html')));
    return;
  }
  event.respondWith(caches.match(req, { ignoreSearch: true }).then((hit) => hit || fetch(req)));
});
