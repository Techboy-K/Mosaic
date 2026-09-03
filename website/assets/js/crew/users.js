/* Staff management — kanban by role, drag to move, profile drawer.
   Every mutation goes through the staff-admin edge function, which re-derives
   the caller's authority server-side. The UI decides what to OFFER; the server
   decides what is ALLOWED. */
(function (w, d) {
  'use strict';
  var S = { roles: [], users: [], restaurants: [], ctx: null };

  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]; }); };
  var initials = function (n, e) { return (n || e || '?')
    .split(/[\s.@]+/).slice(0,2).map(function (x) { return x[0]; }).join('').toUpperCase(); };

  async function fn(action, payload) {
    var s = await Crew.sb.auth.getSession();
    var r = await fetch(w.MOSAIC_SUPABASE.url + '/functions/v1/staff-admin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + s.data.session.access_token },
      body: JSON.stringify(Object.assign({ action: action, origin: location.origin }, payload))
    });
    return r.json();
  }

  async function load() {
    S.ctx = Crew.ctx();
    var r = await Promise.all([
      Crew.sb.from('roles').select('*').eq('is_active', true).order('hierarchy_level'),
      Crew.sb.from('profiles').select('*').order('full_name'),
      Crew.sb.from('user_roles').select('user_id, role_id'),
      Crew.sb.from('user_restaurants').select('user_id, restaurant_id'),
      Crew.sb.from('restaurants').select('*').order('name')
    ]);
    S.roles = r[0].data || [];
    S.restaurants = r[4].data || [];
    var roleOf = {}; (r[2].data || []).forEach(function (x) { roleOf[x.user_id] = x.role_id; });
    var restOf = {}; (r[3].data || []).forEach(function (x) {
      (restOf[x.user_id] = restOf[x.user_id] || []).push(x.restaurant_id); });
    S.users = (r[1].data || []).map(function (u) {
      u.role_id = roleOf[u.id];
      u.role = S.roles.filter(function (x) { return x.id === u.role_id; })[0];
      u.restaurant_ids = restOf[u.id] || [];
      return u;
    });
  }

  function mayAssign(role) {
    return Crew.can('users.assign_role') && role.hierarchy_level > S.ctx.level;
  }
  function mayTouch(u) {
    if (u.is_system_owner) return false;
    var lvl = u.role ? u.role.hierarchy_level : 9999;
    return Crew.can('users.edit') && lvl > S.ctx.level;
  }

  function card(u) {
    var locked = !mayTouch(u);
    return '<article class="ucard' + (locked ? ' is-locked' : '') + '"' +
      (locked ? '' : ' draggable="true"') + ' data-uid="' + u.id + '" tabindex="0">' +
      '<span class="ucard__av" style="background:' + ((u.role && u.role.color) || '#7A7F8C') + '">' +
        esc(initials(u.full_name, u.email)) + '</span>' +
      '<div class="ucard__b">' +
        '<b>' + esc(u.full_name || u.email.split('@')[0]) + '</b>' +
        '<span>' + esc(u.email) + '</span>' +
        '<div class="ucard__tags">' +
          (u.is_system_owner ? '<span class="badge badge--own">owner</span>' : '') +
          '<span class="badge ' + (u.is_active ? 'badge--ok' : 'badge--off') + '">' +
            (u.is_active ? 'active' : 'disabled') + '</span>' +
          '<span class="ucard__br">' + esc(
            u.restaurant_ids.length === S.restaurants.length && S.restaurants.length
              ? 'both branches'
              : (u.restaurant_ids.length
                  ? S.restaurants.filter(function (r) { return u.restaurant_ids.indexOf(r.id) > -1; })
                      .map(function (r) { return r.name; }).join(' + ')
                  : 'no branch')) + '</span>' +
        '</div>' +
      '</div></article>';
  }

  /* Staff are grouped by branch first, then by role. Someone assigned to both
     appears under each, because that is genuinely true of them. */
  var branchFilter = null;   // null = show the branch picker

  function boardFor(users, keySuffix) {
    return S.roles.map(function (r) {
      var mine = users.filter(function (u) { return u.role_id === r.id; });
      var drop = mayAssign(r);
      return '<section class="ucol' + (drop ? '' : ' is-nodrop') + '" data-role="' + r.id + '">' +
        '<header><span class="ucol__dot" style="background:' + (r.color||'#999') + '"></span>' +
          '<b>' + esc(r.name) + '</b><i>' + mine.length + '</i>' +
          (drop ? '' : '<span class="ucol__lock" title="At or above your authority">&#9679;</span>') +
        '</header><div class="ucol__body">' +
        (mine.map(card).join('') || '<p class="ucol__empty">Nobody yet</p>') +
        '</div></section>';
    }).join('');
  }

  function render() {
    var host = d.getElementById('u-board');
    var tabs = d.getElementById('u-branchtabs');
    var back = d.getElementById('u-back');

    /* No combined board. A branch is chosen first, then its people are shown —
       one horizontally-scrolling set of role columns instead of several stacked
       ones, which is what made the old view feel endless. */
    if (!branchFilter) {
      if (tabs) tabs.innerHTML = '';
      if (back) back.hidden = true;
      var groups = S.restaurants.map(function (r) {
        return { id: r.id, name: r.name,
                 users: S.users.filter(function (u) { return u.restaurant_ids.indexOf(r.id) > -1; }) };
      });
      var un = S.users.filter(function (u) { return !u.restaurant_ids.length; });
      if (un.length) groups.push({ id: 'none', name: 'Not assigned to a branch', users: un });

      host.innerHTML = '<div class="upick">' + groups.map(function (g) {
        var byRole = S.roles.map(function (r) {
          var n = g.users.filter(function (u) { return u.role_id === r.id; }).length;
          return n ? '<span><em>' + n + '</em>' + esc(r.name) + '</span>' : '';
        }).join('');
        return '<button class="upick__c" data-bf="' + g.id + '">' +
          '<h2>' + esc(g.name) + '</h2>' +
          '<b>' + g.users.length + '</b><span class="upick__l">staff</span>' +
          '<div class="upick__b">' + (byRole || '<span><em>0</em>nobody yet</span>') + '</div>' +
        '</button>';
      }).join('') + '</div>';
      host.querySelectorAll('[data-bf]').forEach(function (b) {
        b.onclick = function () { branchFilter = b.dataset.bf; render(); }; });
      return;
    }

    var users = branchFilter === 'none'
      ? S.users.filter(function (u) { return !u.restaurant_ids.length; })
      : S.users.filter(function (u) { return u.restaurant_ids.indexOf(branchFilter) > -1; });
    var name = branchFilter === 'none' ? 'Not assigned to a branch'
      : (S.restaurants.filter(function (r) { return r.id === branchFilter; })[0] || {}).name || '';

    if (back) { back.hidden = false; back.onclick = function () { branchFilter = null; render(); }; }
    if (tabs) {
      tabs.innerHTML = S.restaurants.map(function (r) {
        var n = S.users.filter(function (u) { return u.restaurant_ids.indexOf(r.id) > -1; }).length;
        return '<button class="bk-tab' + (branchFilter === r.id ? ' is-on' : '') +
          '" data-bf="' + r.id + '">' + esc(r.name) + ' <i>' + n + '</i></button>'; }).join('') +
        (S.users.some(function (u) { return !u.restaurant_ids.length; })
          ? '<button class="bk-tab' + (branchFilter === 'none' ? ' is-on' : '') +
            '" data-bf="none">Unassigned</button>' : '');
      tabs.querySelectorAll('[data-bf]').forEach(function (b) {
        b.onclick = function () { branchFilter = b.dataset.bf; render(); }; });
    }

    var t = d.getElementById('u-title');
    if (t) t.textContent = name;

    host.innerHTML =
      '<div class="ubranch__b" id="u-scroll">' + S.roles.map(function (r) {
        var mine = users.filter(function (u) { return u.role_id === r.id; });
        var drop = mayAssign(r);
        return '<section class="ucol' + (drop ? '' : ' is-nodrop') + '" data-role="' + r.id + '">' +
          '<header><span class="ucol__dot" style="background:' + (r.color||'#999') + '"></span>' +
            '<b>' + esc(r.name) + '</b><i>' + mine.length + '</i>' +
            (drop ? '' : '<span class="ucol__lock" title="At or above your authority">&#9679;</span>') +
          '</header><div class="ucol__body">' +
          (mine.map(card).join('') || '<p class="ucol__empty">Nobody yet</p>') +
          '</div></section>';
      }).join('') + '</div>' +
      '<div class="scrollcue" id="u-cue"><span>Scroll for more roles &rarr;</span></div>';

    /* only advertise the scroll when there is actually more to see */
    var sc = d.getElementById('u-scroll'), cue = d.getElementById('u-cue');
    function cueState() {
      var more = sc.scrollWidth - sc.clientWidth - sc.scrollLeft > 12;
      cue.classList.toggle('is-on', more);
    }
    sc.addEventListener('scroll', cueState, { passive: true });
    setTimeout(cueState, 60);
    wire();
  }

  var dragging = null;
  function wire() {
    d.querySelectorAll('.ucard').forEach(function (el) {
      el.addEventListener('click', function () { openProfile(el.dataset.uid); });
      el.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openProfile(el.dataset.uid); } });
      if (!el.draggable) return;
      el.addEventListener('dragstart', function (e) {
        dragging = el.dataset.uid; el.classList.add('is-drag');
        e.dataTransfer.effectAllowed = 'move'; });
      el.addEventListener('dragend', function () {
        el.classList.remove('is-drag'); dragging = null;
        d.querySelectorAll('.ucol').forEach(function (c) { c.classList.remove('is-over'); }); });
    });
    d.querySelectorAll('.ucol:not(.is-nodrop)').forEach(function (col) {
      col.addEventListener('dragover', function (e) { e.preventDefault(); col.classList.add('is-over'); });
      col.addEventListener('dragleave', function () { col.classList.remove('is-over'); });
      col.addEventListener('drop', async function (e) {
        e.preventDefault(); col.classList.remove('is-over');
        if (!dragging) return;
        var uid = dragging;
        var u = S.users.filter(function (x) { return x.id === uid; })[0];
        var role = S.roles.filter(function (x) { return x.id === col.dataset.role; })[0];
        if (!u || !role || u.role_id === role.id) return;
        if (!confirm('Move ' + (u.full_name || u.email) + ' to ' + role.name + '?')) return;
        var r = await fn('set_role', { user_id: uid, role_id: role.id });
        if (r.error) { alert(r.error); return; }
        await load(); render();
      });
    });
  }

  async function openProfile(uid) {
    var u = S.users.filter(function (x) { return x.id === uid; })[0]; if (!u) return;
    var may = mayTouch(u);
    var restNames = u.restaurant_ids.map(function (id) {
      return (S.restaurants.filter(function (r) { return r.id === id; })[0]||{}).name; })
      .filter(Boolean).join(', ');
    var roleOpts = S.roles.filter(mayAssign).map(function (r) {
      return '<option value="' + r.id + '"' + (r.id === u.role_id ? ' selected' : '') + '>' +
             esc(r.name) + '</option>'; }).join('');

    d.getElementById('u-drawer').innerHTML =
      '<div class="udrawer__veil" data-x></div><aside class="udrawer__p" role="dialog" aria-modal="true">' +
      '<header><h2>Staff profile</h2><button type="button" data-x aria-label="Close">&times;</button></header>' +
      '<div class="udrawer__b">' +
        '<div class="uprof"><span class="uprof__av" style="background:' +
          ((u.role&&u.role.color)||'#7A7F8C') + '">' + esc(initials(u.full_name,u.email)) + '</span>' +
          '<div><b>' + esc(u.full_name || '—') + '</b><span>' + esc(u.email) + '</span>' +
          '<div class="ucard__tags" style="margin-top:6px">' +
          (u.is_system_owner?'<span class="badge badge--own">system owner</span>':'') +
          '<span class="badge ' + (u.is_active?'badge--ok':'badge--off') + '">' +
          (u.is_active?'active':'disabled') + '</span></div></div></div>' +
        '<dl class="ukv">' +
          '<dt>Role</dt><dd>' + esc((u.role||{}).name || 'none') + '</dd>' +
          '<dt>Branches</dt><dd>' + (esc(restNames) || 'none') + '</dd>' +
          '<dt>Created</dt><dd>' + new Date(u.created_at).toLocaleDateString('en-GB',
            {day:'numeric',month:'short',year:'numeric'}) + '</dd>' +
          '<dt>Last login</dt><dd>' + (u.last_login_at
            ? new Date(u.last_login_at).toLocaleString('en-GB',
                {day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})
            : 'never') + '</dd>' +
        '</dl>' +
        (may ?
          '<hr class="hair">' +
          '<label class="fld"><span>Role</span><select id="up-role">' + roleOpts + '</select></label>' +
          '<label class="fld"><span>Set a new password</span>' +
            '<input id="up-pass" type="text" placeholder="At least 10 characters"></label>' +
          '<div class="fld"><span>Branches</span><div class="brpick">' +
            S.restaurants.map(function (r) {
              return '<label class="chipbox"><input type="checkbox" value="' + r.id + '"' +
                (u.restaurant_ids.indexOf(r.id) > -1 ? ' checked' : '') +
                ' data-br><span>' + esc(r.name) + '</span></label>'; }).join('') +
          '</div></div>' +
          '<div style="display:flex;gap:9px;flex-wrap:wrap;margin-top:4px;">' +
            '<button class="btn btn--wine btn--sm" type="button" id="up-save">Save changes</button>' +
            '<button class="btn btn--ghost btn--sm" type="button" id="up-toggle">' +
              (u.is_active ? 'Disable account' : 'Reactivate') + '</button></div>'
        : '<p class="crew-note" style="text-align:left;margin-top:10px">' +
          (u.is_system_owner
            ? 'This is a system owner account. It cannot be edited, disabled or removed &mdash; by anyone, including another owner.'
            : 'This person is at or above your own authority, so you cannot change their account.') +
          '</p>') +
      '</div></aside>';

    var dr = d.getElementById('u-drawer'); dr.classList.add('is-open');
    dr.querySelectorAll('[data-x]').forEach(function (b) {
      b.onclick = function () { dr.classList.remove('is-open'); }; });

    if (!may) return;
    d.getElementById('up-save').onclick = async function () {
      var role = d.getElementById('up-role').value, pass = d.getElementById('up-pass').value;
      if (role && role !== u.role_id) {
        var a = await fn('set_role', { user_id: u.id, role_id: role });
        if (a.error) return alert(a.error);
      }
      if (pass) {
        var b = await fn('set_password', { user_id: u.id, password: pass });
        if (b.error) return alert(b.error);
      }
      var want = [].slice.call(dr.querySelectorAll('[data-br]:checked'))
                   .map(function (x) { return x.value; });
      var have = u.restaurant_ids.slice();
      var add = want.filter(function (x) { return have.indexOf(x) === -1; });
      var rm  = have.filter(function (x) { return want.indexOf(x) === -1; });
      if (add.length) {
        var ai = await Crew.sb.from('user_restaurants').insert(
          add.map(function (r) { return { user_id: u.id, restaurant_id: r }; }));
        if (ai.error) return alert(ai.error.message);
      }
      if (rm.length) {
        var ri = await Crew.sb.from('user_restaurants').delete()
          .eq('user_id', u.id).in('restaurant_id', rm);
        if (ri.error) return alert(ri.error.message);
      }
      if (add.length || rm.length) {
        await Crew.sb.from('audit_logs').insert({
          actor_id: S.ctx.user.id, actor_email: S.ctx.profile.email,
          action: 'user.branches_changed', resource: 'profiles', resource_id: u.id,
          before: { branches: have }, after: { branches: want } });
      }
      dr.classList.remove('is-open'); await load(); render();
    };
    d.getElementById('up-toggle').onclick = async function () {
      var next = !u.is_active;
      if (!confirm((next ? 'Reactivate ' : 'Disable ') + (u.full_name||u.email) + '?')) return;
      var r = await fn('set_active', { user_id: u.id, is_active: next });
      if (r.error) return alert(r.error);
      dr.classList.remove('is-open'); await load(); render();
    };
  }

  w.CrewUsers = { load: load, render: render, state: S, fn: fn, mayAssign: mayAssign };
})(window, document);
