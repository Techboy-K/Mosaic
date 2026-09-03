/* Crew chrome: navigation derived from role_pages, restaurant switcher, sign-out. */
(function (w, d) {
  'use strict';

  /* Navigation is grouped by what the person is trying to do, not by table name.
     Roles with only a handful of pages get a flat bar — a dropdown holding two
     items is worse than no dropdown. */
  var GROUPS = [
    { key:'service',   label:'Service',   pages:['orders','new-order','quick-notes','kitchen'] },
    { key:'floor',     label:'Floor',     pages:['monitor','bookings','history'] },
    { key:'catalogue', label:'Menu',      pages:['menu'] },
    { key:'people',    label:'People',    pages:['users','roles'] },
    { key:'business',  label:'Business',  pages:['restaurants','reports','audit','settings'] }
  ];
  var PAGES = {
    dashboard:   ['Dashboard',      'dashboard.html'],
    orders:      ['Orders',         'orders.html'],
    'new-order': ['New order',      'new-order.html'],
    'quick-notes':['Quick notes',   'quick-notes.html'],
    kitchen:     ['Kitchen',        'kitchen.html'],
    monitor:     ['Monitor',        'monitor.html'],
    bookings:    ['Bookings',       'bookings.html'],
    history:     ['History',        'history.html'],
    menu:        ['Menu',           'menu.html'],
    users:       ['Staff',          'users.html'],
    roles:       ['Roles',          'roles.html'],
    restaurants: ['Restaurants',    'restaurants.html'],
    reports:     ['Reports',        'reports.html'],
    audit:       ['Audit log',      'audit.html'],
    settings:    ['Settings',       'settings.html']
  };
  var FLAT_LIMIT = 4;

  /* Crew links are root-absolute. A relative 'dashboard.html' resolves against
     the *directory* of the current URL, so at /crew (no trailing slash) it
     becomes /dashboard.html and 404s. Absolute paths hold at /crew, /crew/,
     and /crew/dashboard alike. */
  function u(f) { return '/crew/' + f; }
  function stem(x) { return String(x || '').replace(/\.html$/, ''); }

  w.CrewShell = {
    render: function (ctx, active) {
      var last = stem(location.pathname.split('/').pop());
      var here = (!last || last === 'crew') ? 'index' : last;
      var mine = ctx.pages.filter(function (k) { return PAGES[k]; });
      var isHere = function (k) { return stem(PAGES[k][1]) === here || k === active; };

      var nav;
      if (mine.length <= FLAT_LIMIT) {
        nav = mine.map(function (k) {
          return '<a href="' + u(PAGES[k][1]) + '"' + (isHere(k) ? ' aria-current="page"' : '') +
                 '>' + PAGES[k][0] + '</a>'; }).join('');
      } else {
        var parts = [];
        if (mine.indexOf('dashboard') > -1)
          parts.push('<a href="' + u('dashboard.html') + '"' + (isHere('dashboard') ? ' aria-current="page"' : '') +
                     '>Dashboard</a>');
        GROUPS.forEach(function (g) {
          var items = g.pages.filter(function (k) { return mine.indexOf(k) > -1; });
          if (!items.length) return;
          if (items.length === 1) {
            var k = items[0];
            parts.push('<a href="' + u(PAGES[k][1]) + '"' + (isHere(k) ? ' aria-current="page"' : '') +
                       '>' + PAGES[k][0] + '</a>');
            return;
          }
          var on = items.some(isHere);
          parts.push(
            '<div class="navgrp' + (on ? ' is-on' : '') + '">' +
              '<button type="button" aria-expanded="false">' + g.label +
                '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
                'stroke-width="3"><path d="m5 9 7 7 7-7"/></svg></button>' +
              '<div class="navgrp__m">' + items.map(function (k) {
                return '<a href="' + u(PAGES[k][1]) + '"' + (isHere(k) ? ' aria-current="page"' : '') +
                       '>' + PAGES[k][0] + '</a>'; }).join('') + '</div>' +
            '</div>');
        });
        nav = parts.join('');
      }

      var role = ctx.roles[0] || { name: '—', color: '#B68052' };
      var initials = (ctx.profile.full_name || ctx.profile.email)
        .split(/[\s.@]+/).slice(0, 2).map(function (x) { return x[0]; }).join('').toUpperCase();
      var avatar = ctx.profile.avatar_path
        ? '<img class="crew-av" src="' + ctx.profile.avatar_path + '" alt="">'
        : '<span class="crew-av" style="background:' + (role.color || '#B68052') + '">' + initials + '</span>';

      /* Branch is NOT a global switch. The menu, prices and roles are shared
         across both restaurants, so a system-wide selector implies a split that
         does not exist. Branch is chosen where it actually applies — on Monitor. */
      var where = ctx.restaurants.length > 1
        ? '<span class="crew-rest-one" title="You cover both branches">Both branches</span>'
        : (ctx.restaurants[0] ? '<span class="crew-rest-one">' + ctx.restaurants[0].name + '</span>' : '');

      d.getElementById('crew-shell').innerHTML =
        '<header class="crew-head">' +
          '<a class="crew-brand" href="' + (mine[0] ? u(PAGES[mine[0]][1]) : '#') + '">' +
            '<img src="../assets/img/brand/logo.webp" alt="" width="34" height="34">' +
            '<span>MOSAIC<small>Crew</small></span></a>' +
          '<button class="crew-burger" type="button" id="crew-burger" aria-label="Menu">' +
            '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
            'stroke-width="1.7"><path d="M3.5 6.5h17"/><path d="M3.5 12h17"/><path d="M3.5 17.5h17"/></svg>' +
          '</button>' +
          '<nav class="crew-nav" id="crew-nav">' + nav + '</nav>' +
          '<div class="crew-right">' + where +
            '<button class="crew-me" type="button" id="crew-me">' + avatar +
              '<span class="crew-me__t"><b>' + (ctx.profile.full_name || ctx.profile.email) + '</b>' +
              '<i>' + role.name + (ctx.profile.is_system_owner ? ' · owner' : '') + '</i></span>' +
            '</button>' +
            '<div class="crew-menu" id="crew-menu" hidden>' +
              '<a href="' + u('profile.html') + '">My profile</a>' +
              '<button type="button" id="crew-out">Sign out</button>' +
            '</div>' +
          '</div>' +
        '</header>';

      var me = d.getElementById('crew-me'), menu = d.getElementById('crew-menu');
      me.onclick = function (e) { e.stopPropagation(); menu.hidden = !menu.hidden; };
      d.getElementById('crew-out').onclick = function () { Crew.signOut(); };

      d.querySelectorAll('.navgrp > button').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
          e.stopPropagation();
          var g = btn.parentNode, wasOpen = g.classList.contains('is-open');
          d.querySelectorAll('.navgrp').forEach(function (x) {
            x.classList.remove('is-open'); x.querySelector('button').setAttribute('aria-expanded','false'); });
          if (!wasOpen) { g.classList.add('is-open'); btn.setAttribute('aria-expanded','true'); }
        });
      });
      var burger = d.getElementById('crew-burger');
      burger.onclick = function (e) { e.stopPropagation();
        d.getElementById('crew-nav').classList.toggle('is-open'); };
      d.addEventListener('click', function () {
        menu.hidden = true;
        d.querySelectorAll('.navgrp').forEach(function (x) { x.classList.remove('is-open'); });
        d.getElementById('crew-nav').classList.remove('is-open');
      });
    },
    /* kept for callers; branch scoping now comes from RLS plus each page's own picker */
    restaurant: function () { return 'all'; }
  };
})(window, document);

/* ---------- notification centre ---------- */
(function (w, d) {
  'use strict';
  var open = false;
  w.CrewNotify = {
    async mount(ctx) {
      var host = d.querySelector('.crew-right');
      if (!host || d.getElementById('nbell')) return;
      var b = d.createElement('button');
      b.className = 'nbell'; b.id = 'nbell'; b.type = 'button';
      b.setAttribute('aria-label', 'Notifications');
      b.innerHTML = '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="1.5"><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/>' +
        '<path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg><span class="nbell__n" hidden>0</span>';
      host.insertBefore(b, host.firstChild);
      var panel = d.createElement('div');
      panel.className = 'npanel'; panel.id = 'npanel'; panel.hidden = true;
      host.appendChild(panel);

      async function refresh() {
        var r = await Crew.sb.from('notifications').select('*')
          .order('created_at', { ascending: false }).limit(30);
        var rows = r.data || [];
        var unread = rows.filter(function (x) { return !x.read_at; }).length;
        var n = d.querySelector('.nbell__n');
        n.textContent = unread; n.hidden = unread === 0;
        panel.innerHTML = '<header><b>Notifications</b>' +
          (unread ? '<button type="button" id="nall">Mark all read</button>' : '') + '</header>' +
          (rows.length ? rows.map(function (x) {
            return '<a class="nrow' + (x.read_at ? '' : ' is-new') + '" href="' +
              (x.order_id ? 'orders.html' : '#') + '">' +
              '<b>' + (x.title||'') + '</b>' +
              (x.body ? '<span>' + x.body + '</span>' : '') +
              '<time>' + new Date(x.created_at).toLocaleTimeString('en-GB',
                { hour:'2-digit', minute:'2-digit' }) + '</time></a>'; }).join('')
            : '<p class="crew-empty" style="padding:26px 0">Nothing yet</p>');
        var all = d.getElementById('nall');
        if (all) all.onclick = async function (e) {
          e.stopPropagation();
          await Crew.sb.from('notifications').update({ read_at: new Date().toISOString() })
            .is('read_at', null);
          refresh();
        };
      }
      b.onclick = function (e) { e.stopPropagation(); open = !open; panel.hidden = !open; if (open) refresh(); };
      d.addEventListener('click', function () { open = false; panel.hidden = true; });
      panel.addEventListener('click', function (e) { e.stopPropagation(); });

      Crew.sb.channel('crew-notify')
        .on('postgres_changes', { event:'INSERT', schema:'public', table:'notifications' }, refresh)
        .subscribe();
      refresh();
      setInterval(refresh, 60000);
    }
  };
})(window, document);
