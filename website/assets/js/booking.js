/* Table booking form. Publishes to MosaicBooking so a dine-in order can attach
   itself to the same reservation. */
(function (d) {
  'use strict';
  var root = d.getElementById('book');
  if (!root) return;

  var dateEl  = d.getElementById('bk-date');
  var guestEl = d.getElementById('bk-guests');
  var typeEl  = d.getElementById('bk-type');
  var nameEl  = d.getElementById('bk-name');
  var telEl   = d.getElementById('bk-tel');
  var noteEl  = d.getElementById('bk-hours');
  var hostEl  = d.getElementById('bk-wheel');
  var foodEl  = d.getElementById('bk-food');
  var cartLine= d.getElementById('bk-cartline');

  var wheel = MosaicTime.Wheel(hostEl, function (v) {
    MosaicBooking.set({ time: v.iso, timeHuman: v.human });
  });

  var t = new Date(); t.setMinutes(t.getMinutes() - t.getTimezoneOffset());
  dateEl.min = t.toISOString().slice(0, 10);
  if (!dateEl.value) dateEl.value = dateEl.min;

  function pushDate() {
    wheel.setDate(dateEl.value);
    noteEl.textContent = wheel.openingLabel();
    MosaicBooking.set({ date: dateEl.value });
  }
  dateEl.addEventListener('change', pushDate);

  /* branch selector doubles as the card switcher */
  var btns  = [].slice.call(d.querySelectorAll('[data-branch]'));
  var cards = [].slice.call(d.querySelectorAll('[data-branch-card]'));
  function setBranch(name) {
    btns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.branch === name)); });
    cards.forEach(function (c) { c.classList.toggle('is-active', c.dataset.branchCard === name); });
    MosaicBooking.set({ branch: name });
  }
  btns.forEach(function (b) { b.addEventListener('click', function () { setBranch(b.dataset.branch); }); });

  [[guestEl,'guests'],[typeEl,'type'],[nameEl,'name'],[telEl,'tel']].forEach(function (pair) {
    if (!pair[0]) return;
    pair[0].addEventListener('input',  function () { MosaicBooking.set(kv(pair[1], pair[0].value)); });
    pair[0].addEventListener('change', function () { MosaicBooking.set(kv(pair[1], pair[0].value)); });
  });
  function kv(k, v) { var o = {}; o[k] = v; return o; }

  /* ---- pre-order prompt: eat sooner, or order at the table ---- */
  function paintFood() {
    if (!foodEl) return;
    var n = w_count();
    foodEl.querySelectorAll('[data-pre]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.pre === (MosaicBooking.get().preorder || 'later')));
    });
    if (cartLine) {
      cartLine.hidden = n === 0;
      cartLine.textContent = n + (n === 1 ? ' dish' : ' dishes') +
        ' waiting · AED ' + (window.MosaicCart ? MosaicCart.total().toFixed(0) : '0');
    }
  }
  function w_count() { return window.MosaicCart ? MosaicCart.count() : 0; }

  if (foodEl) {
    foodEl.addEventListener('click', function (e) {
      var b = e.target.closest('[data-pre]');
      if (!b) return;
      MosaicBooking.set({ preorder: b.dataset.pre });
      paintFood();
      if (b.dataset.pre === 'now' && window.MosaicCart) {
        if (w_count()) MosaicCart.open('cart');
        else location.href = 'menu.html';
      }
    });
  }
  if (window.MosaicCart) MosaicCart.onChange(paintFood);

  /* submit: the anon key can only reach public_create_booking(), which inserts a
     pending booking and can read nothing back */
  var form = root.querySelector('form');
  if (form && window.MOSAIC_PUBLIC) {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      var b = MosaicBooking.get();
      var name = (nameEl && nameEl.value || '').trim();
      var tel  = (telEl && telEl.value || '').trim();
      if (name.length < 2)  return note('Please give us a name for the table.', true);
      if (tel.length < 7)   return note('We need a phone number in case anything changes.', true);
      if (!b.date || !b.time) return note('Pick a date and time.', true);

      var btn = form.querySelector('[type=submit]');
      btn.disabled = true; var was = btn.textContent; btn.textContent = 'Booking…';
      try {
        var res = await fetch(window.MOSAIC_PUBLIC.url + '/rest/v1/rpc/public_create_booking', {
          method: 'POST',
          headers: { 'apikey': window.MOSAIC_PUBLIC.anonKey, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            p_restaurant: window.MOSAIC_PUBLIC.restaurants[b.branch],
            p_name: name, p_phone: tel, p_email: null,
            p_party: parseInt(b.guests, 10) || 2,
            p_date: b.date, p_time: b.time,
            p_type: b.type || 'Family',
            p_notes: (document.getElementById('bk-notes') || {}).value || null })
        });
        var out = await res.json();
        btn.disabled = false; btn.textContent = was;
        if (!res.ok) return note(out.message || 'That did not go through. Please call us.', true);
        note('Booked. Your reference is ' + out + ' — we will text you shortly.', false);
        form.querySelectorAll('input,textarea').forEach(function (i) {
          if (i.type !== 'date') i.value = ''; });
      } catch (err) {
        btn.disabled = false; btn.textContent = was;
        note('We could not reach the booking system. Please call the branch.', true);
      }
    });
  }
  function note(msg, bad) {
    var el = document.getElementById('bk-result');
    if (!el) { el = document.createElement('p'); el.id = 'bk-result'; form.appendChild(el); }
    el.className = 'bk-result' + (bad ? ' is-bad' : ' is-ok');
    el.textContent = msg;
  }
  setBranch((btns[0] || {}).dataset ? btns[0].dataset.branch : 'Al Muroor');
  pushDate();
  MosaicBooking.set({ guests: guestEl ? guestEl.value : '', type: typeEl ? typeEl.value : '' });
  paintFood();
})(document);
