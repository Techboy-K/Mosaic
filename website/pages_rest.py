# -*- coding: utf-8 -*-
import importlib.util as _u, json, os
_s=_u.spec_from_file_location('b','build-site.py'); B=_u.module_from_spec(_s); _s.loader.exec_module(B)
icon,I,MENU,BRANCHES = B.icon,B.I,B.MENU,B.BRANCHES

def banner(eyebrow,title,sub,img):
    return f"""<section class="banner">
  <img class="banner__bg" src="{img}" alt="" loading="eager">
  <div class="banner__scrim"></div>
  <div class="wrap"><span class="eyebrow">{eyebrow}</span><h1>{title}</h1>
    <p class="lede" style="max-width:640px;">{sub}</p></div>
</section>"""

# ══════════════════════════════════════════════════════════ MENU
MENU_CSS = """<style>
/* ---------- toolbar ---------- */
.mtools{position:sticky;top:0;z-index:40;background:rgba(255,255,255,.96);
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid var(--hair);}
.mtools__row{display:flex;align-items:center;gap:14px;padding:13px 0;flex-wrap:wrap;}
.msearch{display:flex;align-items:center;gap:10px;border:1px solid var(--hair);background:var(--paper);border-radius:var(--r);
  padding:0 14px;min-height:46px;flex:1;min-width:210px;max-width:360px;color:var(--faint);
  transition:border-color .2s;}
.msearch:focus-within{border-color:var(--gold);}
.msearch input{background:none;border:0;color:var(--ink);font:inherit;font-size:14px;width:100%;outline:none;}
.msearch input::placeholder{color:var(--faint);}
.msearch button{background:none;border:0;color:var(--faint);cursor:pointer;padding:4px;line-height:0;}
.msearch button:hover{color:var(--ink);}
.mcount{font-size:12.5px;color:var(--faint);white-space:nowrap;}
.mchips{display:none;gap:8px;overflow-x:auto;padding:0 0 12px;scrollbar-width:none;
  -webkit-mask-image:linear-gradient(90deg,#000 0,#000 93%,transparent 100%);}
.mchips::-webkit-scrollbar{display:none;}
.chip{display:inline-flex;align-items:center;gap:7px;white-space:nowrap;min-height:38px;padding:0 15px;
  border:1px solid var(--hair);border-radius:var(--r);background:var(--paper);color:var(--ink-2);
  font:inherit;font-size:12.5px;cursor:pointer;transition:.2s;}
.chip:hover{border-color:var(--gold);color:var(--ink);}
.chip.is-on{background:var(--wine);color:#FFF3E6;border-color:var(--wine);}
.chip .num{opacity:.5;font-size:11px;}
.chip.is-on .num{opacity:.6;}
@media(max-width:1023px){.mchips{display:flex;}}

/* ---------- layout ---------- */
.mlayout{display:grid;grid-template-columns:236px 1fr;gap:clamp(28px,4vw,56px);align-items:start;}
@media(max-width:1023px){.mlayout{grid-template-columns:1fr;}}
.rail{position:sticky;top:132px;display:flex;flex-direction:column;gap:1px;max-height:calc(100svh - 170px);
  overflow-y:auto;scrollbar-width:thin;}
@media(max-width:1023px){.rail{display:none;}}
.rail__item{display:flex;align-items:center;justify-content:space-between;gap:12px;width:100%;
  background:none;border:0;border-left:2px solid transparent;padding:10px 14px;cursor:pointer;
  font:inherit;font-size:14px;color:var(--muted);text-align:left;transition:.18s;}
.rail__item:hover{color:var(--wine);background:var(--paper);}
.rail__item.is-on{color:var(--wine);border-left-color:var(--gold);background:var(--paper);font-weight:500;}
.rail__item .num{font-size:11.5px;color:var(--faint);}

.mhead{display:flex;align-items:baseline;justify-content:space-between;gap:18px;flex-wrap:wrap;
  padding-bottom:18px;margin-bottom:clamp(20px,3vw,30px);border-bottom:1px solid var(--hair);}
.mhead h2{font-size:clamp(24px,3.2vw,38px);}
.mhead p{font-size:13px;color:var(--faint);letter-spacing:.04em;}

/* ---------- dish cards ---------- */
.dishgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(238px,1fr));
  gap:clamp(14px,1.6vw,22px);}
.dish{display:flex;flex-direction:column;background:var(--paper);border:1px solid var(--hair-2);
  border-radius:6px;overflow:hidden;box-shadow:0 2px 12px rgba(20,25,40,.05);
  transition:box-shadow .28s,transform .28s;scroll-margin-top:170px;}
.dish:hover{box-shadow:0 14px 34px rgba(20,25,40,.11);transform:translateY(-3px);}
.dish.is-target{border-color:var(--gold);}
.dish__media{position:relative;overflow:hidden;background:var(--sand);}
.dish__img{width:100%;height:172px;object-fit:cover;display:block;transition:transform .5s;}
.dish:hover .dish__img{transform:scale(1.045);}
.dish__img--none{display:block;height:172px;background:
  repeating-linear-gradient(135deg,var(--sand) 0 10px,var(--sand-2) 10px 20px);}
.dish__tag{position:absolute;top:10px;left:10px;background:rgba(255,255,255,.93);color:var(--wine);border-radius:var(--r);
  font-size:9.5px;letter-spacing:.15em;text-transform:uppercase;padding:5px 9px;}
.dish__body{padding:16px 18px 18px;display:flex;flex-direction:column;gap:8px;flex:1;}
.dish__row{display:flex;align-items:baseline;justify-content:space-between;gap:12px;}
.dish__row h3{font-size:17.5px;line-height:1.25;}
.dish__price{font-family:var(--display);font-size:19px;color:var(--wine);white-space:nowrap;}
.dish__price i{font-style:normal;font-size:9.5px;letter-spacing:.13em;color:var(--faint);margin-left:4px;}
.dish__body p{font-size:13px;line-height:1.55;color:var(--muted);flex:1;}
.dish__add{margin-top:4px;align-self:flex-start;background:none;border:1px solid var(--hair);
  border-radius:var(--r);color:var(--muted);font:inherit;font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  font-weight:600;padding:9px 14px;cursor:pointer;transition:.2s;}
.dish__add:hover{border-color:var(--gold);color:var(--gold-h);background:var(--gold-p);}
#menu-empty{padding:60px 0;text-align:center;}
</style>"""

menu_body = banner("The menu","Two hundred and fifty dishes.",
  "One menu, served the same way at both addresses, from eight in the morning until half past eleven at night.",
  "assets/img/rooms/platter.webp") + """
<div class="mtools">
  <div class="wrap">
    <div class="mtools__row">
      <label class="msearch">""" + icon(I['search'],17) + """
        <input id="menu-search" type="search" placeholder="Search 250 dishes…" aria-label="Search the menu">
        <button id="menu-clear" type="button" aria-label="Clear search" hidden>""" + icon(I['x'],15) + """</button>
      </label>
      <span class="mcount"><span class="num" id="menu-count">250</span> shown</span>
      <span style="flex:1"></span>
      <a class="btn btn--primary btn--sm" href="contact.html#book">Book a Table</a>
    </div>
    <div class="mchips" id="menu-chips"></div>
  </div>
</div>

<div class="band band--tight" id="menu-main"><div class="wrap">
  <div class="mlayout">
    <aside class="rail" id="menu-rail" aria-label="Menu categories"></aside>
    <div>
      <div class="mhead">
        <h2 id="menu-title">The whole menu</h2>
        <p id="menu-sub">All 250 dishes, every category</p>
      </div>
      <div class="dishgrid" id="menu-root"></div>
      <p id="menu-empty" class="lede" hidden>Nothing matched that search. Try a dish name or an ingredient.</p>
      <div id="menu-more-wrap" style="display:flex;justify-content:center;margin-top:clamp(26px,4vw,44px);" hidden>
        <button class="btn btn--ghost" type="button" id="menu-more">Show more dishes</button>
      </div>
    </div>
  </div>
</div></div>
"""
B.page('menu.html','Menu — Mosaic Lebanese Restaurant',
  'The full Mosaic menu: 250 Lebanese dishes across 19 categories, with prices in AED. Mezze, charcoal grills, shawarma, manakish and more.',
  menu_body,'menu.html',MENU_CSS,'<script src="assets/js/menu.js" defer></script>')

# ══════════════════════════════════════════════════════════ STORY
BRANDS=[("Mosaic Catering","Events, from boardroom to ballroom"),
        ("La Tartine P&acirc;tisserie","Fine desserts and viennoiserie"),
        ("Nazira Kitchen","Home-style cooking, delivered"),
        ("Salatoush","Let&rsquo;tuce dress it up"),
        ("Space Bun","Modern buns and burgers"),
        ("Shamroukh","Grill house")]
story_body = banner("Our story","Many small pieces,<br>one picture.",
  "Named after the word Mosaic &mdash; because that is what a Lebanese table is.",
  "assets/img/rooms/najda.webp") + f"""
<section class="band"><div class="wrap" style="max-width:820px;">
  <div style="display:flex;flex-direction:column;gap:26px;">
    <p class="rv" style="font-family:var(--display);font-size:clamp(22px,3vw,30px);line-height:1.45;color:var(--ink);">
      Mezze arrives first and never really stops. The grill follows. The bread keeps coming, and somewhere
      around the third plate of hommos nobody is talking about the food any more &mdash; which is the point.</p>
    <p class="lede rv">Our kitchen offers a kaleidoscope of mouth-watering Lebanese dishes that satisfy all
      taste buds. Everything is made in house, from the tabbouleh chopped to order to the saj bread that
      comes off the griddle while you are still reading the menu.</p>
    <p class="lede rv">Not fine dining. Not a hotel dining room with a view to lean on. The everyday,
      come-as-you-are, bring-the-family version &mdash; which, as it turns out, is the harder thing to get
      right, and the thing Abu Dhabi keeps voting for.</p>
  </div>
</div></section>
<section class="band band--tight"><div class="wrap">
  <div class="grid grid--2">
    <img class="rv" src="assets/img/rooms/muroor.webp" alt="The Al Muroor dining room" loading="lazy" style="width:100%;">
    <img class="rv" src="assets/img/rooms/table.webp" alt="A Mosaic table laid with mezze" loading="lazy" style="width:100%;object-fit:cover;">
  </div>
</div></section>
<section class="band band--sand"><div class="wrap">
  <div class="section-head rv"><span class="eyebrow">The people</span>
    <h2>The people behind the plates.</h2></div>
  <img class="rv" src="assets/img/rooms/team.webp" alt="The Mosaic kitchen and floor team" loading="lazy" style="width:100%;">
  <div class="grid grid--3" style="margin-top:clamp(26px,4vw,44px);">
    {"".join(f'''<div class="rv" style="display:flex;flex-direction:column;gap:11px;padding-top:20px;border-top:1px solid var(--hair);">
      <span class="disp" style="font-size:20px;">{t}</span><p style="font-size:14.5px;color:var(--muted);">{d}</p></div>'''
      for t,d in [("Chef Hassane El Baroudi","Named Chef of the Year at the What&rsquo;s On Awards 2025, and running both kitchens since."),
                  ("Made here, daily","Bread on the saj, kibbeh rolled by hand, tabbouleh chopped to order &mdash; nothing arrives pre-made."),
                  ("ISO 22000 &amp; ISO 9001","Certified food safety and quality management, independently audited.")])}
  </div>
</div></section>
<section class="band"><div class="wrap">
  <div class="section-head section-head--center rv"><span class="eyebrow">Mosaic Group</span>
    <h2>Six kitchens, one family.</h2>
    <p class="lede" style="max-width:560px;">From fine pastries and Lebanese cuisine to healthy kitchens
       and modern dining concepts.</p></div>
  <div class="grid grid--3">
    {"".join(f'''<a class="card rv" href="#"><div class="card__body">
      <span class="disp" style="font-size:22px;">{n}</span>
      <p style="font-size:14px;color:var(--muted);">{d}</p>
      <span style="display:flex;align-items:center;gap:8px;margin-top:8px;font-size:11.5px;
        letter-spacing:.15em;text-transform:uppercase;color:var(--gold);">Visit {icon(I['arrow'],14)}</span>
    </div></a>''' for n,d in BRANDS)}
  </div>
</div></section>
"""
B.page('story.html','Our Story — Mosaic Lebanese Restaurant',
  'Named after the word Mosaic. The story of an Abu Dhabi Lebanese kitchen, its chef, and the six brands of Mosaic Group.',
  story_body,'story.html')

# ══════════════════════════════════════════════════════════ CATERING
STEPS=[("Tell us the shape of the day","Guest count, timing, venue, and anything the room needs to avoid."),
       ("We build and cost a menu","Sent within two working days, priced per head, no surprises."),
       ("Taste it","For weddings and large events, before anything is confirmed."),
       ("We arrive, set, serve and clear","Our team, our equipment, your evening.")]
FORMATS=[("Boardroom lunch","10&ndash;30 guests","Mezze platters, hot mains and dessert, delivered and set."),
         ("Reception","50&ndash;300 guests","Live saj and shawarma stations, canap&eacute; towers, full service team."),
         ("Weddings","On request","A menu built with you, tasted before you sign anything."),
         ("Iftar &amp; Suhoor","Ramadan","Hot and cold mezzeh, fresh bread and live cooking stations.")]
def field(label,ph,wide=False,sel=False):
    tag = ('<select><option>'+ph+'</option></select>') if sel else f'<input type="text" placeholder="{ph}">'
    return f'<label class="fld{" fld--wide" if wide else ""}"><span>{label}</span>{tag}</label>'

FORM_CSS = """<style>

.branch-cards{display:flex;flex-direction:column;gap:clamp(18px,2.4vw,28px);}
  .branch-card{display:none;}
  .branch-card.is-active{display:flex;}
.timegrid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;}.timegrid{grid-template-columns:repeat(3,minmax(0,1fr));}
.slot{min-height:44px;display:flex;align-items:center;justify-content:center;border:1px solid var(--hair);
  border-radius:var(--r);background:var(--paper);color:var(--ink-2);font:inherit;font-size:14px;cursor:pointer;transition:.2s;}
.slot:hover{border-color:var(--gold);color:var(--ink);}
.slot[aria-pressed="true"]{background:var(--wine);color:#FFF3E6;border-color:var(--wine);}
.branchpick{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.branchpick button{display:flex;flex-direction:column;gap:3px;align-items:flex-start;padding:15px 17px;
  border:1px solid var(--hair);border-radius:5px;background:var(--paper);color:var(--ink);cursor:pointer;font:inherit;text-align:left;}
.branchpick button[aria-pressed="true"]{border-color:var(--gold);background:var(--gold-p);}
.branchpick small{color:var(--faint);font-size:12px;}
.faq{display:flex;flex-direction:column;}
.faq details{border-bottom:1px solid var(--hair);padding:20px 0;}
.faq summary{font-family:var(--display);font-size:clamp(18px,2.2vw,22px);cursor:pointer;list-style:none;
  display:flex;justify-content:space-between;gap:18px;align-items:center;}
.faq summary::-webkit-details-marker{display:none;}
.faq summary::after{content:"+";color:var(--gold);font-family:var(--sans);font-size:20px;}
.faq details[open] summary::after{content:"–";}
.faq p{margin-top:11px;color:var(--muted);font-size:15px;max-width:660px;}
@media(max-width:560px){.formgrid{grid-template-columns:1fr;}}@media(min-width:901px){
  .branch-card{display:none;}
  .branch-card.is-active{display:flex;}
}@media(max-width:620px){.timegrid{grid-template-columns:repeat(3,minmax(0,1fr));}}</style>"""

cater_body = banner("Mosaic Catering","Your table, wherever<br>you are putting it.",
  "Corporate events, weddings, friends at home, or an unforgettable night with the people you like most.",
  "assets/img/catering/station.webp") + f"""
<section class="band"><div class="wrap">
  <div class="grid grid--2" style="align-items:start;gap:clamp(30px,5vw,80px);">
    <div class="rv" style="display:flex;flex-direction:column;gap:22px;">
      <span class="eyebrow">How it works</span>
      <h2 style="font-size:clamp(26px,4vw,46px);">First-class Lebanese,<br>on your terms.</h2>
      <p class="lede">Our range caters for all cravings &mdash; from those looking for home-made food to
        international connoisseurs. Personalised service, with emphasis on taste, style and flexibility.</p>
      <div style="display:flex;flex-direction:column;">
        {"".join(f'''<div style="display:flex;gap:20px;padding:20px 0;border-bottom:1px solid var(--hair-2);">
          <span class="num" style="font-family:var(--display);font-size:14px;color:var(--gold);padding-top:4px;">0{i+1}</span>
          <div style="display:flex;flex-direction:column;gap:5px;">
            <span class="disp" style="font-size:19px;">{t}</span>
            <span style="font-size:14px;color:var(--muted);">{d}</span></div></div>'''
          for i,(t,d) in enumerate(STEPS))}
      </div>
    </div>
    <form class="rv" style="background:var(--paper);border:1px solid var(--hair-2);border-radius:6px;box-shadow:0 3px 18px rgba(20,25,40,.06);padding:clamp(24px,3.4vw,42px);display:flex;flex-direction:column;gap:22px;" onsubmit="return false;">
      <div style="display:flex;flex-direction:column;gap:7px;">
        <h2 style="font-size:clamp(24px,3vw,32px);">Plan an event</h2>
        <p style="font-size:14px;color:var(--muted);">We reply within one working day.</p></div>
      <div class="formgrid">
        {field("Full name","Your name")}{field("Phone","+971")}
        {field("Email","you@company.com",wide=True)}
        {field("Event date","Select a date")}{field("Guests","50–100",sel=True)}
        {field("Event type","Corporate reception",sel=True)}{field("Venue","Abu Dhabi")}
      </div>
      <label class="fld"><span>Anything we should know</span>
        <textarea placeholder="Allergies, dietary requirements, service style…"></textarea></label>
      <button class="btn btn--primary" type="submit" style="width:100%;">Send enquiry</button>
      <div style="display:flex;gap:18px;flex-wrap:wrap;padding-top:16px;border-top:1px solid var(--hair-2);">
        <a href="tel:0522329182" class="num" style="display:flex;align-items:center;gap:9px;font-size:14px;color:var(--ink);">
          <span style="color:var(--gold)">{icon(I['phone'],17)}</span>052 2329 182</a>
        <a href="mailto:catering@mosaic-ae.com" style="display:flex;align-items:center;gap:9px;font-size:14px;color:var(--ink);">
          <span style="color:var(--gold)">{icon(I['mail'],17)}</span>catering@mosaic-ae.com</a>
      </div>
    </form>
  </div>
</div></section>
<section class="band band--sand"><div class="wrap">
  <div class="section-head rv"><h2>Formats we do most often.</h2>
    <p class="lede" style="max-width:520px;">Every one of these is a starting point, not a package.
       Menus are written for the event.</p></div>
  <div class="grid grid--4">
    {"".join(f'''<div class="card rv"><div class="card__body">
      <span class="eyebrow">{s}</span><span class="disp" style="font-size:22px;">{t}</span>
      <p style="font-size:14px;color:var(--muted);">{d}</p></div></div>''' for t,s,d in FORMATS)}
  </div>
</div></section>
<section class="band band--tight"><div class="wrap"><div class="grid grid--3">
  <img class="rv" src="assets/img/catering/canapes.webp" alt="Canapé tower" loading="lazy" style="width:100%;">
  <img class="rv" src="assets/img/catering/station.webp" alt="Buffet station" loading="lazy" style="width:100%;">
  <img class="rv" src="assets/img/catering/spread.webp" alt="Catering spread" loading="lazy" style="width:100%;">
</div></div></section>
"""
B.page('catering.html','Catering — Mosaic Lebanese Restaurant',
  'Mosaic Catering: corporate events, weddings, receptions and Ramadan iftar in Abu Dhabi. Personalised Lebanese menus, priced per head.',
  cater_body,'catering.html',FORM_CSS)

# ══════════════════════════════════════════════════════════ AWARDS
CERTS = [
 ("2516","Favourite Casual Middle Eastern Restaurant","What&rsquo;s On Awards","2025","Al Muroor"),
 ("2503","Chef of the Year &mdash; Chef Hassane El Baroudi","What&rsquo;s On Awards","2025",""),
 ("2530","Best of the Best &mdash; Top 1% of World&rsquo;s Best Restaurants","Tripadvisor Travellers&rsquo; Choice","2025",""),
 ("2505","Winner","FACT Dining Awards Abu Dhabi","2025","Muroor"),
 ("2557","Highly Commended &mdash; Favourite Middle Eastern Restaurant","What&rsquo;s On Awards","2024","Muroor"),
 ("2511","Travelers&rsquo; Choice","Tripadvisor","2023",""),
 ("2564","Winner &mdash; Business Lunch, UAE","BBC Good Food Middle East Magazine Awards","2022",""),
 ("2524","Winner &mdash; Favourite Middle Eastern Restaurant","What&rsquo;s On Awards","2022","Muroor"),
 ("2560","Travelers&rsquo; Choice","Tripadvisor","2022",""),
 ("2543","Travelers&rsquo; Choice","Tripadvisor","2020",""),
 ("2552","Winner &mdash; Middle Eastern Restaurant, Abu Dhabi","BBC Good Food Middle East Magazine Awards","2019",""),
 ("2536","Finalist &mdash; Favourite Business Lunch","What&rsquo;s On Awards","2019",""),
 ("2525","Certificate of Excellence","Tripadvisor","2019",""),
 ("2539","Winner &mdash; Favourite Middle Eastern Restaurant","What&rsquo;s On Awards","2018",""),
 ("2521","Best Middle Eastern Casual Dine","Zomato Users&rsquo; Choice Awards","2018",""),
 ("2528","Certificate of Excellence","Tripadvisor","2018",""),
 ("2507","ISO 9001:2015 &mdash; Quality Management","IQA Certification","",""),
 ("2514","ISO 22000:2018 &mdash; Food Safety Management","APEX Certification","",""),
 ("2533","95.83% Excellent Hygiene","Zomato Hygiene Audit, NSD Gulf Ltd","",""),
]
AW_CSS = """<style>
.certgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:clamp(16px,2.4vw,30px);}
.cert{background:none;border:0;padding:0;cursor:pointer;text-align:left;display:flex;flex-direction:column;gap:11px;font:inherit;}
.cert img{width:100%;border-radius:3px;box-shadow:0 14px 34px rgba(20,25,40,.16);transition:transform .35s,box-shadow .35s;}
.cert:hover img,.cert:focus-visible img{transform:translateY(-8px);box-shadow:0 24px 50px rgba(20,25,40,.24);}
.cert .y{font-family:var(--display);font-size:15px;color:var(--wine);}
.cert .t{font-size:12.5px;line-height:1.42;color:var(--ink);}
.cert .b{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);}
#lightbox{position:fixed;inset:0;z-index:95;background:rgba(16,19,32,.96);display:none;
  align-items:center;justify-content:center;flex-direction:column;gap:20px;padding:clamp(22px,5vw,58px);
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);}
#lightbox.is-open{display:flex;}
#lightbox img{max-height:66svh;width:auto;box-shadow:0 36px 80px rgba(0,0,0,.7);}
#lb-close{position:absolute;top:20px;right:24px;background:none;border:1px solid var(--on-dark-hair);
  border-radius:50%;color:var(--on-dark);width:46px;height:46px;cursor:pointer;font-size:20px;}
#lb-close:hover{border-color:var(--on-dark);}
</style>"""
cert_html = "".join(
  f'''<button class="cert" type="button" data-img="assets/img/awards/cert-{k}.webp"
      data-title="{t}" data-body="{b}{(' · '+y) if y else ''}{(' · '+n) if n else ''}">
    <img src="assets/img/awards/cert-{k}.webp" alt="{t}" loading="lazy">
    <span class="y">{y or 'Certified'}</span><span class="t">{t}</span>
    <span class="b">{b}{(' · '+n) if n else ''}</span></button>''' for k,t,b,y,n in CERTS)

aw_body = banner("Recognition","Decided by the people<br>who eat here.",
  "Public-vote awards are a very direct piece of feedback. Every vote was somebody who ate with us, remembered it, and took the time to say so.",
  "assets/img/awards/stage.webp") + f"""
<section class="band"><div class="wrap">
  <div class="grid grid--2" style="align-items:center;gap:clamp(28px,5vw,72px);">
    <div class="rv" style="display:flex;flex-direction:column;gap:20px;">
      <span class="eyebrow">August 2026</span>
      <h2 style="font-size:clamp(26px,4vw,46px);">Two branches. Two titles.<br>One vote that came from you.</h2>
      <p class="lede">Mosaic closed the What&rsquo;s On Abu Dhabi Awards 2026 with two wins in a single
         evening &mdash; a result that puts both of our addresses on the capital&rsquo;s official list of favourites.</p>
      <p style="color:var(--muted);font-size:15px;">Published by Motivate Media Group, the awards run across
         37 categories, every one decided by public vote. Al Najda was named Favourite Business Lunch;
         Al Muroor, Favourite Casual Middle Eastern Restaurant.</p>
    </div>
    <div class="grid grid--2 rv" style="align-items:start;">
      <img src="assets/img/awards/trophies.webp" alt="The 2026 trophies" loading="lazy" style="width:100%;">
      <img src="assets/img/awards/ceremony.webp" alt="Mosaic receiving the Favourite Business Lunch award" loading="lazy" style="width:100%;margin-top:30px;">
    </div>
  </div>
</div></section>
<section class="band band--sand"><div class="wrap">
  <div class="section-head rv"><span class="eyebrow">The wall</span>
    <h2>Every certificate, since 2018.</h2>
    <p class="lede" style="max-width:540px;">Nineteen of them. Tap any one to read it.</p></div>
  <div class="certgrid">{cert_html}</div>
</div></section>
<div id="lightbox" role="dialog" aria-modal="true" aria-label="Award certificate">
  <button id="lb-close" type="button" aria-label="Close">&times;</button>
  <img id="lb-img" src="" alt="">
  <div style="text-align:center;display:flex;flex-direction:column;gap:6px;max-width:620px;">
    <span class="disp" id="lb-title" style="font-size:clamp(17px,2.2vw,24px);color:var(--on-dark);"></span>
    <span id="lb-body" style="font-size:13px;color:var(--on-dark-muted);"></span></div>
</div>
"""
AW_JS = """<script>
(function(){var lb=document.getElementById('lightbox'),im=document.getElementById('lb-img'),
 ti=document.getElementById('lb-title'),bo=document.getElementById('lb-body'),
 cl=document.getElementById('lb-close'),last=null;
function open(b){last=document.activeElement;im.src=b.dataset.img;im.alt=b.dataset.title;
 ti.innerHTML=b.dataset.title;bo.innerHTML=b.dataset.body;lb.classList.add('is-open');cl.focus();}
function close(){lb.classList.remove('is-open');last&&last.focus();}
document.querySelectorAll('.cert').forEach(function(b){b.addEventListener('click',function(){open(b);});});
cl.addEventListener('click',close);
lb.addEventListener('click',function(e){if(e.target===lb)close();});
addEventListener('keydown',function(e){if(e.key==='Escape'&&lb.classList.contains('is-open'))close();});
})();
</script>"""
B.page('awards.html','Awards — Mosaic Lebanese Restaurant',
  'Nineteen awards since 2018, including What’s On Abu Dhabi 2026 Favourite Business Lunch and Favourite Casual Middle Eastern Restaurant.',
  aw_body,'awards.html',AW_CSS,AW_JS)

# ══════════════════════════════════════════════════════════ CONTACT
TIMES=["12:00","12:30","13:00","13:30","19:00","19:30","20:00","20:30","21:00","21:30"]
slots="".join(f'<button class="slot" type="button" aria-pressed="{"true" if t=="19:30" else "false"}">{t}</button>' for t in TIMES)
FAQ=[("Do you take walk-ins?","Always &mdash; booking simply guarantees the table, particularly for business lunch and weekend evenings."),
     ("Is there a dress code?","No. Come as you are."),
     ("Can you handle allergies?","Tell us when you book or in your order notes and the kitchen will work around it."),
     ("Do you cater for large groups?","Yes &mdash; from ten around a table to three hundred at a reception. Mosaic Catering handles both."),
     ("Is there parking?","[TO CONFIRM &mdash; not published on the current site]"),
     ("Are the branches step-free?","[TO CONFIRM &mdash; not published on the current site]")]
bcards="".join(f"""<article class="card rv branch-card" data-branch-card="{b['name']}">
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
    <p style="font-size:12.5px;color:var(--faint);padding-left:28px;">Direct line to the {b['name']} host desk</p>
  </div></article>""" for b in BRANCHES)

contact_body = banner("Contact &amp; booking","Come and sit down.",
  "Two rooms in Abu Dhabi, open seven days. Book below, or call the branch directly.",
  "assets/img/rooms/muroor.webp") + f"""
<section class="band" id="book"><div class="wrap">
  <div class="grid grid--2" style="align-items:start;gap:clamp(28px,5vw,72px);">
    <form class="rv" style="background:var(--paper);border:1px solid var(--hair-2);border-radius:6px;box-shadow:0 3px 18px rgba(20,25,40,.06);padding:clamp(24px,3.4vw,44px);display:flex;flex-direction:column;gap:22px;" onsubmit="return false;">
      <div style="display:flex;flex-direction:column;gap:7px;">
        <span class="eyebrow">Reserve</span>
        <h2 style="font-size:clamp(24px,3.2vw,36px);">Book a table</h2>
        <p style="font-size:14px;color:var(--muted);">Confirmation by SMS. No deposit for parties under ten.</p></div>
      <div style="display:flex;flex-direction:column;gap:8px;">
        <span style="font-size:10.5px;letter-spacing:.19em;text-transform:uppercase;color:var(--faint);font-weight:600;">Which branch</span>
        <div class="branchpick">
          <button type="button" data-branch="Al Muroor" aria-pressed="true">Al Muroor<small>Guardian Towers</small></button>
          <button type="button" data-branch="Al Najda" aria-pressed="false">Al Najda<small>Vision Towers</small></button>
        </div>
      </div>
      <div class="formgrid">
        <label class="fld"><span>Date</span><input id="bk-date" type="date"></label>
        <label class="fld"><span>Guests</span><select id="bk-guests"><option>1 person</option><option>2 people</option><option>3 people</option><option>4 people</option><option>5 people</option><option>6 people</option><option>7 people</option><option>8 people</option><option>9 people</option><option>10 people</option><option>11 people</option><option>12 people</option><option>13+ — we&rsquo;ll call you</option></select></label>
      </div>
      <div style="display:flex;flex-direction:column;gap:8px;">
        <div style="display:flex;align-items:baseline;justify-content:space-between;gap:12px;">
          <span style="font-size:10.5px;letter-spacing:.19em;text-transform:uppercase;color:var(--faint);font-weight:600;">Time</span>
          <span id="bk-hours" style="font-size:11.5px;color:var(--faint);"></span>
        </div>
        <div id="bk-wheel"></div>
      </div>
      <hr class="hair">
      <div class="formgrid"><label class="fld"><span>Full name</span><input id="bk-name" type="text" autocomplete="name" placeholder="Your name"></label><label class="fld"><span>Mobile</span><input id="bk-tel" type="tel" inputmode="tel" autocomplete="tel" placeholder="+971"></label>
        <label class="fld fld--wide"><span>Type of booking</span>
          <select id="bk-type"><option>Business</option><option>Family</option><option>Friends</option></select></label></div>
      <label class="fld"><span>Allergies or requests</span>
        <textarea id="bk-notes" placeholder="High chair, quiet corner, nut allergy…"></textarea></label>
      <hr class="hair">
      <div id="bk-food" class="preorder">
        <div class="preorder__head">
          <span class="eyebrow">Your food</span>
          <p>Order now and the kitchen starts it so it lands as you sit down &mdash;
             or leave it and order at the table.</p>
        </div>
        <div class="preorder__opts">
          <button type="button" data-pre="later" aria-pressed="true">
            <strong>Order at the table</strong><span>Decide when you get here</span></button>
          <button type="button" data-pre="now" aria-pressed="false">
            <strong>Pre-order now</strong><span>Ready when you arrive</span></button>
        </div>
        <p class="preorder__cart" id="bk-cartline" hidden></p>
      </div>
      <button class="btn btn--primary" type="submit" style="width:100%;">Confirm reservation</button>
      <p style="font-size:13px;color:var(--muted);text-align:center;">Prefer to speak to someone?
         Call the branch directly &mdash; numbers on the right.</p>
    </form>
    <div class="branch-cards">{bcards}</div>
  </div>
</div></section>
<section class="band band--sand"><div class="wrap">
  <div class="grid grid--2" style="gap:clamp(28px,5vw,72px);align-items:start;">
    <div class="rv" style="display:flex;flex-direction:column;gap:16px;">
      <span class="eyebrow">Good to know</span>
      <h2 style="font-size:clamp(24px,3.6vw,42px);">Questions we get asked.</h2>
      <div style="display:flex;flex-direction:column;gap:10px;margin-top:8px;">
        <a href="mailto:info@mosaic-ae.com" style="display:flex;align-items:center;gap:10px;font-size:15px;color:var(--ink);">
          <span style="color:var(--gold)">{icon(I['mail'],17)}</span>info@mosaic-ae.com</a>
        <a href="mailto:catering@mosaic-ae.com" style="display:flex;align-items:center;gap:10px;font-size:15px;color:var(--ink);">
          <span style="color:var(--gold)">{icon(I['mail'],17)}</span>catering@mosaic-ae.com</a>
      </div>
    </div>
    <div class="faq rv">
      {"".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in FAQ)}
    </div>
  </div>
</div></section>
"""
CONTACT_JS = """<script>
(function(){
 document.querySelectorAll('.timegrid').forEach(function(g){
   g.addEventListener('click',function(e){var b=e.target.closest('.slot');if(!b)return;
     g.querySelectorAll('.slot').forEach(function(s){s.setAttribute('aria-pressed','false');});
     b.setAttribute('aria-pressed','true');});});
 document.querySelectorAll('.branchpick').forEach(function(g){
   g.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
     g.querySelectorAll('button').forEach(function(s){s.setAttribute('aria-pressed','false');});
     b.setAttribute('aria-pressed','true');});});
})();
</script>"""
CONTACT_JS = CONTACT_JS + '<script src="assets/js/public-config.js" defer></script>'\
  '<script src="assets/js/timewheel.js" defer></script>'\
  '<script src="assets/js/booking.js" defer></script>'
B.page('contact.html','Contact & Booking — Mosaic Lebanese Restaurant',
  'Book a table at Mosaic Al Muroor or Al Najda in Abu Dhabi. Addresses, direct phone numbers, opening hours and FAQs.',
  contact_body,'contact.html',FORM_CSS,CONTACT_JS)
print('menu / story / catering / awards / contact written')
