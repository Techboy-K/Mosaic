# -*- coding: utf-8 -*-
"""Shrink a generated GLB: re-encode the baked texture, and narrow 32-bit indices to 16-bit."""
import struct, json, io, sys, os
from PIL import Image
import numpy as np

def pad4(b, fill=b'\x00'):
    return b + fill * ((4 - len(b) % 4) % 4)

def optimise(src, dest, tex_px=1024, tex_q=82, aux_px=512, aux_q=72, drop_tangents=True):
    raw = open(src,'rb').read()
    off, chunks = 12, {}
    while off < len(raw):
        clen, ctype = struct.unpack('<I4s', raw[off:off+8])
        chunks[ctype] = bytearray(raw[off+8:off+8+clen]); off += 8 + clen
    j   = json.loads(chunks[b'JSON'])
    BIN = bytes(chunks[b'BIN\x00'])
    views = j['bufferViews']

    # pull every bufferView out so we can rebuild the buffer cleanly
    blobs = [BIN[v.get('byteOffset',0): v.get('byteOffset',0)+v['byteLength']] for v in views]

    # 1. textures. baseColor carries the visible detail so it keeps the most
    #    resolution; roughness/metallic and normal maps survive smaller.
    base_idx = set()
    for m in j.get('materials', []):
        bc = m.get('pbrMetallicRoughness', {}).get('baseColorTexture')
        if bc is not None: base_idx.add(bc['index'])
    tex2img = {}
    for ti, t in enumerate(j.get('textures', [])):
        if 'source' in t: tex2img[ti] = t['source']
    base_imgs = {tex2img.get(i) for i in base_idx}

    for ii, img in enumerate(j.get('images', [])):
        vi = img.get('bufferView')
        if vi is None: continue
        is_base = ii in base_imgs
        px, q = (tex_px, tex_q) if is_base else (aux_px, aux_q)
        im = Image.open(io.BytesIO(blobs[vi])).convert('RGB')
        if im.width > px:
            im = im.resize((px, round(im.height*px/im.width)), Image.LANCZOS)
        b = io.BytesIO(); im.save(b,'JPEG',quality=q,optimize=True,progressive=False)
        blobs[vi] = b.getvalue(); img['mimeType'] = 'image/jpeg'

    # 1b. TANGENT is 16 bytes/vertex and three.js derives it from the normal map
    #     with screen-space derivatives, so it is dead weight on the wire.
    if drop_tangents:
        for mesh in j.get('meshes', []):
            for prim in mesh['primitives']:
                prim['attributes'].pop('TANGENT', None)

    # 2. uint32 -> uint16 indices when the mesh is small enough
    for mesh in j.get('meshes', []):
        for prim in mesh['primitives']:
            ai = prim.get('indices')
            if ai is None: continue
            acc = j['accessors'][ai]
            if acc['componentType'] != 5125: continue           # already narrow
            nverts = j['accessors'][prim['attributes']['POSITION']]['count']
            if nverts >= 65536: continue
            vi = acc['bufferView']
            arr = np.frombuffer(blobs[vi], dtype='<u4').astype('<u2')
            blobs[vi] = arr.tobytes(); acc['componentType'] = 5123

    # which accessors is anything still pointing at?
    live_acc = set()
    for mesh in j.get('meshes', []):
        for prim in mesh['primitives']:
            live_acc.update(prim['attributes'].values())
            if 'indices' in prim: live_acc.add(prim['indices'])
            for tgt in prim.get('targets', []): live_acc.update(tgt.values())
    for sk in j.get('skins', []):
        if 'inverseBindMatrices' in sk: live_acc.add(sk['inverseBindMatrices'])
    for an in j.get('animations', []):
        for sm in an.get('samplers', []):
            live_acc.add(sm['input']); live_acc.add(sm['output'])

    # orphaned accessors keep their entry (indices are positional) but lose their data
    for ai, a in enumerate(j.get('accessors', [])):
        if ai not in live_acc:
            a.pop('bufferView', None)

    used = set()
    for a in j.get('accessors', []):
        if 'bufferView' in a: used.add(a['bufferView'])
    for im in j.get('images', []):
        if 'bufferView' in im: used.add(im['bufferView'])
    for i in range(len(blobs)):
        if i not in used: blobs[i] = b''

    # rebuild buffer with fresh 4-byte-aligned offsets
    out, cursor = bytearray(), 0
    for i, v in enumerate(views):
        pad = (4 - cursor % 4) % 4
        out += b'\x00'*pad; cursor += pad
        v['byteOffset'] = cursor
        v['byteLength'] = len(blobs[i])
        v.pop('byteStride', None) if v.get('byteStride') in (0,None) else None
        out += blobs[i]; cursor += len(blobs[i])
    j['buffers'] = [{'byteLength': len(out)}]

    js = pad4(json.dumps(j, separators=(',',':')).encode('utf-8'), b' ')
    bn = pad4(bytes(out))
    glb = (b'glTF' + struct.pack('<II', 2, 12 + 8+len(js) + 8+len(bn))
           + struct.pack('<I4s', len(js), b'JSON') + js
           + struct.pack('<I4s', len(bn), b'BIN\x00') + bn)
    open(dest,'wb').write(glb)
    return len(raw), len(glb)

if __name__ == '__main__':
    a,b = optimise(sys.argv[1], sys.argv[2])
    print(f'{os.path.basename(sys.argv[1])}: {a/1048576:.2f} MB -> {b/1048576:.2f} MB  ({100*b/a:.0f}%)')
