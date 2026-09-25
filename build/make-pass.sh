#!/bin/zsh
# Builds magnifica.pkpass: copies wallet/ sources into a scratch folder, writes manifest.json (SHA-1 of every
# file), signs it (detached PKCS#7 with the Pass Type ID certificate plus Apple's WWDR G4 intermediate), then
# zips everything flat. Keys live outside the repo: ~/.config/magnifica-card/pass/ (override: MAGNIFICA_PASS_KEYS).
# Usage: zsh build/make-pass.sh
set -e
ROOT="${0:A:h:h}"
KEYS="${MAGNIFICA_PASS_KEYS:-$HOME/.config/magnifica-card/pass}"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

cp "$ROOT/wallet/pass.json" "$WORK/"
cp "$ROOT"/wallet/images/*.png "$WORK/"

python3 - "$WORK" <<'EOF'
import hashlib, json, sys
from pathlib import Path
work = Path(sys.argv[1])
manifest = {p.name: hashlib.sha1(p.read_bytes()).hexdigest() for p in sorted(work.iterdir()) if p.is_file()}
(work / "manifest.json").write_text(json.dumps(manifest, indent=2))
EOF

openssl smime -binary -sign -certfile "$KEYS/wwdr.pem" -signer "$KEYS/pass.pem" -inkey "$KEYS/pass.key" \
  -in "$WORK/manifest.json" -out "$WORK/signature" -outform DER

rm -f "$ROOT/magnifica.pkpass"
(cd "$WORK" && zip -q -X "$ROOT/magnifica.pkpass" pass.json manifest.json signature *.png)
printf 'built %s  (%.2f MB)\n' "$ROOT/magnifica.pkpass" "$(( $(stat -f%z "$ROOT/magnifica.pkpass") / 1e6 ))"
