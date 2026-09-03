# -*- coding: utf-8 -*-
"""Stamp every local css/js reference with a hash of that file's contents.

Assets are served with a long max-age so repeat visits are fast. That is only
safe if the URL changes when the file does — otherwise a browser keeps serving
a stale copy until the cache expires, and a deployed fix appears not to land.
The HTML itself is revalidated on every request, so a new hash is picked up
immediately.

Run after the page generators. Idempotent.
"""
import hashlib, os, re, sys

W = os.path.dirname(os.path.abspath(__file__))
REF = re.compile(r'(?P<attr>src|href)="(?P<path>(?!https?:|//|data:|#)[^"?]+\.(?:js|css))(?:\?v=[0-9a-f]+)?"')
_h = {}

def digest(fs):
    if fs not in _h:
        with open(fs, 'rb') as f:
            _h[fs] = hashlib.sha256(f.read()).hexdigest()[:10]
    return _h[fs]

def main():
    changed = stamped = missing = 0
    for root, dirs, files in os.walk(W):
        dirs[:] = [d for d in dirs if d not in ('assets', '__pycache__', 'data')]
        for name in files:
            if not name.endswith('.html'):
                continue
            page = os.path.join(root, name)
            src = open(page, encoding='utf-8').read()
            miss = []

            def sub(m):
                nonlocal missing
                target = os.path.normpath(os.path.join(root, m.group('path')))
                if not os.path.isfile(target):
                    miss.append(m.group('path')); missing += 1
                    return m.group(0)
                return '%s="%s?v=%s"' % (m.group('attr'), m.group('path'), digest(target))

            out, n = REF.subn(sub, src)
            stamped += n
            for p in miss:
                print('  ! missing asset %s -> %s' % (os.path.relpath(page, W), p), file=sys.stderr)
            if out != src:
                open(page, 'w', encoding='utf-8').write(out)
                changed += 1
    print('versioned %d refs across %d pages%s'
          % (stamped, changed, ' (%d missing)' % missing if missing else ''))
    return 1 if missing else 0

if __name__ == '__main__':
    sys.exit(main())
