// Writes qr.svg: the reader URL as a crisp QR (dark on white, 4-module quiet zone, error correction M).
// Run: node build/make-qr.cjs
const fs = require('fs');
const path = require('path');
const qrcode = require('./vendor/qrcode-generator.cjs');

const READER = 'https://juanalbertoramos.github.io/magnifica-humanitas/';
const q = qrcode(0, 'M');
q.addData(READER);
q.make();

const n = q.getModuleCount(), quiet = 4, size = n + 2 * quiet;
let d = '';
for (let r = 0; r < n; r++) {
  for (let c = 0; c < n; c++) if (q.isDark(r, c)) d += `M${c + quiet} ${r + quiet}h1v1h-1z`;
}
const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" shape-rendering="crispEdges">` +
  `<rect width="${size}" height="${size}" fill="#fff"/><path d="${d}" fill="#0d0a06"/></svg>\n`;
fs.writeFileSync(path.join(__dirname, '..', 'qr.svg'), svg);
console.log(`qr.svg: ${n}x${n} modules for ${READER}`);
