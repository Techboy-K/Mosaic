# -*- coding: utf-8 -*-
"""
Post-process a generated GLB for web display.

The remesher hands back a FLAT-SHADED mesh: vertices are split per face and each
carries its own face normal, which is exactly what reads as faceted, "edgy" food.
We recompute area-weighted smooth normals across every vertex that shares a
position — without merging the vertex buffer, so UV seams stay intact.
"""
import struct, json, io, sys, os
import numpy as np
from PIL import Image

def pad4(b, fill=b'\x00'):
    return b + fill * ((4 - len(b) % 4) % 4)

CT = {5120:'<i1',5121:'<u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
NC = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}

def refine(src, dest, base_px=1536, base_q=86, aux_px=1024, aux_q=78,
           smooth=True, crease_deg=52.0):
    raw = open(src,'rb').read()
    off, ch = 12, {}
    while off < len(raw):
        l,t = struct.unpack('<I4s', raw[off:off+8]); ch[t] = raw[off+8:off+8+l]; off += 8+l
    j = json.loads(ch[b'JSON']); BIN = ch[b'BIN\x00']
    views = j['bufferViews']
    blobs = [bytearray(BIN[v.get('byteOffset',0): v.get('byteOffset',0)+v['byteLength']]) for v in views]

    def read(ai):
        a = j['accessors'][ai]
        arr = np.frombuffer(bytes(blobs[a['bufferView']]), dtype=CT[a['componentType']])
        n = NC[a['type']]
        return arr.reshape(-1, n) if n > 1 else arr

    # ---- 1. smooth normals -------------------------------------------------
    if smooth:
        for mesh in j.get('meshes', []):
            for prim in mesh['primitives']:
                at = prim['attributes']
                if 'POSITION' not in at or 'NORMAL' not in at or 'indices' not in prim: continue
                P = read(at['POSITION']).astype(np.float64)
                I = read(prim['indices']).astype(np.int64).reshape(-1,3)

                # area-weighted face normals accumulated onto their corners
                v0,v1,v2 = P[I[:,0]],P[I[:,1]],P[I[:,2]]
                fn = np.cross(v1-v0, v2-v0)          # length == 2*area, so it self-weights
                acc = np.zeros_like(P)
                for c in range(3):
                    np.add.at(acc, I[:,c], fn)

                # Share normals across vertices at the same point — but only where the
                # surface is genuinely continuous. Averaging across a real edge (the rim
                # of a plate, the corner of a chip) is what turns food into plasticine,
                # so faces that meet more sharply than the crease angle keep their own.
                key = np.round(P, 5)
                _, inv = np.unique(key, axis=0, return_inverse=True)
                grp = np.zeros((inv.max()+1, 3))
                np.add.at(grp, inv, acc)
                gl = np.linalg.norm(grp, axis=1, keepdims=True)
                gn = np.divide(grp, gl, out=np.zeros_like(grp), where=gl>1e-12)

                al = np.linalg.norm(acc, axis=1, keepdims=True)
                own = np.divide(acc, al, out=np.zeros_like(acc), where=al>1e-12)

                cos_lim = np.cos(np.deg2rad(crease_deg))
                agree = (own * gn[inv]).sum(1)          # how far this corner leans from the group
                N = np.where((agree >= cos_lim)[:,None], gn[inv], own)
                ln = np.linalg.norm(N, axis=1, keepdims=True)
                N = np.divide(N, ln, out=np.zeros_like(N), where=ln>1e-12)
                kept = int((agree < cos_lim).sum())
                print(f'   smoothed {len(N)-kept} verts, kept {kept} crease verts '
                      f'(> {crease_deg:.0f}deg)')

                na = j['accessors'][at['NORMAL']]
                blobs[na['bufferView']] = bytearray(N.astype('<f4').tobytes())
                na['componentType'] = 5126; na['type'] = 'VEC3'; na['count'] = len(N)
                na.pop('min', None); na.pop('max', None)

                # tangents were authored against the split normals; drop them and let
                # three.js derive per-pixel tangents for the normal map instead
                at.pop('TANGENT', None)

    # ---- 2. textures -------------------------------------------------------
    for m in j.get('materials', []):
        if 'normalTexture' in m:
            m['normalTexture']['scale'] = 1.6      # push back the fine surface relief

    base_imgs = set()
    tex2img = {ti: t['source'] for ti,t in enumerate(j.get('textures',[])) if 'source' in t}
    for m in j.get('materials', []):
        bc = m.get('pbrMetallicRoughness', {}).get('baseColorTexture')
        if bc is not None and bc['index'] in tex2img: base_imgs.add(tex2img[bc['index']])

    for ii, img in enumerate(j.get('images', [])):
        vi = img.get('bufferView')
        if vi is None: continue
        px,q = (base_px, base_q) if ii in base_imgs else (aux_px, aux_q)
        im = Image.open(io.BytesIO(bytes(blobs[vi]))).convert('RGB')
        if im.width > px: im = im.resize((px, round(im.height*px/im.width)), Image.LANCZOS)
        b = io.BytesIO(); im.save(b,'JPEG',quality=q,optimize=True,progressive=False)
        blobs[vi] = bytearray(b.getvalue()); img['mimeType'] = 'image/jpeg'

    # ---- 3. narrow indices, drop orphans, repack --------------------------
    for mesh in j.get('meshes', []):
        for prim in mesh['primitives']:
            ai = prim.get('indices')
            if ai is None: continue
            a = j['accessors'][ai]
            if a['componentType'] != 5125: continue
            if j['accessors'][prim['attributes']['POSITION']]['count'] >= 65536: continue
            arr = np.frombuffer(bytes(blobs[a['bufferView']]), dtype='<u4').astype('<u2')
            blobs[a['bufferView']] = bytearray(arr.tobytes()); a['componentType'] = 5123

    live = set()
    for mesh in j.get('meshes', []):
        for prim in mesh['primitives']:
            live.update(prim['attributes'].values())
            if 'indices' in prim: live.add(prim['indices'])
    for ai,a in enumerate(j.get('accessors', [])):
        if ai not in live: a.pop('bufferView', None)

    used = {a['bufferView'] for a in j['accessors'] if 'bufferView' in a}
    used |= {i['bufferView'] for i in j.get('images',[]) if 'bufferView' in i}
    out, cur = bytearray(), 0
    for i,v in enumerate(views):
        data = bytes(blobs[i]) if i in used else b''
        pad = (4-cur%4)%4; out += b'\x00'*pad; cur += pad
        v['byteOffset'] = cur; v['byteLength'] = len(data)
        v.pop('byteStride', None)
        out += data; cur += len(data)
    j['buffers'] = [{'byteLength': len(out)}]

    js = pad4(json.dumps(j, separators=(',',':')).encode(), b' ')
    bn = pad4(bytes(out))
    glb = (b'glTF' + struct.pack('<II', 2, 12+8+len(js)+8+len(bn))
           + struct.pack('<I4s', len(js), b'JSON') + js
           + struct.pack('<I4s', len(bn), b'BIN\x00') + bn)
    open(dest,'wb').write(glb)
    return len(raw), len(glb)

if __name__ == '__main__':
    a,b = refine(sys.argv[1], sys.argv[2])
    print(f'{os.path.basename(sys.argv[1])}: {a/1048576:.2f} MB -> {b/1048576:.2f} MB')
