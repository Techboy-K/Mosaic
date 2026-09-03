# -*- coding: utf-8 -*-
import importlib.util as _u, json, os
_s=_u.spec_from_file_location('b','build-site.py'); B=_u.module_from_spec(_s); _s.loader.exec_module(B)
icon, I, MENU, BRANCHES = B.icon, B.I, B.MENU, B.BRANCHES

# the six dishes we have real 3D scans for — Mosaic's own showcase order
DISHES = [
 dict(id=3474, name="Chicken Shawarma Saj Plate", cat="Shawarma Plates", price="48", signature=True,
      model="assets/models/shawarma-saj.glb",
      desc="Chicken shawarma wrapped in warm saj bread, topped with garlic paste and served with French fries."),
 dict(id=3026, name="Mutabbal Mosaic", cat="Cold Appetizers", price="39", signature=False,
      model="assets/models/mutabbal.glb",
      desc="Silky purée of grilled eggplant, lemon and tahini, topped with fried eggplant, walnuts and pomegranate."),
 dict(id=3024, name="Mosaic Spicy Hommos", cat="Cold Appetizers", price="35", signature=False,
      model="assets/models/spicy-hommos.glb",
      desc="Smooth chickpea purée with lemon juice and tahini, topped with chilli paste."),
 dict(id=3030, name="Warak Inab Bil Zeit", cat="Cold Appetizers", price="38", signature=False,
      model="assets/models/warak-inab.glb",
      desc="Seven pieces of vine leaves stuffed with rice and herbs."),
 dict(id=3060, name="Grilled Kibbeh Sajiyeh", cat="Hot Appetizers", price="42", signature=False,
      model="assets/models/kibbeh-sajiyeh.glb",
      desc="Chargrilled rustic kibbeh discs of minced meat, burghul and traditional spices."),
 dict(id=2940, name="Mixed Grill 3 Skewers", cat="BBQ Plates", price="97", signature=False,
      model="assets/models/mixed-grill.glb",
      desc="Shish tawook, kabab and lamb tikka, with BBQ tomatoes, onions and pickles."),
]
dots = "".join(f'<button type="button" class="dot{" is-on" if i==0 else ""}" data-i="{i}" '
               f'aria-label="{d["name"]}"></button>' for i,d in enumerate(DISHES))

CSS = """<style>
/* ---------- hero ---------- */
.hero{position:relative;height:260svh;}
.hero__pin{position:sticky;top:0;height:100svh;overflow:hidden;background:var(--sand);}
.hero__film{position:absolute;inset:0;width:100%;height:100%;
  filter:brightness(1.04) saturate(1.05);transform:scale(1.04);}
.hero__scrim{position:absolute;inset:0;background:
  radial-gradient(58% 52% at 50% 47%,rgba(255,255,255,.90) 0%,rgba(255,255,255,.72) 42%,rgba(255,255,255,.30) 72%,rgba(255,255,255,.06) 100%),
  linear-gradient(180deg,rgba(255,255,255,.34) 0%,rgba(255,255,255,0) 26%,rgba(255,255,255,0) 70%,rgba(255,255,255,.66) 100%);}
.hero__copy{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
  justify-content:center;text-align:center;gap:clamp(12px,1.6vh,20px);
  padding:74px var(--pad) 0;}
.hero__welcome{font-family:var(--brandsans);font-size:clamp(10.5px,1.2vw,14px);letter-spacing:.46em;
  text-transform:uppercase;color:var(--wine);font-weight:700;
  text-shadow:0 1px 14px rgba(255,255,255,.98);}
.hero h1{font-size:clamp(40px,7.8vw,112px);line-height:.98;color:var(--wine);
  text-shadow:0 2px 26px rgba(255,255,255,.95), 0 0 60px rgba(255,255,255,.85);}
.hero__sub{font-size:clamp(14px,1.45vw,17.5px);color:var(--ink);max-width:min(520px,84vw);
  font-weight:500;text-shadow:0 1px 16px rgba(255,255,255,.98), 0 0 34px rgba(255,255,255,.9);}
.hero__cta{display:flex;gap:13px;flex-wrap:wrap;justify-content:center;margin-top:6px;}
.hero__cue{position:absolute;left:50%;bottom:24px;transform:translateX(-50%);display:flex;
  flex-direction:column;align-items:center;gap:8px;color:var(--wine);font-weight:600;
  text-shadow:0 1px 12px rgba(255,255,255,.95);font-size:10px;
  letter-spacing:.26em;text-transform:uppercase;}
.hero__cue i{width:2px;height:44px;background:linear-gradient(var(--wine),transparent);
  animation:cue 2.2s ease-in-out infinite;transform-origin:top;}
@keyframes cue{0%,100%{transform:scaleY(.35);opacity:.4}50%{transform:scaleY(1);opacity:1}}

/* ---------- 3D dishes ---------- */
.dishes{position:relative;height:520svh;}
.dishes__pin{position:sticky;top:0;height:100svh;overflow:hidden;
  background:radial-gradient(95% 80% at 50% 32%,#FFFFFF 0%,#F6EFE3 46%,#E7DED3 100%);}
#dish-gl{position:absolute;inset:0;width:100%;height:100%;}
.dishes__top{position:absolute;left:0;right:0;top:clamp(84px,12vh,128px);text-align:center;
  display:flex;flex-direction:column;align-items:center;gap:7px;padding:0 var(--pad);}
.dishes__fade{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,transparent 46%,rgba(247,241,232,.72) 70%,rgba(231,222,211,.96) 100%);}
.dishes__copy{position:absolute;left:0;right:0;bottom:clamp(40px,8vh,96px);text-align:center;
  padding:0 var(--pad);display:flex;flex-direction:column;align-items:center;gap:8px;}
.dishes__copy h3{font-size:clamp(26px,4.4vw,54px);color:var(--wine);}
.dishes__copy p{color:var(--ink-2);font-size:clamp(14px,1.4vw,17px);max-width:min(540px,90vw);}
.price{display:flex;align-items:baseline;gap:8px;margin-top:2px;}
.price b{font-family:var(--display);font-weight:600;font-size:clamp(23px,2.9vw,34px);color:var(--wine);}
.price span{font-size:11px;letter-spacing:.2em;color:var(--faint);}
.dots{display:flex;gap:7px;justify-content:center;margin-top:12px;}
.dot{width:24px;height:2px;background:rgba(20,25,40,.16);border:0;padding:0;cursor:pointer;
  transition:background .35s;}
.dot.is-on{background:var(--gold);}
.dishes__actions{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-top:18px;}
.dishes__hint{font-size:11.5px;color:var(--muted);letter-spacing:.06em;}

/* ---------- story film ---------- */
.film{position:relative;height:400svh;}
.film__pin{position:sticky;top:0;height:100svh;overflow:hidden;background:var(--sand);}
#story-film{position:absolute;inset:0;width:100%;height:100%;}
.film__scrim{position:absolute;inset:0;background:linear-gradient(90deg,
  rgba(255,255,255,.95) 0%,rgba(255,255,255,.86) 38%,rgba(255,255,255,.30) 74%,rgba(255,255,255,.12) 100%);}
.film__lines{position:absolute;inset:0;display:flex;align-items:center;}
.film-line{position:absolute;max-width:min(620px,84vw);opacity:0;
  display:flex;flex-direction:column;gap:15px;will-change:transform,opacity;}
.film-line h3{font-size:clamp(26px,3.6vw,44px);color:var(--wine);}
.film-line p{color:var(--ink-2);font-size:clamp(15px,1.6vw,19px);}

/* ---------- catering ---------- */
.cater{position:relative;height:170svh;}
.cater__pin{position:sticky;top:0;height:100svh;overflow:hidden;}
.cater video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;}
.cater__scrim{position:absolute;inset:0;background:linear-gradient(180deg,
  rgba(255,255,255,.66),rgba(255,255,255,.34) 45%,rgba(255,255,255,.74));}
.cater__copy{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
  justify-content:center;text-align:center;gap:20px;padding:0 var(--pad);}

@media(max-width:760px){
  .dishes{height:460svh;}
  .film{height:360svh;}
}
</style>"""

body = f"""
<!-- ============ 1 · WELCOME ============ -->
<section class="hero" id="hero">
  <div class="hero__pin">
    <canvas class="hero__film" id="hero-film" aria-hidden="true"></canvas>
    <div class="hero__scrim"></div>
    <div class="hero__copy" id="hero-copy">
      <span class="hero__welcome">Welcome to</span>
      <h1>Mosaic<br>Restaurant</h1>
      <span class="orn"><i></i><i></i><i></i></span>
      <p class="hero__sub">A kaleidoscope of mouth-watering Lebanese dishes &mdash; mezze, charcoal
         grills and saj bread, across two addresses in Abu Dhabi.</p>
      <div class="hero__cta">
        <a class="btn btn--primary" href="menu.html">View the Menu</a>
        <a class="btn btn--ghost btn--onlight" href="contact.html#book">Book a Table</a>
      </div>
    </div>
    <div class="hero__cue" id="hero-cue" aria-hidden="true"><i></i>Scroll</div>
  </div>
</section>

<!-- ============ 2 · MENU HIGHLIGHTS (real 3D scans) ============ -->
<section class="dishes" id="dishes" data-dishes='{json.dumps(DISHES).replace("'", "&#39;")}'>
  <div class="dishes__pin">
    <canvas id="dish-gl" aria-hidden="true"></canvas>
    <div class="dishes__fade"></div>
    <div class="dishes__top">
      <span class="eyebrow">A culinary experience</span>
      <span class="dishes__hint">Six of two hundred and fifty &middot; keep scrolling to turn the table</span>
    </div>
    <div class="dishes__copy">
      <span class="eyebrow" id="dish-cat">Shawarma Plates &middot; Signature</span>
      <h3 id="dish-name">Chicken Shawarma Saj Plate</h3>
      <p id="dish-desc">Chicken shawarma wrapped in warm saj bread, topped with garlic paste and served with French fries.</p>
      <div class="price"><b id="dish-price">48</b><span>AED</span></div>
      <div class="dots" id="dish-dots" role="tablist" aria-label="Dish">{dots}</div>
      <div class="dishes__actions">
        <a class="btn btn--primary" href="menu.html">See the full menu &mdash; 250 dishes</a>
        <a class="btn btn--ghost" id="dish-link" href="menu.html">This dish</a>
      </div>
    </div>
  </div>
</section>

<!-- ============ 3 · OUR STORY ============ -->
<section class="film" id="story-film-sec">
  <div class="film__pin">
    <canvas id="story-film" aria-hidden="true"></canvas>
    <div class="film__scrim"></div>
    <div class="film__lines"><div class="wrap" style="width:100%;position:relative;height:60%;">
      <div class="film-line"><span class="eyebrow">Our story</span>
        <h3 style="font-size:clamp(30px,4.6vw,58px);color:var(--wine);">Named after the<br>word &ldquo;Mosaic&rdquo;.</h3></div>
      <div class="film-line"><h3>A hundred small pieces.</h3>
        <p>Only making sense together &mdash; which is exactly how a Lebanese table works.
           Mezze arrives first and never really stops.</p></div>
      <div class="film-line"><h3>Everything made here.</h3>
        <p>Bread off the saj, kibbeh rolled by hand, tabbouleh chopped to order.
           Nothing arrives pre-made.</p></div>
      <div class="film-line"><h3>Come as you are.</h3>
        <p>Not fine dining, not a hotel dining room with a view to lean on &mdash;
           the everyday, bring-the-family version.</p>
        <div><a class="btn btn--ghost" href="story.html">Read our story</a></div></div>
    </div></div>
  </div>
</section>

<!-- ============ 4 · AWARDS ============ -->
<section class="band band--sand">
  <div class="wrap">
    <div class="section-head section-head--center rv">
      <span class="eyebrow">Recognition</span>
      <h2>Decided by the people who eat here.</h2>
      <span class="orn"><i></i><i></i><i></i></span>
      <p class="lede" style="max-width:560px;">Nineteen titles since 2018, most of them public-vote awards
         &mdash; no panel, no jury, no shortlist compiled behind closed doors.</p>
    </div>
    <div class="stats rv">
      <div><span class="n num" data-count="19">0</span><span class="l">titles since 2018</span></div>
      <div><span class="n num" data-count="250">0</span><span class="l">dishes on the menu</span></div>
      <div><span class="n num" data-count="2">0</span><span class="l">addresses in Abu Dhabi</span></div>
      <div><span class="n num" data-count="7">0</span><span class="l">days a week</span></div>
    </div>
    <div class="grid grid--2 rv" style="margin-top:clamp(28px,4vw,48px);align-items:center;">
      <img src="assets/img/awards/trophies.webp" alt="Mosaic&rsquo;s What&rsquo;s On Abu Dhabi 2026 trophies"
           loading="lazy" style="width:100%;">
      <div style="display:flex;flex-direction:column;gap:18px;">
        <h3 style="font-size:clamp(24px,3.2vw,40px);">Two branches. Two titles.<br>One vote that came from you.</h3>
        <p class="lede">Mosaic closed the What&rsquo;s On Abu Dhabi Awards 2026 with two wins in a single evening
           &mdash; Favourite Business Lunch for Al Najda, Favourite Casual Middle Eastern for Al Muroor.</p>
        <div><a class="btn btn--ghost" href="awards.html">See every certificate</a></div>
      </div>
    </div>
  </div>
</section>

<!-- ============ 5 · CATERING ============ -->
<section class="cater">
  <div class="cater__pin">
    <video muted loop playsinline preload="none" poster="assets/img/catering/station.webp"
           data-src="assets/video/catering.mp4" id="cater-vid"></video>
    <div class="cater__scrim"></div>
    <div class="cater__copy">
      <div class="panel" style="max-width:min(720px,92vw);">
        <span class="eyebrow">Mosaic Catering</span>
        <h2 style="font-size:clamp(28px,4.6vw,58px);">Your table, wherever<br>you are putting it.</h2>
        <span class="orn"><i></i><i></i><i></i></span>
        <p class="lede" style="max-width:520px;">Corporate events, weddings, friends at home
           &mdash; personalised service and first-class Lebanese cuisine, with emphasis on taste,
           style and flexibility.</p>
        <a class="btn btn--primary" href="catering.html">Plan an event</a>
      </div>
    </div>
  </div>
</section>

<!-- ============ 6 · FIND US ============ -->
<section class="band" id="find">
  <div class="wrap">
    <div class="section-head section-head--center rv">
      <span class="eyebrow">Find us</span>
      <h2>Two rooms, one kitchen.</h2>
      <span class="orn"><i></i><i></i><i></i></span>
      <p class="lede" style="max-width:520px;">Both in Abu Dhabi, both open seven days.
         Pick the one closest to you &mdash; the menu does not change.</p>
    </div>
    <div class="grid grid--2">
      {"".join(f'''<article class="card rv">
        <img class="card__media" src="{b['img']}" alt="The {b['name']} dining room" loading="lazy">
        <div class="card__body">
          <h3 style="font-size:clamp(22px,2.8vw,30px);">{b['name']}</h3>
          <p style="display:flex;gap:11px;color:var(--muted);font-size:14.5px;">
            <span style="color:var(--faint);flex:none;">{icon(I['pin'],17)}</span><span>{b['addr']}</span></p>
          <p style="display:flex;gap:11px;color:var(--muted);font-size:14px;" class="num">
            <span style="color:var(--faint);flex:none;">{icon(I['clock'],17)}</span>
            <span>Sat&ndash;Thu 8:00&ndash;23:30 &middot; Fri 13:30&ndash;23:30</span></p>
          <p style="display:flex;gap:11px;align-items:center;">
            <span style="color:var(--gold);flex:none;">{icon(I['phone'],17)}</span>
            <a class="num" href="tel:{b['tel'].replace(' ','')}" style="font-size:15px;">{b['tel']}</a></p>
          <div style="display:flex;gap:11px;align-items:center;padding:13px 15px;background:var(--sand);border-radius:4px;margin-top:2px;">
            <span style="color:var(--gold);flex:none;">{icon(I['trophy'],18)}</span>
            <span style="font-size:12.5px;line-height:1.45;">
              <strong style="font-weight:600;">{b['award']}</strong><br>
              <span style="color:var(--faint);font-size:11.5px;">{b['body']}</span></span>
          </div>
          <div style="display:flex;gap:11px;margin-top:auto;padding-top:12px;">
            <a class="btn btn--primary" style="flex:1;min-height:48px;padding:0 12px;" href="contact.html#book">Book</a>
            <a class="btn btn--ghost" style="flex:1;min-height:48px;padding:0 12px;" href="menu.html">Order</a>
          </div>
        </div>
      </article>''' for b in BRANCHES)}
    </div>
  </div>
</section>
"""

JS = """<script src="assets/js/vendor/three.min.js" defer></script>
<script src="assets/js/vendor/GLTFLoader.js" defer></script>
<script src="assets/js/home.js" defer></script>
<script>
/* catering video: only fetch + play when it is actually on screen */
(function(){var v=document.getElementById('cater-vid');if(!v)return;
new IntersectionObserver(function(es){es.forEach(function(e){
  if(e.isIntersecting){ if(!v.src){v.src=v.dataset.src;} v.play().catch(function(){}); }
  else { v.pause(); }});},{threshold:.1}).observe(v);})();
</script>"""

B.page('index.html',
  'Mosaic Lebanese Restaurant — Abu Dhabi',
  'Award-winning Lebanese dining in Abu Dhabi. Mezze, charcoal grills and saj bread at Al Muroor and Al Najda. 250 dishes, open seven days.',
  body, 'index.html', CSS, JS, cls='page-home')
print('index.html written')
