/* One shared table booking, readable from the booking form and from checkout,
   so a dine-in order and a reservation can never disagree. */
(function (w) {
  'use strict';
  var KEY = 'mosaic.booking.v1', subs = [];
  function read() { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } }
  function write(b) { try { localStorage.setItem(KEY, JSON.stringify(b)); } catch (e) {}
                      subs.forEach(function (f) { f(b); }); }
  w.MosaicBooking = {
    get: read,
    set: function (patch) { write(Object.assign(read(), patch)); },
    clear: function () { write({}); },
    /* a booking only counts once it can actually be honoured */
    complete: function () { var b = read(); return !!(b.branch && b.date && b.time && b.guests); },
    summary: function () {
      var b = read();
      if (!b.date) return '';
      var dt = new Date(b.date + 'T12:00:00');
      var day = dt.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
      return b.branch + ' · ' + day + ' · ' + (b.timeHuman || b.time) + ' · ' + b.guests;
    },
    onChange: function (f) { subs.push(f); f(read()); }
  };
})(window);
