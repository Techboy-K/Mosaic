#!/bin/sh
# Mirror only the application source into graphify-src/ so the knowledge graph
# indexes code, not the 1,713 photographs or the duplicated agent-config folders.
set -e
SRC=graphify-src
rm -rf "$SRC"; mkdir -p "$SRC"

copy() {  # copy <relpath> preserving directory structure
  [ -e "$1" ] || return 0
  mkdir -p "$SRC/$(dirname "$1")"
  cp "$1" "$SRC/$1"
}

# public site: generators, page markup, client JS (skip vendored three.js)
for f in website/*.py website/*.html; do copy "$f"; done
for f in website/assets/js/*.js; do copy "$f"; done
for f in website/assets/js/crew/*.js; do copy "$f"; done
for f in website/crew/*.html; do copy "$f"; done
copy website/assets/css/site.css
copy website/assets/css/crew.css
copy website/data/delivery-zones.json

# backend: schema, policies, functions
for f in supabase/migrations/*.sql; do copy "$f"; done
copy supabase/run-sql.py
copy supabase/functions/staff-admin/index.ts

# architecture notes
copy ARCHITECTURE.md

echo "scoped source: $(find "$SRC" -type f | wc -l | tr -d ' ') files"
