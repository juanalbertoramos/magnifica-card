// Browser checks for the Magnifica Card. Serves the project over HTTP, drives headless Chrome over
// the DevTools protocol, and prints one JSON line of measurements for tests/verify.py to assert on.
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { writeFileSync, mkdirSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const OUT = join(ROOT, 'tests', 'out');
const PORT = 8799, DEVTOOLS = 9335;
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.mp4': 'video/mp4', '.woff2': 'font/woff2', '.webmanifest': 'application/manifest+json',
};

const server = createServer(async (req, res) => {
  let path = decodeURIComponent(new URL(req.url, 'http://local').pathname);
  if (path.endsWith('/')) path += 'index.html';
  const file = join(ROOT, path);
  try {
    await stat(file);
    res.writeHead(200, { 'Content-Type': TYPES[extname(file)] || 'application/octet-stream' });
    res.end(await readFile(file));
  } catch {
    res.writeHead(404); res.end('not found');
  }
}).listen(PORT);

const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', `--remote-debugging-port=${DEVTOOLS}`,
  `--user-data-dir=/tmp/magnifica-card-test-${Date.now()}`, 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 40 && !target; i++) {
  await sleep(250);
  try { target = (await (await fetch(`http://127.0.0.1:${DEVTOOLS}/json`)).json()).find((t) => t.type === 'page'); } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
let id = 0; const pending = new Map();
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result ?? m.error); pending.delete(m.id); }
};
await new Promise((r) => (ws.onopen = r));
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async (expression) => (await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result.value;

await send('Page.enable'); await send('Runtime.enable');
const out = {};

// 1. Layout at iPhone 14/15 size, plus a screenshot for the QR decode
await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
await send('Page.navigate', { url: `http://127.0.0.1:${PORT}/` });
await sleep(3000);
Object.assign(out, await evaluate(`(() => {
  const img = document.getElementById('qr'), q = img.getBoundingClientRect();
  return { vw: document.documentElement.clientWidth, sw: document.documentElement.scrollWidth,
           qr: { x: q.x, y: q.y, w: q.width, h: q.height }, qrLoaded: img.naturalWidth > 0, title: document.title };
})()`));
mkdirSync(OUT, { recursive: true });
writeFileSync(join(OUT, 'phone-390.png'), Buffer.from((await send('Page.captureScreenshot', { format: 'png' })).data, 'base64'));

// 2. Small phone (iPhone SE): the whole panel must stay on screen
await send('Emulation.setDeviceMetricsOverride', { width: 375, height: 667, deviceScaleFactor: 2, mobile: true });
await sleep(500);
out.se = await evaluate(`(() => { const p = document.querySelector('.panel').getBoundingClientRect();
  return { panelBottom: p.bottom, vh: innerHeight, sw: document.documentElement.scrollWidth }; })()`);

// 3. Share: the Web Share payload, then the clipboard fallback when Web Share is unavailable
out.shared = await evaluate(`(async () => {
  Object.defineProperty(navigator, 'share', { configurable: true, value: async (d) => { window.__shared = d; } });
  document.getElementById('share').click(); await new Promise((r) => setTimeout(r, 50)); return window.__shared;
})()`);
out.clipboard = await evaluate(`(async () => {
  Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async (t) => { window.__clip = t; } } });
  document.getElementById('share').click(); await new Promise((r) => setTimeout(r, 50)); return window.__clip;
})()`);

// 4. Offline: once the service worker controls the page, cut the server and reload
await evaluate(`navigator.serviceWorker.ready.then(() => true)`);
await send('Page.reload'); await sleep(2000);
out.controlled = await evaluate(`!!navigator.serviceWorker.controller`);
server.close(); server.closeAllConnections();
await send('Page.reload'); await sleep(2500);
out.offline = await evaluate(`(() => ({ panel: !!document.querySelector('.panel'),
  qrLoaded: (document.getElementById('qr')?.naturalWidth || 0) > 0 }))()`);

console.log(JSON.stringify(out));
ws.close(); chrome.kill();
