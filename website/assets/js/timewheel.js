/* Reusable Apple-style hour/minute wheel, constrained to real opening hours.
   Used by the booking form and by dine-in checkout. */
(function (w, d) {
  'use strict';

  /* Published on every page of mosaicrestaurant.com. 0 Sun … 6 Sat */
  var HOURS = {
    0: [480, 1410], 1: [480, 1410], 2: [480, 1410], 3: [480, 1410], 4: [480, 1410],
    5: [810, 1410],                    /* Friday opens 13:30 */
    6: [480, 1410]
  };
  var STEP = 15;                       /* reservation-industry standard slot */

  var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
  function human(h, m) {
    var ap = h < 12 ? 'AM' : 'PM', t = h % 12 === 0 ? 12 : h % 12;
    return t + ':' + pad(m) + ' ' + ap;
  }
  function rangeFor(dateStr) {
    var dow = dateStr ? new Date(dateStr + 'T12:00:00').getDay() : new Date().getDay();
    return HOURS[dow];
  }

  function TimeWheel(host, onChange) {
    host.classList.add('wheel-band');
    host.innerHTML =
      '<div class="wheel-cols">' +
        '<div class="wheel" tabindex="0" role="listbox" aria-label="Hour"></div>' +
        '<span class="wheel-sep" aria-hidden="true">:</span>' +
        '<div class="wheel" tabindex="0" role="listbox" aria-label="Minute"></div>' +
      '</div>';
    var cols = host.querySelectorAll('.wheel');
    var hourEl = cols[0], minEl = cols[1];
    var date = null, sel = { h: 19, m: 30 }, rafs = new WeakMap();

    function hoursList() {
      var r = rangeFor(date), out = [];
      for (var h = Math.floor(r[0] / 60); h <= Math.floor(r[1] / 60); h++)
        if (h * 60 <= r[1]) out.push(h);
      return out;
    }
    function minutesFor(h) {
      var r = rangeFor(date), out = [];
      for (var m = 0; m < 60; m += STEP) {
        var t = h * 60 + m;
        if (t >= r[0] && t <= r[1]) out.push(m);
      }
      return out;
    }
    function fill(wheel, items, cur, render) {
      wheel.innerHTML = '<div class="wheel__pad"></div>' + items.map(function (v) {
        return '<button class="wheel__i" type="button" role="option" data-v="' + v + '">' +
               render(v) + '</button>';
      }).join('') + '<div class="wheel__pad"></div>';
      var i = items.indexOf(cur); if (i < 0) i = 0;
      centre(wheel, wheel.querySelectorAll('.wheel__i')[i], false);
      return items[i];
    }
    function centre(wheel, el, smooth) {
      if (!el) return;
      wheel.scrollTo({ top: el.offsetTop - wheel.clientHeight / 2 + el.offsetHeight / 2,
                       behavior: smooth ? 'smooth' : 'auto' });
      soon(wheel);
    }
    function soon(wheel) {
      cancelAnimationFrame(rafs.get(wheel));
      rafs.set(wheel, requestAnimationFrame(function () { mark(wheel); }));
    }
    function mark(wheel) {
      var mid = wheel.scrollTop + wheel.clientHeight / 2, best = null, bd = 1e9;
      wheel.querySelectorAll('.wheel__i').forEach(function (el) {
        var dist = Math.abs(el.offsetTop + el.offsetHeight / 2 - mid);
        el.classList.remove('is-on'); el.setAttribute('aria-selected', 'false');
        if (dist < bd) { bd = dist; best = el; }
      });
      if (!best) return;
      best.classList.add('is-on'); best.setAttribute('aria-selected', 'true');
      var v = +best.dataset.v;
      if (wheel === hourEl && v !== sel.h) { sel.h = v; drawMinutes(); }
      else if (wheel === minEl) sel.m = v;
      onChange && onChange(api.value());
    }
    function drawMinutes() {
      var mm = minutesFor(sel.h); if (!mm.length) mm = [0];
      sel.m = fill(minEl, mm, sel.m, pad);
    }

    [hourEl, minEl].forEach(function (wheel) {
      wheel.addEventListener('scroll', function () { soon(wheel); }, { passive: true });
      wheel.addEventListener('click', function (e) {
        var i = e.target.closest('.wheel__i'); if (i) centre(wheel, i, true);
      });
      wheel.addEventListener('keydown', function (e) {
        var on = wheel.querySelector('.is-on'); if (!on) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); centre(wheel, on.nextElementSibling, true); }
        if (e.key === 'ArrowUp')   { e.preventDefault(); centre(wheel, on.previousElementSibling, true); }
      });
    });

    var api = {
      setDate: function (v) {
        date = v;
        var hs = hoursList();
        if (hs.indexOf(sel.h) < 0) sel.h = hs.indexOf(19) > -1 ? 19 : hs[Math.floor(hs.length / 2)];
        sel.h = fill(hourEl, hs, sel.h, function (h) {
          var ap = h < 12 ? 'AM' : 'PM', t = h % 12 === 0 ? 12 : h % 12;
          return t + '<em>' + ap + '</em>';
        });
        drawMinutes();
        onChange && onChange(api.value());
      },
      value: function () {
        return { h: sel.h, m: sel.m, iso: pad(sel.h) + ':' + pad(sel.m), human: human(sel.h, sel.m) };
      },
      openingLabel: function () {
        var r = rangeFor(date);
        return 'Open ' + human(Math.floor(r[0] / 60), r[0] % 60) +
               ' – ' + human(Math.floor(r[1] / 60), r[1] % 60) + ' that day';
      }
    };
    return api;
  }

  w.MosaicTime = { Wheel: TimeWheel, human: human, rangeFor: rangeFor, STEP: STEP };
})(window, document);
