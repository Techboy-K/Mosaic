# -*- coding: utf-8 -*-
"""Copy + optimise every asset the site needs out of the research package."""
import json, os, io, shutil, subprocess
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

R   = '/Users/karim/Desktop/Mosaic/mosaic-restaurant-research/'
W   = '/Users/karim/Desktop/Mosaic/website/'
IMG = W + 'assets/img/'

def jpg(src, dest, width, quality=82):
    im = Image.open(src); im.load()
    if im.mode != 'RGB':
        bg = Image.new('RGB', im.size, (255,255,255))
        im = im.convert('RGBA'); bg.paste(im, mask=im.split()[-1]); im = bg
    if im.width > width:
        im = im.resize((width, round(im.height*width/im.width)), Image.LANCZOS)
    im.save(dest, 'JPEG', quality=quality, optimize=True, progressive=True)
    return im.size

def webp(src, dest, width, quality=78):
    im = Image.open(src); im.load()
    if im.mode not in ('RGB','RGBA'): im = im.convert('RGB')
    if im.width > width:
        im = im.resize((width, round(im.height*width/im.width)), Image.LANCZOS)
    im.save(dest, 'WEBP', quality=quality, method=6)
    return im.size

# ---------------------------------------------------------------- menu data + dish photos
menu = json.load(open(R + 'menu/complete-menu.json'))
out_cats, n_img, missing = [], 0, []
for cat in menu['menus']:
    items = []
    for it in cat['items']:
        slug = str(it['product_id'])
        img_rel = None
        lp = it.get('local_image')
        if lp and os.path.exists(R + lp):
            for w, suffix in ((900,'@2x'), (450,'')):
                try:
                    webp(R+lp, f'{IMG}dishes/{slug}{suffix}.webp', w, 76)
                except Exception as e:
                    missing.append((slug, str(e)[:40])); break
            else:
                img_rel = f'assets/img/dishes/{slug}.webp'; n_img += 1
        else:
            missing.append((slug, 'no local file'))
        items.append({
            'id': it['product_id'], 'name': it['name'], 'desc': it['description'],
            'price': it['price_aed'], 'img': img_rel,
            'url': it.get('source_url',''), 'inStock': it.get('in_stock', True),
        })
    out_cats.append({'name': cat['category'], 'slug': cat['category_url'].rstrip('/').split('/')[-1],
                     'count': cat['item_count'], 'items': items})
json.dump({'currency':'AED','categories':out_cats},
          open(W+'data/menu.json','w'), ensure_ascii=False, separators=(',',':'))
print(f'menu.json  {sum(len(c["items"]) for c in out_cats)} items across {len(out_cats)} categories')
print(f'dish images written: {n_img}   missing: {len(missing)}')
for m in missing[:6]: print('   !', m)

# ---------------------------------------------------------------- brand + rooms + awards
def grab(src, dest, width, q=84, fmt='webp'):
    p = R + src
    if not os.path.exists(p): print('   MISSING', src); return
    (webp if fmt=='webp' else jpg)(p, dest, width, q)

grab('media/other/logo/2131__c0bc6908-de05-46dc-8b3e-ebd6eef1bc70.webp', IMG+'brand/logo.webp', 512, 90)
grab('media/beauty/interior/2555__Muroor-branch-demo-photo-1.png', IMG+'rooms/muroor.webp', 1320, 80)
grab('media/beauty/interior/2556__Najda-branch-demo-photo-1.png',  IMG+'rooms/najda.webp', 1320, 80)
grab('media/beauty/team-staff/2231__team_mosaic-1.png',            IMG+'rooms/team.webp', 1920, 78)
grab('media/beauty/team-staff/4082__DSC06159-scaled.jpg',          IMG+'rooms/kitchen.webp', 1400, 78)
grab('media/beauty/ambience-spread/4144__WhatsApp-Image-2026-08-21-at-15.10.32.jpeg', IMG+'rooms/table.webp', 1920, 78)
grab('media/beauty/ambience-spread/4085__Mosaic3834-scaled.jpg',   IMG+'rooms/platter.webp', 1400, 78)
grab('media/beauty/catering/2519__Frame-201.png',  IMG+'catering/station.webp', 900, 80)
grab('media/beauty/catering/2525__Frame-207.png',  IMG+'catering/canapes.webp', 900, 80)
grab('media/beauty/catering/2518__Frame-202.png',  IMG+'catering/spread.webp', 900, 80)
grab('media/other/award-certificate/4055__Whats-on-2026-scaled.jpeg', IMG+'awards/trophies.webp', 1100, 82)
grab('media/other/award-certificate/4053__Screenshot-2026-06-24-161204.png', IMG+'awards/ceremony.webp', 1100, 82)
grab('media/beauty/team-staff/4124__Untitled-30-June-2026-at-15.59.29-67.webp', IMG+'awards/stage.webp', 1100, 82)
print('brand / rooms / catering / awards done')

# ---------------------------------------------------------------- certificates (already cropped)
CD = '/Users/karim/Desktop/Mosaic/design/certs/'
for f in sorted(os.listdir(CD)):
    webp(CD+f, IMG+'awards/cert-'+f.replace('.jpg','.webp'), 700, 82)
print('certificates:', len(os.listdir(CD)))
