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

const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--autoplay-policy=no-user-gesture-required',
  `--remote-debugging-port=${DEVTOOLS}`, `--user-data-dir=/tmp/magnifica-card-test-${Date.now()}`, 'about:blank'], { stdio: 'ignore' });
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
const shot = async (name) => writeFileSync(join(OUT, name), Buffer.from((await send('Page.captureScreenshot', { format: 'png' })).data, 'base64'));
const viewport = (width, height) => send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 2, mobile: true });
const rect = (sel) => `(() => { const r = document.querySelector('${sel}').getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; })()`;

await send('Page.enable'); await send('Runtime.enable');
mkdirSync(OUT, { recursive: true });
const out = {};

// 1. Layout at iPhone 14/15 size, plus a screenshot for the QR decode
await viewport(390, 844);
await send('Page.navigate', { url: `http://127.0.0.1:${PORT}/` });
await sleep(3000);
Object.assign(out, await evaluate(`(() => {
  const img = document.getElementById('qr'), q = img.getBoundingClientRect(), css = getComputedStyle(document.documentElement);
  return { vw: document.documentElement.clientWidth, sw: document.documentElement.scrollWidth,
           qr: { x: q.x, y: q.y, w: q.width, h: q.height }, qrLoaded: img.naturalWidth > 0, title: document.title,
           videoSrc: document.querySelector('.bg').currentSrc.split('/').pop(),
           tokens: { kicker: css.getPropertyValue('--tc-kicker').trim(), title: css.getPropertyValue('--tc-title').trim(),
                     sub: css.getPropertyValue('--tc-sub').trim() } };
})()`));
await shot('phone-390.png');
out.autoplay = await evaluate(`(async () => { const v = document.querySelector('.bg'), t1 = v.currentTime;
  await new Promise((r) => setTimeout(r, 1200));
  return { paused: v.paused, advanced: v.currentTime > t1, loop: v.loop, muted: v.muted, control: !!document.getElementById('motion') };
})()`);

// 2. Contrast: hide the overlay text, freeze the loop at several moments, capture what sits behind the text
out.contrast = [];
// 390x844: Home Screen app; 390x660: Safari with its toolbars; 390x632: Safari opened from Messages (banner); 375x667: SE
for (const [w, h] of [[390, 844], [390, 660], [390, 632], [375, 667]]) {
  await viewport(w, h); await sleep(400);
  for (const t of [0.4, 2.8, 5.2, 7.6]) {
    await evaluate(`(async () => { const v = document.querySelector('.bg'); v.pause(); v.currentTime = ${t};
      await new Promise((r) => { v.addEventListener('seeked', r, { once: true }); setTimeout(r, 1500); });
      document.documentElement.classList.add('measure-bg'); await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); })()`);
    const file = `bg-${w}x${h}-t${t}.png`;
    await shot(file);
    out.contrast.push({ file, kicker: await evaluate(rect('.kicker')), title: await evaluate(rect('h1')), sub: await evaluate(rect('.sub')) });
    await evaluate(`document.documentElement.classList.remove('measure-bg')`);
  }
}
await evaluate(`document.querySelector('.bg').play().catch(() => {})`);
await viewport(390, 844); await sleep(400);

// 3. A pause saved by the earlier version (with a pause button) must not stop the loop, and is forgotten
await evaluate(`localStorage.setItem('magnifica-motion', 'paused')`);
await send('Page.reload'); await sleep(2500);
out.afterOldPause = await evaluate(`(async () => { const v = document.querySelector('.bg'), t1 = v.currentTime;
  await new Promise((r) => setTimeout(r, 1200));
  return { paused: v.paused, advanced: v.currentTime > t1, saved: localStorage.getItem('magnifica-motion') }; })()`);

// 4. Full-screen QR: opens with focus on Close, scans, closes on Escape with focus back on the QR
out.overlay = { opened: await evaluate(`(async () => { document.getElementById('qrBtn').click();
  await new Promise((r) => setTimeout(r, 350));
  return { visible: !document.getElementById('qrOverlay').hidden, focus: document.activeElement.id }; })()`) };
await shot('qr-overlay.png');
out.overlay.closed = await evaluate(`(async () => { document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
  await new Promise((r) => setTimeout(r, 100));
  return { hidden: document.getElementById('qrOverlay').hidden, focus: document.activeElement.id }; })()`);

// 5. Small phones and landscape: no sideways scroll at 320 px; the whole card reachable in landscape
await viewport(375, 667); await sleep(400);
out.se = await evaluate(`(() => { const p = document.querySelector('.panel').getBoundingClientRect();
  return { panelBottom: p.bottom, vh: innerHeight, sw: document.documentElement.scrollWidth }; })()`);
await viewport(320, 568); await sleep(400);
out.narrow = await evaluate(`({ sw: document.documentElement.scrollWidth, vw: document.documentElement.clientWidth })`);
await viewport(844, 390); await sleep(400);
out.landscape = await evaluate(`(() => { const p = document.querySelector('.panel').getBoundingClientRect();
  return { overflowY: getComputedStyle(document.body).overflowY, panelBottom: p.bottom + scrollY,
           scrollHeight: document.scrollingElement.scrollHeight }; })()`);
await viewport(390, 844); await sleep(400);

// 6. Share: the Web Share payload, then the clipboard fallback when Web Share is unavailable
out.shared = await evaluate(`(async () => {
  Object.defineProperty(navigator, 'share', { configurable: true, value: async (d) => { window.__shared = d; } });
  document.getElementById('share').click(); await new Promise((r) => setTimeout(r, 50)); return window.__shared;
})()`);
out.clipboard = await evaluate(`(async () => {
  Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async (t) => { window.__clip = t; } } });
  document.getElementById('share').click(); await new Promise((r) => setTimeout(r, 50)); return window.__clip;
})()`);

// 7. Offline: once the service worker controls the page, cut the server and reload
await evaluate(`navigator.serviceWorker.ready.then(() => true)`);
await send('Page.reload'); await sleep(2000);
out.controlled = await evaluate(`!!navigator.serviceWorker.controller`);
server.close(); server.closeAllConnections();
await send('Page.reload'); await sleep(2500);
out.offline = await evaluate(`(() => ({ panel: !!document.querySelector('.panel'),
  qrLoaded: (document.getElementById('qr')?.naturalWidth || 0) > 0 }))()`);

console.log(JSON.stringify(out));
ws.close(); chrome.kill();
