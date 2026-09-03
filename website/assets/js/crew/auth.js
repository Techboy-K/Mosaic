/* Crew session + permission context.
   Every page calls Crew.requirePage(key). The check here is a convenience so we
   can render the right UI — the real enforcement is Row Level Security in
   Postgres, which applies whatever the browser believes. */
(function (w) {
  'use strict';
  var cfg = w.MOSAIC_SUPABASE;
  var sb  = w.supabase.createClient(cfg.url, cfg.anonKey, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: false }
  });

  var ctx = null;   // { user, profile, roles, level, perms:Set, pages:[], restaurants:[] }

  /* A boot query that fails must never degrade to an empty result: empty roles
     reads as "no permissions" and locks a legitimate user out of their own
     pages. Retry once (the first request after sign-in can race the client's
     token attachment), then surface the error so the caller can say so. */
  async function q(label, builder) {
    var r = await builder();
    if (r.error) {
      await new Promise(function (ok) { setTimeout(ok, 350); });
      r = await builder();
    }
    if (r.error) { var e = new Error(label + ': ' + r.error.message); e.stage = label; throw e; }
    return r.data;
  }

  async function loadContext() {
    var s = await sb.auth.getSession();
    var session = s.data.session;
    if (!session) { ctx = null; return null; }

    var uid = session.user.id;
    var res = await Promise.all([
      q('profile',     function () { return sb.from('profiles').select('*').eq('id', uid).single(); }),
      q('roles',       function () { return sb.from('user_roles').select('role_id, roles(*)').eq('user_id', uid); }),
      q('restaurants', function () { return sb.from('user_restaurants').select('restaurant_id, restaurants(*)').eq('user_id', uid); })
    ]);
    var profile = res[0];
    var roles   = (res[1] || []).map(function (r) { return r.roles; }).filter(Boolean);
    var rests   = (res[2] || []).map(function (r) { return r.restaurants; }).filter(Boolean);

    if (!profile || !profile.is_active) { await sb.auth.signOut(); ctx = null; return null; }

    var ids = roles.map(function (r) { return r.id; });
    var perms = new Set(), pages = [];
    if (ids.length) {
      var pr = await q('permissions', function () {
        return sb.from('role_permissions').select('permissions(key)').in('role_id', ids);
      });
      (pr || []).forEach(function (r) { if (r.permissions) perms.add(r.permissions.key); });
      var pg = await q('pages', function () {
        return sb.from('role_pages').select('page_key, sort_order').in('role_id', ids).order('sort_order');
      });
      var seen = {};
      (pg || []).forEach(function (r) {
        if (!seen[r.page_key]) { seen[r.page_key] = 1; pages.push(r.page_key); }
      });
    }
    ctx = {
      user: session.user, profile: profile, roles: roles, restaurants: rests,
      level: roles.length ? Math.min.apply(null, roles.map(function (r) { return r.hierarchy_level; })) : 9999,
      perms: perms, pages: pages
    };
    return ctx;
  }

  function bootError(err) {
    var d = document, box = d.createElement('div');
    box.setAttribute('role', 'alert');
    box.style.cssText = 'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;' +
      'justify-content:center;background:#141928;color:#E7DED3;font:15px/1.6 system-ui,sans-serif;padding:24px;';
    box.innerHTML = '<div style="max-width:420px;text-align:center">' +
      '<div style="font:600 20px/1.3 Georgia,serif;margin-bottom:10px">Couldn\u2019t load your account</div>' +
      '<p style="margin:0 0 6px;opacity:.85">Your session is fine \u2014 the portal couldn\u2019t reach the server.</p>' +
      '<p style="margin:0 0 18px;font-size:13px;opacity:.55"></p>' +
      '<button style="background:#B68052;border:0;color:#141928;font:600 14px system-ui;' +
      'padding:11px 22px;border-radius:6px;cursor:pointer">Try again</button></div>';
    box.querySelector('p:nth-of-type(2)').textContent = String(err && err.message || err);
    box.querySelector('button').onclick = function () { location.reload(); };
    (d.body || d.documentElement).appendChild(box);
  }

  var Crew = {
    sb: sb,
    ctx: function () { return ctx; },
    load: loadContext,
    can: function (p) { return !!(ctx && ctx.perms.has(p)); },
    isOwner: function () { return !!(ctx && ctx.profile.is_system_owner); },
    isSuperadmin: function () { return !!(ctx && ctx.level === 0); },

    async signIn(email, password) {
      var r = await sb.auth.signInWithPassword({ email: email, password: password });
      if (r.error) return { ok: false, message: r.error.message };
      var c;
      try { c = await loadContext(); }
      catch (e) { return { ok: false, message: "Signed in, but your profile couldn't be loaded. Check your connection and try again." }; }
      if (!c) return { ok: false, message: 'This account is not active. Speak to a manager.' };
      await sb.from('profiles').update({ last_login_at: new Date().toISOString() }).eq('id', c.user.id);
      return { ok: true, ctx: c };
    },

    async signOut() { await sb.auth.signOut(); ctx = null; location.href = 'index.html'; },

    /* Gate a page. Returns the context, or redirects.
       A superadmin is never gated: "manages everything" is the definition of the
       role, so a missing page grant must not be able to lock them out. */
    async requirePage(pageKey) {
      var c;
      try { c = await loadContext(); }
      catch (e) {
        /* A boot query failed. This is an infrastructure problem, not an
           authorization one — bouncing to login would read as a surprise
           logout, and denied.html would be a lie. Say what happened. */
        bootError(e);
        return null;
      }
      if (!c) { location.replace('index.html?next=' + encodeURIComponent(location.pathname.split('/').pop())); return null; }
      if (c.level === 0) return c;
      if (pageKey && c.pages.indexOf(pageKey) === -1) { location.replace('denied.html'); return null; }
      return c;
    },

    /* Where should this user land after login? First page their role grants. */
    homeFor: function (c) {
      var map = { dashboard:'dashboard.html', orders:'orders.html', kitchen:'kitchen.html',
                  monitor:'monitor.html', menu:'menu.html', users:'users.html',
                  roles:'roles.html', restaurants:'restaurants.html', reports:'reports.html',
                  audit:'audit.html', settings:'settings.html', 'new-order':'new-order.html',
                  'quick-notes':'quick-notes.html', history:'history.html' };
      for (var i = 0; i < c.pages.length; i++) if (map[c.pages[i]]) return map[c.pages[i]];
      return 'denied.html';
    }
  };

  sb.auth.onAuthStateChange(function (evt) {
    if (evt === 'SIGNED_OUT' && !/\/crew\/(index\.html)?$/.test(location.pathname)) {
      location.replace('index.html');
    }
  });

  w.Crew = Crew;
})(window);
