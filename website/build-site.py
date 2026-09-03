# -*- coding: utf-8 -*-
"""Generate every page from one shared shell so header/footer never drift."""
import json, os, html

W = os.path.dirname(os.path.abspath(__file__))
MENU = json.load(open(os.path.join(W, 'data', 'menu.json')))

NAV = [("Menu","menu.html"),("Our Story","story.html"),
       ("Catering","catering.html"),("Awards","awards.html"),("Contact","contact.html")]

BRANCHES = [
 dict(name="Al Muroor", addr="Al Sa&rsquo;ada area, Al Rumaithi street<br>Guardian Towers, Abu Dhabi",
      tel="02 234 0202", hotline="600 580 580", img="assets/img/rooms/muroor.webp",
      award="Favourite Casual Middle Eastern Restaurant", body="What&rsquo;s On Abu Dhabi Awards 2026"),
 dict(name="Al Najda", addr="Mohammed Bin Butti street, facing Al Sultan Bakery<br>Vision Towers, Abu Dhabi",
      tel="02 622 6122", hotline="600 580 580", img="assets/img/rooms/najda.webp",
      award="Favourite Business Lunch", body="What&rsquo;s On Abu Dhabi Awards 2026"),
]

SOCIAL = {
 "Instagram":'<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4.1"/><circle cx="17.3" cy="6.7" r=".9" fill="currentColor" stroke="none"/>',
 "Facebook":'<path d="M14.6 8.4V6.9c0-.8.4-1.2 1.3-1.2h1.4V2.9h-2.4c-2.5 0-3.7 1.5-3.7 3.7v1.8H9v2.9h2.2V21h3.4v-9.7h2.4l.4-2.9Z"/>',
 "TikTok":'<path d="M14.2 3h2.6a4.9 4.9 0 0 0 4.2 4.3v2.6a7.5 7.5 0 0 1-4.2-1.4v6.1a5.7 5.7 0 1 1-5.7-5.7c.3 0 .6 0 .9.1v2.7a3 3 0 1 0 2.2 2.9Z"/>',
 "YouTube":'<rect x="2.6" y="5.4" width="18.8" height="13.2" rx="3.6"/><path d="m10.4 9.4 5 2.6-5 2.6Z"/>',
 "LinkedIn":'<rect x="3" y="3" width="18" height="18" rx="2.4"/><path d="M7.4 10.4V17"/><circle cx="7.4" cy="7.2" r="1.1" fill="currentColor" stroke="none"/><path d="M11.6 17v-3.7a2.1 2.1 0 0 1 4.2 0V17"/><path d="M11.6 10.4V17"/>',
}
SOCIAL_URL = {
 "Instagram":"https://www.instagram.com/mosaic.restaurant",
 "Facebook":"https://www.facebook.com/mosaic.lebanese.restaurant",
 "TikTok":"https://www.tiktok.com/@mosaic.ae",
 "YouTube":"https://www.youtube.com/@mosaic.restaurant",
 "LinkedIn":"https://www.linkedin.com/company/mosaic-lebanese-restaurant",
}

def icon(paths, size=18, sw=1.4):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths}</svg>')

I = dict(
 pin='<path d="M12 21.5s7-6.1 7-11.3a7 7 0 1 0-14 0C5 15.4 12 21.5 12 21.5Z"/><circle cx="12" cy="10" r="2.6"/>',
 clock='<circle cx="12" cy="12" r="8.7"/><path d="M12 6.9V12l3.4 2"/>',
 phone='<path d="M6.3 3.5h3l1.6 4-2 1.5a12.4 12.4 0 0 0 5.8 5.8l1.5-2 4 1.6v3a1.7 1.7 0 0 1-1.9 1.7A16.5 16.5 0 0 1 4.6 5.4 1.7 1.7 0 0 1 6.3 3.5Z"/>',
 mail='<rect x="2.8" y="5" width="18.4" height="14" rx="1.6"/><path d="m3.4 6.2 8.6 6.3 8.6-6.3"/>',
 arrow='<path d="M4 12h15.5"/><path d="m13.4 5.9 6.1 6.1-6.1 6.1"/>',
 trophy='<path d="M7 4h10v5a5 5 0 0 1-10 0Z"/><path d="M7 5.5H4.3V7A3.2 3.2 0 0 0 7.5 10.2"/><path d="M17 5.5h2.7V7a3.2 3.2 0 0 1-3.2 3.2"/><path d="M12 14v3.2"/><path d="M8.6 20.3h6.8"/><path d="M9.6 17.2h4.8l1 3.1H8.6Z"/>',
 burger='<path d="M3.5 6.5h17"/><path d="M3.5 12h17"/><path d="M3.5 17.5h17"/>',
 cart='<circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M2.5 3h3l2.4 12.2a1.6 1.6 0 0 0 1.6 1.3h8.3a1.6 1.6 0 0 0 1.6-1.25L21.5 7H6"/>',
 x='<path d="M6 6l12 12"/><path d="M18 6 6 18"/>',
 search='<circle cx="11" cy="11" r="6.7"/><path d="m16 16 4.4 4.4"/>',
 plus='<path d="M12 5v14"/><path d="M5 12h14"/>',
 chev='<path d="m8.5 5 7 7-7 7"/>',
)

def head_html(active):
    cur = ' aria-current="page"'
    nav = "".join(
      '<a href="%s"%s>%s</a>' % (u, cur if u == active else '', n) for n, u in NAV)
    dnav = "".join(f'<a href="{u}">{n}</a>' for n,u in NAV)
    return f"""<header class="site-head">
  <a class="brand" href="index.html">
    <img src="assets/img/brand/logo.webp" alt="" width="44" height="44">
    <span><span class="brand__name">MOSAIC</span><span class="brand__sub">Lebanese Restaurant</span></span>
    <span class="visually-hidden">Mosaic Lebanese Restaurant — home</span>
  </a>
  <nav class="nav" aria-label="Primary">{nav}</nav>
  <div class="head-actions">
    <a class="btn btn--ghost btn--sm" href="menu.html">Order Online</a>
    <a class="btn btn--primary btn--sm" href="contact.html#book">Book a Table</a>
    <button class="cart-btn" type="button" data-cart-open aria-label="Open your order">{icon(I['cart'],19)}
      <span class="cart-btn__n" data-cart-count hidden>0</span></button>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="drawer" aria-label="Open menu">{icon(I['burger'],22)}</button>
  </div>
</header>
<div class="drawer" id="drawer">
  <div class="drawer__top">
    <a class="brand" href="index.html"><img src="assets/img/brand/logo.webp" alt="" width="44" height="44">
      <span><span class="brand__name">MOSAIC</span><span class="brand__sub">Lebanese Restaurant</span></span></a>
    <button class="nav-toggle" type="button" data-drawer-close aria-label="Close menu">{icon(I['x'],22)}</button>
  </div>
  <nav aria-label="Mobile">{dnav}</nav>
  <div class="drawer__cta">
    <a class="btn btn--primary" href="contact.html#book">Book a Table</a>
    <a class="btn btn--ghost" href="menu.html">Order Online</a>
  </div>
</div>"""

def foot_html():
    br = ""
    for b in BRANCHES:
        br += f"""    <div class="foot-col">
      <h4>{b['name']}</h4>
      <p>{b['addr']}</p>
      <a href="tel:{b['tel'].replace(' ','')}" class="num">{b['tel']}</a>
    </div>\n"""
    soc = "".join(f'<a href="{SOCIAL_URL[k]}" target="_blank" rel="noopener" aria-label="{k}">{icon(v,18)}</a>'
                  for k,v in SOCIAL.items())
    return f"""<footer class="site-foot">
  <div class="wrap">
    <div class="foot-grid">
      <div class="foot-col">
        <a class="brand" href="index.html"><img src="assets/img/brand/logo.webp" alt="" width="44" height="44">
          <span><span class="brand__name">MOSAIC</span><span class="brand__sub">Lebanese Restaurant</span></span></a>
        <p style="max-width:280px;margin-top:6px;">A kaleidoscope of Lebanese dishes, served in Abu Dhabi
           across two addresses.</p>
        <div class="socials">{soc}</div>
      </div>
{br}      <div class="foot-col">
        <h4>Opening hours</h4>
        <p class="num">Sat &ndash; Thu &nbsp;8:00 &ndash; 23:30<br>Friday &nbsp;13:30 &ndash; 23:30</p>
        <a href="mailto:info@mosaic-ae.com">info@mosaic-ae.com</a>
        <a href="mailto:catering@mosaic-ae.com">catering@mosaic-ae.com</a>
      </div>
    </div>
    <hr class="hair" style="margin:clamp(28px,4vw,44px) 0 0;">
    <div class="foot-bottom">
      <span>Mosaic Lebanese Restaurant &middot; Abu Dhabi</span>
      <div style="display:flex;gap:20px;flex-wrap:wrap;">
        <a href="#">Mosaic Catering</a><a href="#">La Tartine P&acirc;tisserie</a>
        <a href="#">Nazira Kitchen</a><a href="#">Salatoush</a><a href="#">Space Bun</a>
      </div>
    </div>
  </div>
</footer>"""

def page(fname, title, desc, body, active, extra_css="", extra_js="", cls=""):
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#39497C">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:image" content="assets/img/rooms/table.webp">
<link rel="icon" href="assets/img/brand/logo.webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=PT+Sans:wght@400;700&family=Poppins:wght@300;400;500;600&display=swap">
<link rel="stylesheet" href="assets/css/site.css">
{extra_css}</head>
<body class="{cls}">
{head_html(active)}
<main id="main">
{body}
</main>
{foot_html()}
<script src="assets/js/booking-store.js" defer></script>
<script src="assets/js/cart.js" defer></script>
<script src="assets/js/site.js" defer></script>
{extra_js}</body>
</html>
"""
    open(os.path.join(W, fname), 'w', encoding='utf-8').write(doc)
    return fname
