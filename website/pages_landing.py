# -*- coding: utf-8 -*-
"""Landing page: one film, scrubbed by scroll, with copy pinned to each beat."""
import importlib.util as _u
_s=_u.spec_from_file_location('b','build-site.py'); B=_u.module_from_spec(_s); _s.loader.exec_module(B)
icon, I = B.icon, B.I

# dish, price, category, the beat it belongs to, and which side of the frame is free
DISHES = [
 ('d1',3473,'Chicken Shawarma Saj Plate','Shawarma Plates','48','right',
  'Chicken shawarma wrapped in warm saj bread, topped with garlic paste and served with French fries.','Signature'),
 ('d2',2939,'Mixed Grill 3 Skewers','BBQ Plates','97','left',
  'Shish tawook, kabab and lamb tikka, with BBQ tomatoes, onions and pickles.',''),
 ('d3',3059,'Grilled Kibbeh Sajiyeh','Hot Appetizers','42','left',
  'Chargrilled rustic kibbeh discs of minced meat, burghul and traditional spices, finished with walnuts.',''),
 ('d4',3029,'Warak inab Bizet','Cold Appetizers','38','right',
  'Seven pieces of vine leaves stuffed with rice and herbs.',''),
 ('d5',3023,'Mosaic Spicy Hommos','Cold Appetizers','35','left',
  'Smooth chickpea pur&eacute;e with lemon juice and tahini, topped with chilli paste and pine nuts.',''),
 ('d6',3025,'Mutabbal Mosaic','Cold Appetizers','39','left',
  'Silky pur&eacute;e of grilled eggplant, lemon and tahini, topped with fried eggplant, walnuts and pomegranate.',''),
]

def dish_beat(bid,mid,name,cat,price,side,desc,tag):
    return f'''
  <div class="beat beat--{side}" id="beat-{bid}">
    <div class="dishcard">
      <span class="dishcard__cat">{cat}{' &middot; ' + tag if tag else ''}</span>
      <h2>{name}</h2>
      <p>{desc}</p>
      <div class="dishcard__p"><b>{price}</b><span>AED</span></div>
      <div class="dishcard__act">
        <button class="btn btn--primary btn--sm" type="button" data-add
                data-id="{mid}" data-name="{name}" data-price="{price}">Order this</button>
        <a class="btn btn--ghost btn--sm btn--onlight" href="menu.html">See full menu</a>
      </div>
    </div>
  </div>'''

beats = "".join(dish_beat(*d) for d in DISHES)

body = f'''
<div class="film" id="track">
  <div class="film__stage" id="stage">
    <video id="film" class="film__v" muted playsinline preload="auto"
           poster="assets/img/rooms/landing-poster.webp"
           src="assets/video/landing.mp4"></video>
    <div class="film__wash"></div>

    <!-- 1 · the room -->
    <div class="beat beat--center" id="beat-welcome">
      <span class="film__eyebrow">Mosaic Restaurant &middot; Abu Dhabi</span>
      <h1>Welcome to<br>our table.</h1>
      <span class="orn"><i></i><i></i><i></i></span>
      <p class="film__sub">Authentic Lebanese cuisine in Abu Dhabi &mdash; two rooms,
         one kitchen, and a table that never really stops arriving.</p>
      <div class="film__cta">
        <a class="btn btn--primary" href="menu.html">View the menu</a>
        <a class="btn btn--ghost btn--onlight" href="contact.html#book">Book a table</a>
      </div>
    </div>

    <!-- 2 · the table -->
    <div class="beat beat--low" id="beat-table">
      <span class="film__eyebrow">Dine with us</span>
      <h2>A table, laid.</h2>
      <p class="film__sub">Mezze first. Then the grill. Then more bread.</p>
    </div>
{beats}

    <!-- 9 · menu CTA -->
    <div class="beat beat--center" id="beat-menucta">
      <span class="film__eyebrow">Two hundred and fifty dishes</span>
      <h2>That was six of them.</h2>
      <p class="film__sub">Nineteen categories, one menu, served the same way at both
         addresses from eight in the morning until half past eleven at night.</p>
      <div class="film__cta"><a class="btn btn--primary" href="menu.html">See the full menu</a></div>
    </div>

    <!-- 10 · awards on the wall -->
    <div class="beat beat--lowleft" id="beat-awards">
      <div class="dishcard dishcard--wide">
        <span class="dishcard__cat">Recognition</span>
        <h2>Decided by the people<br>who eat here.</h2>
        <p>Nineteen awards since 2018, most of them won on public vote &mdash; including
           What&rsquo;s On Abu Dhabi 2026 for Favourite Business Lunch and Favourite Casual
           Middle Eastern, Tripadvisor Best of the Best, and BBC Good Food Middle East.</p>
        <a class="btn btn--ghost btn--sm btn--onlight" href="awards.html">Every certificate</a>
      </div>
    </div>

    <!-- 11 · mosaics -->
    <div class="beat beat--center beat--band" id="beat-mosaic">
      <span class="film__eyebrow">Our story</span>
      <h2>Named after the<br>word &ldquo;Mosaic&rdquo;.</h2>
      <p class="film__sub">A hundred small pieces that only make sense together &mdash;
         which is exactly how a Lebanese table works.</p>
    </div>

    <!-- 12 · the spread -->
    <div class="beat beat--center" id="beat-spread">
      <h2>Everything, at once.</h2>
      <p class="film__sub">The way it is meant to be eaten. Bring people.</p>
      <div class="film__cta">
        <a class="btn btn--primary" href="catering.html">Mosaic Catering</a>
        <a class="btn btn--ghost btn--onlight" href="story.html">Our story</a>
      </div>
    </div>

    <!-- 13 · book -->
    <div class="beat beat--center" id="beat-book">
      <span class="film__eyebrow">Find us</span>
      <h2>Two rooms,<br>one kitchen.</h2>
      <div class="film__branches">
        <a href="contact.html#book"><b>Al Muroor</b><span>Guardian Towers</span><i>02 234 0202</i></a>
        <a href="contact.html#book"><b>Al Najda</b><span>Vision Towers</span><i>02 622 6122</i></a>
      </div>
      <p class="film__sub film__sub--sm">Sat&ndash;Thu 8:00&ndash;23:30 &middot; Fri 13:30&ndash;23:30</p>
      <div class="film__cta"><a class="btn btn--primary" href="contact.html#book">Book a table</a></div>
    </div>

    <div class="film__cue" id="film-cue"><i></i>Scroll</div>
    <div class="film__prog"><span id="film-bar"></span></div>
    <nav class="film__rail" aria-label="Jump to a moment">
      <a href="#" data-jump="welcome" title="Welcome"></a>
      <a href="#" data-jump="d1" title="The dishes"></a>
      <a href="#" data-jump="menucta" title="The menu"></a>
      <a href="#" data-jump="awards" title="Awards"></a>
      <a href="#" data-jump="spread" title="The table"></a>
      <a href="#" data-jump="book" title="Find us"></a>
    </nav>
  </div>
</div>
'''

CSS = '''<style>
.film{position:relative; height:1100svh;}
.film__stage{position:sticky; top:0; height:100svh; overflow:hidden; background:#0d0f16;}
.film__v{position:absolute; inset:0; width:100%; height:100%; object-fit:cover;}
.film__wash{position:absolute; inset:0; pointer-events:none;
  background:
    radial-gradient(58% 46% at 50% 44%, rgba(255,255,255,.34) 0%, rgba(255,255,255,0) 72%),
    linear-gradient(180deg, rgba(255,255,255,.30) 0%, rgba(255,255,255,0) 22%,
                    rgba(255,255,255,0) 72%, rgba(255,255,255,.34) 100%);}
body:not(.film-ready) .film__v{opacity:0;}

.beat{position:absolute; inset:0; display:flex; flex-direction:column; justify-content:center;
  gap:clamp(10px,1.5vh,18px); padding:clamp(70px,9vh,120px) clamp(22px,6vw,90px);
  opacity:0; will-change:opacity,transform;}
.beat--center{align-items:center; text-align:center;}
.beat--center::before{content:""; position:absolute; left:50%; top:50%;
  width:min(900px,92vw); height:min(560px,72vh); transform:translate(-50%,-50%);
  background:radial-gradient(ellipse at center, rgba(255,255,255,.72) 0%,
    rgba(255,255,255,.42) 45%, rgba(255,255,255,0) 72%);
  pointer-events:none; z-index:-1;}
.beat--center > *{position:relative;}
.beat--low{align-items:center; text-align:center; justify-content:flex-end;
  padding-bottom:clamp(80px,14vh,170px);}
.beat--low::before{content:""; position:absolute; left:50%; bottom:0;
  width:min(1000px,100vw); height:min(420px,52vh); transform:translateX(-50%);
  background:radial-gradient(ellipse at 50% 78%, rgba(255,255,255,.74) 0%,
    rgba(255,255,255,.44) 46%, rgba(255,255,255,0) 74%);
  pointer-events:none; z-index:-1;}
.beat--low > *{position:relative;}
.beat--left{align-items:flex-start;}
/* The mosaic frames fill 26–68% of the shot. This beat names them, so it has to
   sit in the clear strip underneath rather than covering them. */
.beat--band .film__sub{max-width:min(560px,80vw);}
/* Centred over the framed mosaics, so the lift is tightened to the copy itself
   — the artwork behind still has to read. */
.beat--band::before{width:min(660px,86vw); height:min(360px,46vh);
  background:radial-gradient(ellipse at center, rgba(255,255,255,.86) 0%,
    rgba(255,255,255,.60) 42%, rgba(255,255,255,0) 73%);}
.beat--lowleft{align-items:flex-start; justify-content:flex-end;
  padding-bottom:clamp(56px,9vh,110px);}
.beat--right{align-items:flex-end;}

.film__eyebrow{font-family:var(--brandsans); font-size:clamp(10px,1.1vw,12.5px);
  letter-spacing:.4em; text-transform:uppercase; color:var(--wine); font-weight:700;
  text-shadow:0 1px 14px rgba(255,255,255,.95);}
.film h1{font-size:clamp(38px,7.4vw,104px); line-height:.98; color:var(--wine);
  text-shadow:0 2px 30px rgba(255,255,255,.95), 0 0 70px rgba(255,255,255,.85);}
.film h2{font-size:clamp(26px,4.4vw,58px); line-height:1.04; color:var(--wine);
  text-shadow:0 2px 24px rgba(255,255,255,.95), 0 0 50px rgba(255,255,255,.8);}
.film__sub{font-size:clamp(14px,1.5vw,18px); color:var(--ink); font-weight:500;
  max-width:min(520px,86vw); text-shadow:0 1px 16px rgba(255,255,255,.98);}
.film__sub--sm{font-size:13px; color:var(--ink-2);}
.film__cta{display:flex; gap:12px; flex-wrap:wrap; margin-top:6px;}
.beat--center .film__cta{justify-content:center;}

/* copy sits on the side of the frame the dish is not using */
.dishcard{background:rgba(255,255,255,.90); border:1px solid rgba(129,23,25,.26);
  backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px);
  border-radius:4px; padding:clamp(20px,2.6vw,32px); max-width:min(400px,44vw);
  display:flex; flex-direction:column; gap:10px;
  box-shadow:0 18px 60px rgba(20,25,40,.16);}
.dishcard--wide{max-width:min(430px,42vw);}
.dishcard__cat{font-family:var(--brandsans); font-size:10.5px; letter-spacing:.24em;
  text-transform:uppercase; color:var(--gold-h); font-weight:700;}
.dishcard h2{font-size:clamp(22px,2.7vw,33px); text-shadow:none; line-height:1.1;}
.dishcard p{font-size:14px; color:var(--ink-2); line-height:1.65;}
.dishcard__p{display:flex; align-items:baseline; gap:7px; margin-top:2px;}
.dishcard__p b{font-family:var(--display); font-weight:600; font-size:30px; color:var(--wine);}
.dishcard__p span{font-size:11px; letter-spacing:.18em; color:var(--faint);}
.dishcard__act{display:flex; flex-wrap:wrap; gap:9px; margin-top:4px;}
.dishcard__act .btn{align-self:flex-start;}

.film__branches{display:flex; gap:14px; flex-wrap:wrap; justify-content:center; margin:4px 0;}
.film__branches a{background:rgba(255,255,255,.9); border:1px solid rgba(129,23,25,.24);
  border-radius:4px; padding:15px 22px; display:flex; flex-direction:column; gap:2px;
  color:var(--ink); backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px); min-width:172px;}
.film__branches a:hover{border-color:var(--gold); color:var(--ink);}
.film__branches b{font-family:var(--display); font-size:19px; color:var(--wine);}
.film__branches span{font-size:12px; color:var(--muted);}
.film__branches i{font-style:normal; font-size:13px; color:var(--ink); font-variant-numeric:tabular-nums;}

.film__cue{position:absolute; left:50%; bottom:26px; transform:translateX(-50%);
  display:flex; flex-direction:column; align-items:center; gap:8px; color:var(--wine);
  font-size:10px; letter-spacing:.26em; text-transform:uppercase; font-weight:600;
  text-shadow:0 1px 12px rgba(255,255,255,.95);}
.film__cue i{width:2px; height:42px; background:linear-gradient(var(--wine),transparent);
  animation:cue 2.2s ease-in-out infinite; transform-origin:top;}
@keyframes cue{0%,100%{transform:scaleY(.35);opacity:.4}50%{transform:scaleY(1);opacity:1}}
.film__prog{position:absolute; left:0; right:0; bottom:0; height:2px; background:rgba(20,25,40,.10);}
.film__prog span{display:block; height:100%; background:var(--gold); transform-origin:left;
  transform:scaleX(0);}
.film__rail{position:absolute; right:clamp(12px,2vw,26px); top:50%; transform:translateY(-50%);
  display:flex; flex-direction:column; gap:11px;}
.film__rail a{width:8px; height:8px; border-radius:50%; background:rgba(20,25,40,.22);
  border:1px solid rgba(255,255,255,.7); transition:.2s;}
.film__rail a:hover{background:var(--wine); transform:scale(1.35);}

@media(max-width:820px){
  .film{height:1400svh;}
  .beat{padding:80px 20px 100px;}
  .beat--left,.beat--right{align-items:stretch; justify-content:flex-end; padding-bottom:96px;}
  .dishcard,.dishcard--wide{max-width:100%;}
  .film__rail{display:none;}
}
@media (prefers-reduced-motion: reduce){ .film__cue i{animation:none;} }
</style>'''

JS = '<script src="assets/js/landing.js" defer></script>'

B.page('index.html','Mosaic Lebanese Restaurant — Abu Dhabi',
  'Award-winning Lebanese dining in Abu Dhabi. Mezze, charcoal grills and saj bread at Al Muroor and Al Najda. 250 dishes, open seven days.',
  body, 'index.html', CSS, JS, cls='page-film')
print('index.html — scroll film')
