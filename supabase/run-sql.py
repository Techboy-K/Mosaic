#!/usr/bin/env python3
"""Apply a .sql file to the Mosaic Supabase project via the Management API."""
import json, os, sys, urllib.request

env = {}
for line in open(os.path.join(os.path.dirname(__file__), '..', '.secrets', 'supabase.env')):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1); env[k] = v

def run(sql, label=''):
    req = urllib.request.Request(
        f"https://api.supabase.com/v1/projects/{env['SUPABASE_PROJECT_REF']}/database/query",
        data=json.dumps({'query': sql}).encode(),
        headers={'Authorization': 'Bearer ' + env['SUPABASE_ACCESS_TOKEN'],
                 'Content-Type': 'application/json',
                 'User-Agent': 'mosaic-crew-migrator/1.0',
                 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return True, json.loads(r.read().decode() or '[]')
    except urllib.error.HTTPError as e:
        return False, e.read().decode()[:600]

if __name__ == '__main__':
    for path in sys.argv[1:]:
        ok, out = run(open(path).read(), path)
        name = os.path.basename(path)
        if ok:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}\n     {out}")
            sys.exit(1)
