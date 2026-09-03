/* Shared order machinery: fetching, rendering, transitions, the server-owned
   undo bar, realtime, and notification sound. Used by waiter, chef and supervisor. */
(function (w, d) {
  'use strict';
  var STATUS = {}, REST = {}, sub = null;

  async function statusDefs() {
    if (Object.keys(STATUS).length) return STATUS;
    var r = await Crew.sb.from('order_status_defs').select('*').order('sort_order');
    (r.data||[]).forEach(function (s) { STATUS[s.key] = s; });
    var q = await Crew.sb.from('restaurants').select('id,name').order('name');
    (q.data||[]).forEach(function (x) { REST[x.id] = x.name; });
    return STATUS;
  }
  function restName(id) { return REST[id] || 'Unassigned branch'; }

  var esc = function (s) { return String(s==null?'':s).replace(/[&<>"']/g, function (c) {
    return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]; }); };

  function age(iso) {
    var m = Math.floor((Date.now() - new Date(iso)) / 60000);
    if (m < 1) return 'just now';
    if (m < 60) return m + 'm';
    return Math.floor(m/60) + 'h ' + (m%60) + 'm';
  }

  function restaurantFilter(q) {
    var r = CrewShell.restaurant();
    return r && r !== 'all' ? q.eq('restaurant_id', r) : q;
  }

  async function fetchOrders(statuses, opts) {
    opts = opts || {};
    var q = Crew.sb.from('orders')
      .select('*, order_items(*)')
      .in('status', statuses)
      .order('priority', { ascending: false })
      .order('created_at', { ascending: true });
    q = restaurantFilter(q);
    if (opts.mine) q = q.or('owner_id.eq.' + Crew.ctx().user.id + ',owner_id.is.null');
    var r = await q;
    return r.data || [];
  }

  function card(o, actions, opts) {
    opts = opts || {};
    var s = STATUS[o.status] || {};
    var items = (o.order_items||[]).map(function (i) {
      return '<li><b>' + i.qty + '&times;</b><span>' + esc(i.name) +
        (i.notes ? '<i>' + esc(i.notes) + '</i>' : '') + '</span></li>'; }).join('');
    return '<article class="ocard" data-pri="' + o.priority + '" data-id="' + o.id + '">' +
      '<div class="ocard__h"><div><span class="ocard__n">#' + o.number + '</span>' +
        (o.table_label ? ' <span class="ocard__t">' + esc(o.table_label) + '</span>' : '') +
        (opts.hideBranch ? '' :
          '<span class="ocard__br">' + esc(restName(o.restaurant_id)) + '</span>') + '</div>' +
        (opts.hideStatus ? '' :
          '<span class="ostat" style="background:' + (s.colour||'#7A7F8C') + '">' +
          esc(s.label||o.status) + '</span>') + '</div>' +
      (o.priority !== 'NORMAL'
        ? '<span class="opri opri--' + o.priority.toLowerCase() + '">' +
          (o.priority === 'URGENT' ? 'Urgent' : 'High') + '</span>' : '') +
      (o.is_quick_note
        ? '<div class="ocard__note"><b>Quick note</b><br>' +
            esc(o.quick_note_text||'').replace(/\n/g,'<br>') + '</div>'
        : '<ul class="ocard__items">' + (items || '<li><i>No items yet</i></li>') + '</ul>') +
      (o.notes ? '<div class="ocard__note">' + esc(o.notes) + '</div>' : '') +
      '<div class="ocard__age">' + age(o.created_at) + ' ago</div>' +
      (actions ? '<div class="ocard__acts">' + actions(o) + '</div>' : '') +
    '</article>';
  }

  /* ---------------- transitions ---------------- */
  async function move(orderId, to, meta) {
    var r = await Crew.sb.rpc('transition_order',
      { p_order: orderId, p_to: to, p_meta: meta || {} });
    if (r.error) { alert(r.error.message); return null; }
    // find the event we just created so the undo bar can reference it
    var e = await Crew.sb.from('order_events').select('*')
      .eq('order_id', orderId).order('id', { ascending:false }).limit(1).single();
    if (e.data && e.data.undo_expires_at && !e.data.undone_at) showUndo(e.data);
    return r.data;
  }

  /* The countdown is cosmetic. The server decides whether undo is still valid,
     so changing the browser clock buys nothing. */
  var undoTimer = null, undoBar = null;
  function showUndo(evt) {
    if (!undoBar) {
      undoBar = d.createElement('div'); undoBar.className = 'undo-bar';
      d.body.appendChild(undoBar);
    }
    clearInterval(undoTimer);
    function tick() {
      var left = Math.max(0, Math.round((new Date(evt.undo_expires_at) - Date.now())/1000));
      if (left <= 0) { clearInterval(undoTimer); undoBar.classList.remove('is-up'); return; }
      undoBar.innerHTML = '<span>Handed on &mdash; order moved</span>' +
        '<button type="button" id="undo-go">Undo <b>' + left + '</b></button>';
      d.getElementById('undo-go').onclick = async function () {
        var r = await Crew.sb.rpc('undo_transition', { p_event: evt.id });
        clearInterval(undoTimer); undoBar.classList.remove('is-up');
        if (r.error) alert(r.error.message);
        else d.dispatchEvent(new CustomEvent('orders:changed'));
      };
    }
    tick(); undoBar.classList.add('is-up');
    undoTimer = setInterval(tick, 1000);
  }

  /* ---------------- realtime ---------------- */
  function watch(onChange) {
    if (sub) Crew.sb.removeChannel(sub);
    sub = Crew.sb.channel('crew-orders')
      .on('postgres_changes', { event:'*', schema:'public', table:'orders' }, onChange)
      .on('postgres_changes', { event:'INSERT', schema:'public', table:'notifications' },
          function (p) { Sound.play(p.new.kind); onChange(p); })
      .subscribe();
    return sub;
  }

  /* ---------------- audio ---------------- */
  var Sound = {
    enabled: localStorage.getItem('mosaic.sound') !== 'off',
    volume: parseFloat(localStorage.getItem('mosaic.volume') || '0.85'),
    ctx: null,
    unlock: function () {
      if (!this.ctx) { try { this.ctx = new (w.AudioContext||w.webkitAudioContext)(); } catch(e){} }
      if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume();
    },

    /* A struck bell, not a beep. Bells are inharmonic — the partials sit at
       non-integer ratios of the fundamental, which is what stops it sounding
       like a test tone. Sharp attack, long exponential tail, and the higher
       partials decay faster than the low ones, as they do in real metal. */
    _bell: function (f0, when, gain, decay) {
      var c = this.ctx, out = c.createGain();
      out.gain.value = gain;
      out.connect(c.destination);
      // ratios and relative loudness of a struck tubular bell
      var partials = [[0.56,1.0,1.0],[0.92,0.65,0.9],[1.19,0.52,0.65],[1.71,0.42,0.45],
                      [2.00,0.35,0.38],[2.74,0.22,0.25],[3.00,0.18,0.2],[3.76,0.12,0.15]];
      partials.forEach(function (p) {
        var o = c.createOscillator(), g = c.createGain();
        o.type = 'sine';
        o.frequency.value = f0 * p[0];
        var d = decay * p[2];
        g.gain.setValueAtTime(0, when);
        g.gain.linearRampToValueAtTime(p[1] * 0.9, when + 0.004);   // hard strike
        g.gain.exponentialRampToValueAtTime(0.0001, when + d);
        o.connect(g); g.connect(out);
        o.start(when); o.stop(when + d + 0.05);
      });
      // the metallic "ping" of the hammer hitting
      var nb = c.createBuffer(1, c.sampleRate * 0.03, c.sampleRate);
      var nd = nb.getChannelData(0);
      for (var i = 0; i < nd.length; i++) nd[i] = (Math.random()*2-1) * (1 - i/nd.length);
      var ns = c.createBufferSource(), nf = c.createBiquadFilter(), ng = c.createGain();
      ns.buffer = nb; nf.type = 'bandpass'; nf.frequency.value = f0 * 4; nf.Q.value = 2;
      ng.gain.setValueAtTime(0.25, when);
      ng.gain.exponentialRampToValueAtTime(0.0001, when + 0.06);
      ns.connect(nf); nf.connect(ng); ng.connect(out);
      ns.start(when); ns.stop(when + 0.06);
    },

    play: function (kind) {
      if (!this.enabled) return;
      this.unlock();
      if (!this.ctx) return;
      var t = this.ctx.currentTime + 0.01, v = this.volume;
      if (kind === 'order_ready') {          // two rising strikes — plates are up
        this._bell(660, t,        v * 0.9, 1.7);
        this._bell(990, t + 0.19, v * 0.9, 2.2);
      } else if (kind === 'priority') {      // urgent: three quick strikes
        this._bell(880, t,        v, 0.9);
        this._bell(880, t + 0.16, v, 0.9);
        this._bell(1170, t + 0.32, v, 1.8);
      } else if (kind === 'order_new') {     // single warm strike
        this._bell(587, t, v * 0.95, 2.0);
      } else {
        this._bell(740, t, v * 0.7, 1.3);
      }
    },
    setEnabled: function (v) { this.enabled=v; localStorage.setItem('mosaic.sound', v?'on':'off'); },
    setVolume:  function (v) { this.volume=v; localStorage.setItem('mosaic.volume', String(v)); }
  };

  /* browsers block audio until a gesture — ask once, unobtrusively */
  function soundBar() {
    if (Sound.ctx) return '';
    return '<div class="soundbar" id="soundbar">' +
      '<span>Turn on sound so you hear new orders</span>' +
      '<button class="btn btn--wine btn--sm" type="button" id="sound-on">Enable sound</button></div>';
  }
  d.addEventListener('click', function (e) {
    if (e.target.id === 'sound-on') {
      Sound.unlock(); Sound.setEnabled(true); Sound.play('order_new');
      var b = d.getElementById('soundbar'); if (b) b.remove();
    }
  });

  /* When the viewer can see more than one branch, split the queue by branch
     rather than interleaving them — mixing Muroor and Najda tickets is exactly
     how the wrong plate goes to the wrong room. */
  function renderGrouped(rows, actions, emptyMsg) {
    if (!rows.length) return '<p class="crew-empty">' + emptyMsg + '</p>';
    var ids = [];
    rows.forEach(function (o) { if (ids.indexOf(o.restaurant_id) === -1) ids.push(o.restaurant_id); });
    if (ids.length < 2) return '<div class="oq">' + rows.map(function (o) {
      return card(o, actions); }).join('') + '</div>';
    ids.sort(function (a, b) { return restName(a).localeCompare(restName(b)); });
    return ids.map(function (rid) {
      var mine = rows.filter(function (o) { return o.restaurant_id === rid; });
      return '<section class="obranch">' +
        '<header class="obranch__h"><h2>' + esc(restName(rid)) + '</h2>' +
        '<span>' + mine.length + '</span></header>' +
        '<div class="oq">' + mine.map(function (o) { return card(o, actions); }).join('') + '</div>' +
      '</section>';
    }).join('');
  }

  w.CrewOrders = { statusDefs:statusDefs, STATUS:STATUS, restName:restName, renderGrouped:renderGrouped, fetchOrders:fetchOrders, card:card, move:move,
                   watch:watch, Sound:Sound, soundBar:soundBar, age:age, esc:esc,
                   restaurantFilter:restaurantFilter };
})(window, document);
