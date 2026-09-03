/* Order basket + checkout.
   Lines persist in localStorage; the drawer and checkout are built on demand.
   Delivery is gated on data/delivery-zones.json so nobody can enter an address
   we cannot reach. */
(function (w, d) {
  'use strict';
  var KEY = 'mosaic.cart.v1', listeners = [], ZONES = null;

  function read()  { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } }
  function write(c){ try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) {}
                     listeners.forEach(function (f) { f(c); }); }
  function money(n){ return Number(n).toFixed(0); }
  function esc(s)  { return String(s).replace(/[&<>"']/g, function (c) {
                       return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]; }); }

  var Cart = {
    lines: function () { var c = read(); return Object.keys(c).map(function (k) { return c[k]; }); },
    count: function () { return Cart.lines().reduce(function (n, l) { return n + l.qty; }, 0); },
    total: function () { return Cart.lines().reduce(function (n, l) { return n + l.qty * l.price; }, 0); },
    add: function (item, qty) {
      var c = read(), id = String(item.id);
      if (!c[id]) c[id] = { id: item.id, name: item.name, price: +item.price, qty: 0 };
      c[id].qty += (qty || 1); write(c); return c[id].qty;
    },
    setQty: function (id, q) { var c = read(); if (!c[id]) return;
                               if (q <= 0) delete c[id]; else c[id].qty = q; write(c); },
    clear: function () { write({}); },
    onChange: function (f) { listeners.push(f); f(read()); }
  };
  w.MosaicCart = Cart;

  /* ---------------------------------------------------------------- badge */
  function badge() {
    var n = Cart.count();
    d.querySelectorAll('[data-cart-count]').forEach(function (el) { el.textContent = n; el.hidden = n === 0; });
  }
  Cart.onChange(function () { badge(); if (drawer && drawer.classList.contains('is-open')) paint(); });
  if (w.MosaicBooking) w.MosaicBooking.onChange(function () {
    if (drawer && drawer.classList.contains('is-open')) paint();
  });
  addEventListener('storage', function (e) { if (e.key === KEY) { badge(); paint(); } });

  /* ---------------------------------------------------------------- toast */
  var toast, tt;
  Cart.toast = function (m) {
    if (!toast) { toast = d.createElement('div'); toast.className = 'cart-toast';
                  toast.setAttribute('role','status'); toast.setAttribute('aria-live','polite');
                  d.body.appendChild(toast); }
    toast.textContent = m; toast.classList.add('is-up');
    clearTimeout(tt); tt = setTimeout(function () { toast.classList.remove('is-up'); }, 2400);
  };

  /* ---------------------------------------------------------------- drawer */
  var drawer, body, foot, lastFocus, step = 'cart';

  function build() {
    drawer = d.createElement('div');
    drawer.className = 'drawer-cart';
    drawer.innerHTML =
      '<div class="drawer-cart__veil" data-close></div>' +
      '<aside class="drawer-cart__panel" role="dialog" aria-modal="true" aria-label="Your order">' +
        '<header class="drawer-cart__head">' +
          '<h2 id="dc-title">Your order</h2>' +
          '<button class="drawer-cart__x" type="button" data-close aria-label="Close">&times;</button>' +
        '</header>' +
        '<div class="drawer-cart__body" id="dc-body"></div>' +
        '<footer class="drawer-cart__foot" id="dc-foot"></footer>' +
      '</aside>';
    d.body.appendChild(drawer);
    body = drawer.querySelector('#dc-body');
    foot = drawer.querySelector('#dc-foot');
    drawer.addEventListener('click', function (e) {
      if (e.target.closest('[data-close]')) close();
    });
    addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-open')) close();
    });
  }

  function open(to) {
    if (!drawer) build();
    step = to || 'cart';
    lastFocus = d.activeElement;
    drawer.classList.add('is-open');
    d.body.style.overflow = 'hidden';
    paint();
    var f = drawer.querySelector('.drawer-cart__x'); f && f.focus();
  }
  function close() {
    if (!drawer) return;
    drawer.classList.remove('is-open');
    d.body.style.overflow = '';
    lastFocus && lastFocus.focus();
  }
  Cart.open = open; Cart.close = close;

  /* ---------------------------------------------------------------- views */
  function paint() {
    if (!drawer) return;
    drawer.querySelector('#dc-title').textContent = step === 'cart' ? 'Your order' : 'Checkout';
    (step === 'cart' ? cartView : checkoutView)();
  }

  function cartView() {
    var lines = Cart.lines();
    if (!lines.length) {
      body.innerHTML = '<div class="dc-empty"><p>Your order is empty.</p>' +
        '<a class="btn btn--primary" href="menu.html">Browse the menu</a></div>';
      foot.innerHTML = ''; return;
    }
    body.innerHTML = '<ul class="dc-list">' + lines.map(function (l) {
      return '<li class="dc-line"><div class="dc-line__t"><span class="dc-line__n">' + esc(l.name) + '</span>' +
        '<span class="dc-line__p num">AED ' + money(l.price * l.qty) + '</span></div>' +
        '<div class="dc-qty" role="group" aria-label="Quantity for ' + esc(l.name) + '">' +
          '<button type="button" data-q="-1" data-id="' + l.id + '" aria-label="One fewer">&minus;</button>' +
          '<span class="num">' + l.qty + '</span>' +
          '<button type="button" data-q="1" data-id="' + l.id + '" aria-label="One more">+</button>' +
          '<button class="dc-rm" type="button" data-rm="' + l.id + '">Remove</button>' +
        '</div></li>';
    }).join('') + '</ul>';

    foot.innerHTML =
      '<div class="dc-row"><span>Subtotal</span><strong class="num">AED ' + money(Cart.total()) + '</strong></div>' +
      '<p class="dc-note">Delivery is calculated at the next step.</p>' +
      '<button class="btn btn--primary" type="button" id="dc-go" style="width:100%">Checkout</button>' +
      '<button class="btn btn--ghost" type="button" data-close style="width:100%">Keep browsing</button>';

    body.onclick = function (e) {
      var q = e.target.closest('[data-q]'), rm = e.target.closest('[data-rm]');
      if (q) { var c = read(), id = q.dataset.id;
               if (c[id]) Cart.setQty(id, c[id].qty + (+q.dataset.q)); }
      if (rm) Cart.setQty(rm.dataset.rm, 0);
    };
    foot.querySelector('#dc-go').onclick = function () { step = 'checkout'; paint(); };
  }

  /* -------------------------------------------------------------- checkout */
  var form = { mode: 'delivery', area: '', zone: null };
  var MODES = [['delivery','Delivery'],['pickup','Pickup'],['dinein','Dine-in']];

  function zoneFor(area) {
    if (!ZONES) return null;
    for (var i = 0; i < ZONES.zones.length; i++)
      if (ZONES.zones[i].areas.indexOf(area) > -1) return ZONES.zones[i];
    return null;
  }

  function checkoutView() {
    if (!ZONES) {
      body.innerHTML = '<p class="dc-note">Loading delivery areas…</p>';
      fetch('data/delivery-zones.json').then(function (r) { return r.json(); })
        .then(function (z) { ZONES = z; paint(); })
        .catch(function () { ZONES = { zones: [], outside_message: '' }; paint(); });
      return;
    }
    var sub = Cart.total();
    var zone = form.zone;
    var fee  = (form.mode === 'delivery' && zone) ? zone.fee : 0;
    var belowMin = form.mode === 'delivery' && zone && sub < zone.min;

    var areaOpts = '<option value="">Select your area…</option>' +
      ZONES.zones.map(function (z) {
        return '<optgroup label="' + esc(z.name) + '">' +
          z.areas.map(function (a) {
            return '<option' + (form.area === a ? ' selected' : '') + '>' + esc(a) + '</option>';
          }).join('') + '</optgroup>';
      }).join('') +
      '<option value="__out">My area is not listed</option>';

    var B = w.MosaicBooking;
    var booked = B && B.complete();

    /* Dine-in only exists alongside a table booking. If the booking is gone,
       fall back to pickup rather than leaving an order nobody can fulfil. */
    if (form.mode === 'dinein' && !booked && form.hadBooking) {
      form.mode = 'pickup'; form.hadBooking = false;
      Cart.toast('Table booking removed — switched to pickup.');
    }
    if (booked) form.hadBooking = true;

    body.innerHTML =
      '<div class="dc-seg dc-seg--3" role="group" aria-label="How would you like it">' +
        MODES.map(function (m) {
          return '<button type="button" data-mode="' + m[0] + '" aria-pressed="' +
                 (form.mode === m[0]) + '">' + m[1] + '</button>';
        }).join('') +
      '</div>' +

      (form.mode === 'dinein' ?
        (booked
          ? '<div class="dc-booked"><div><strong>Table booked</strong>' +
              '<span>' + esc(B.summary()) + '</span></div>' +
              '<a href="contact.html#book" class="dc-chg">Change</a></div>' +
            '<p class="dc-note">We&rsquo;ll time the kitchen so your food arrives just after you sit down.</p>'
          : '<div class="dc-needbook">' +
              '<p><strong>Dine-in needs a table first.</strong> Book one and we&rsquo;ll have your ' +
              'order ready as you sit down.</p>' +
              '<a class="btn btn--primary" href="contact.html#book" style="width:100%">Book a table</a>' +
              '<button class="btn btn--ghost" type="button" data-mode="pickup" style="width:100%">' +
              'Just do pickup instead</button>' +
            '</div>')
        : '') +

      (form.mode === 'delivery' ?
        '<label class="fld"><span>Area</span><select id="dc-area">' + areaOpts + '</select></label>' +
        (form.area === '__out'
          ? '<p class="dc-warn">' + esc(ZONES.outside_message) + '</p>'
          : (zone ? '<p class="dc-ok">' + esc(zone.name) + ' &middot; ' + esc(zone.eta) +
                    ' &middot; delivery AED ' + zone.fee +
                    (zone.min ? ' &middot; minimum AED ' + zone.min : '') + '</p>' : '')) +
        (zone ?
          '<label class="fld"><span>Street / building</span><input id="dc-street" placeholder="Street name and building"></label>' +
          '<div class="formgrid">' +
            '<label class="fld"><span>Flat / villa no.</span><input id="dc-flat" placeholder="e.g. 1203"></label>' +
            '<label class="fld"><span>Floor</span><input id="dc-floor" placeholder="Optional"></label>' +
          '</div>' +
          '<label class="fld"><span>Nearest landmark</span><input id="dc-mark" placeholder="Helps the driver find you"></label>'
          : '')
        : form.mode === 'pickup' ?
        '<div class="dc-pick">' +
          '<label class="dc-pickone"><input type="radio" name="dc-branch" value="Al Muroor" checked>' +
            '<span><strong>Al Muroor</strong>Guardian Towers, Al Rumaithi street</span></label>' +
          '<label class="dc-pickone"><input type="radio" name="dc-branch" value="Al Najda">' +
            '<span><strong>Al Najda</strong>Vision Towers, Mohammed Bin Butti street</span></label>' +
        '</div>' : '') +

      ((form.mode === 'dinein' && booked) ? '' :
      '<hr class="hair">' +
      '<div class="formgrid">' +
        '<label class="fld"><span>Full name</span><input id="dc-name" autocomplete="name" placeholder="Your name"></label>' +
        '<label class="fld"><span>Mobile</span><input id="dc-tel" type="tel" inputmode="tel" autocomplete="tel" placeholder="05X XXX XXXX"></label>' +
      '</div>' +
      '<label class="fld"><span>Second number <em>if we can&rsquo;t reach you</em></span>' +
        '<input id="dc-tel2" type="tel" inputmode="tel" placeholder="Optional but useful"></label>' +
      '') +
      '<label class="fld"><span>Notes for the kitchen</span>' +
        '<textarea id="dc-notes" placeholder="Allergies, no onion, leave at reception…"></textarea></label>';

    var blocked = (form.mode === 'delivery' && (!zone || belowMin)) ||
                  (form.mode === 'dinein' && !booked);

    foot.innerHTML =
      '<div class="dc-row"><span>Subtotal</span><span class="num">AED ' + money(sub) + '</span></div>' +
      (form.mode === 'delivery'
        ? '<div class="dc-row"><span>Delivery</span><span class="num">' + (zone ? 'AED ' + money(fee) : '—') + '</span></div>'
        : '') +
      '<div class="dc-row dc-row--tot"><span>Total</span><strong class="num">AED ' + money(sub + fee) + '</strong></div>' +
      (belowMin ? '<p class="dc-warn">Minimum for ' + esc(zone.name) + ' is AED ' + zone.min +
                  '. Add AED ' + money(zone.min - sub) + ' more to check out.</p>' : '') +
      '<button class="btn btn--primary" type="button" id="dc-place" style="width:100%"' +
        (blocked ? ' disabled' : '') + '>' +
        (form.mode === 'dinein' ? 'Confirm pre-order' : 'Place order') + '</button>' +
      '<button class="btn btn--ghost" type="button" id="dc-back" style="width:100%">Back to order</button>' +
      '<p class="dc-note">[TO CONFIRM] Coverage, fees and minimums are placeholders until Mosaic supplies their real zones.</p>';

    body.onclick = function (e) {
      var m = e.target.closest('[data-mode]');
      if (m) { form.mode = m.dataset.mode; paint(); }
    };
    var areaEl = body.querySelector('#dc-area');
    if (areaEl) areaEl.onchange = function () {
      form.area = areaEl.value;
      form.zone = areaEl.value === '__out' ? null : zoneFor(areaEl.value);
      paint();
    };
    foot.querySelector('#dc-back').onclick = function () { step = 'cart'; paint(); };
    var place = foot.querySelector('#dc-place');
    if (place) place.onclick = function () {
      if (form.mode === 'dinein') {
        if (!booked) { Cart.toast('Book a table first — dine-in orders are tied to a booking.'); return; }
        Cart.toast('Pre-order flow is not connected to a backend yet.');
        return;
      }
      var name = (body.querySelector('#dc-name') || {}).value || '';
      var tel  = (body.querySelector('#dc-tel')  || {}).value || '';
      if (!name.trim() || !tel.trim()) { Cart.toast('We need a name and a mobile number.'); return; }
      Cart.toast('Order flow is not connected to a backend yet.');
    };
  }

  /* ---------------------------------------------------------------- wiring */
  d.addEventListener('click', function (e) {
    var a = e.target.closest('[data-add]');
    if (a) {
      e.preventDefault();
      var q = Cart.add({ id: a.dataset.id, name: a.dataset.name, price: a.dataset.price });
      Cart.toast(a.dataset.name + ' added · ' + q + ' in your order');
      a.classList.add('is-added'); setTimeout(function () { a.classList.remove('is-added'); }, 900);
      return;
    }
    if (e.target.closest('[data-cart-open]')) { e.preventDefault(); open('cart'); }
  });
})(window, document);
