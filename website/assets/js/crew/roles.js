/* Roles: pyramid visualisation + creation wizard. Superadmin only.
   The pyramid is built from whatever roles exist — it never assumes five. */
(function (w, d) {
  'use strict';
  var S = { roles: [], perms: [], counts: {} };
  var PAGE_KEYS = ['dashboard','orders','new-order','quick-notes','kitchen','monitor',
                   'history','menu','users','roles','restaurants','reports','audit','settings'];
  var esc = function (s) { return String(s==null?'':s).replace(/[&<>"']/g, function (c) {
    return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]; }); };

  async function load() {
    var r = await Promise.all([
      Crew.sb.from('roles').select('*').order('hierarchy_level'),
      Crew.sb.from('permissions').select('*').order('resource'),
      Crew.sb.from('user_roles').select('role_id')
    ]);
    S.roles = r[0].data || [];
    S.perms = r[1].data || [];
    S.counts = {};
    (r[2].data || []).forEach(function (x) { S.counts[x.role_id] = (S.counts[x.role_id]||0)+1; });
  }

  /* group roles by level so the pyramid widens naturally */
  function pyramid() {
    var tiers = {};
    S.roles.forEach(function (r) { (tiers[r.hierarchy_level] = tiers[r.hierarchy_level] || []).push(r); });
    var levels = Object.keys(tiers).map(Number).sort(function (a,b) { return a-b; });
    return '<div class="pyr">' + levels.map(function (lv, i) {
      var row = tiers[lv];
      return '<div class="pyr__tier" style="--w:' + Math.min(100, 34 + i*17) + '%">' +
        row.map(function (r) {
          return '<div class="pyr__node" style="--c:' + (r.color||'#7A7F8C') + '" data-role="' + r.id + '">' +
            '<b>' + esc(r.name) + '</b>' +
            '<span>level ' + r.hierarchy_level + ' · ' + (S.counts[r.id]||0) + ' staff</span>' +
            (r.is_system ? '<i class="pyr__sys">system</i>' : '') +
          '</div>'; }).join('') +
      '</div>';
    }).join('') + '</div>';
  }

  function table() {
    return '<table class="rtable"><thead><tr><th>Role</th><th>Level</th><th>Staff</th>' +
      '<th>Permissions</th><th>Pages</th><th></th></tr></thead><tbody>' +
      S.roles.map(function (r) {
        return '<tr data-role="' + r.id + '">' +
          '<td><span class="rdot" style="background:' + (r.color||'#999') + '"></span>' +
            esc(r.name) + (r.is_system ? ' <i class="rsys">system</i>' : '') +
            '<br><small>' + esc(r.description||'') + '</small></td>' +
          '<td class="num">' + r.hierarchy_level + '</td>' +
          '<td class="num">' + (S.counts[r.id]||0) + '</td>' +
          '<td class="num" data-perms="' + r.id + '">…</td>' +
          '<td class="num" data-pages="' + r.id + '">…</td>' +
          '<td>' + (r.is_system ? '<span class="rlock">protected</span>' : '') + '</td>' +
        '</tr>'; }).join('') + '</tbody></table>';
  }

  async function counts() {
    var a = await Crew.sb.from('role_permissions').select('role_id');
    var b = await Crew.sb.from('role_pages').select('role_id');
    var pc = {}, gc = {};
    (a.data||[]).forEach(function (x) { pc[x.role_id]=(pc[x.role_id]||0)+1; });
    (b.data||[]).forEach(function (x) { gc[x.role_id]=(gc[x.role_id]||0)+1; });
    d.querySelectorAll('[data-perms]').forEach(function (el) {
      el.textContent = pc[el.dataset.perms] || 0; });
    d.querySelectorAll('[data-pages]').forEach(function (el) {
      el.textContent = gc[el.dataset.pages] || 0; });
  }

  function render() {
    d.getElementById('r-pyramid').innerHTML = pyramid();
    d.getElementById('r-table').innerHTML = table();
    counts();
  }

  /* ---------------------------------------------- creation wizard */
  function wizard(ctx) {
    var host = d.getElementById('r-wizard'), step = 0;
    var STEPS = ['Identity','Hierarchy','Pages','Permissions','Restrictions','Review'];
    var data = { name:'', description:'', color:'#B68052', hierarchy_level:25,
                 pages:[], perms:[], restaurants:'all' };

    function levelPreview() {
      var all = S.roles.map(function (r) {
        return { name:r.name, lv:r.hierarchy_level, ghost:false }; });
      all.push({ name: data.name || 'New role', lv: data.hierarchy_level, ghost:true });
      all.sort(function (a,b) { return a.lv-b.lv; });
      return '<div class="lvlist">' + all.map(function (r) {
        return '<div class="lvrow' + (r.ghost?' is-ghost':'') + '">' +
          '<span class="num">' + r.lv + '</span><b>' + esc(r.name) + '</b></div>'; }).join('') + '</div>';
    }

    function body() {
      if (step===0) return '<h3>What is this role called?</h3>' +
        '<label class="fld"><span>Name</span><input id="rw-name" value="'+esc(data.name)+'" placeholder="Host, Barista, Runner…"></label>' +
        '<label class="fld"><span>Description</span><input id="rw-desc" value="'+esc(data.description)+'" placeholder="What this role is responsible for"></label>' +
        '<label class="fld"><span>Colour</span><input id="rw-color" type="color" value="'+data.color+'" style="height:46px"></label>';
      if (step===1) return '<h3>Where does it sit?</h3>' +
        '<p class="hint">Lower number means more authority. It must sit below your own level ('+ctx.level+').</p>' +
        '<label class="fld"><span>Hierarchy level</span>' +
          '<input id="rw-lv" type="number" min="'+(ctx.level+1)+'" max="999" value="'+data.hierarchy_level+'"></label>' +
        levelPreview();
      if (step===2) return '<h3>Which pages can it open?</h3><div class="permwrap">' +
        PAGE_KEYS.map(function (k) {
          return '<label class="chipbox"><input type="checkbox" value="'+k+'"'+
            (data.pages.indexOf(k)>-1?' checked':'')+'><span>'+k+'</span></label>'; }).join('') + '</div>';
      if (step===3) {
        var byRes = {};
        S.perms.forEach(function (p) { (byRes[p.resource]=byRes[p.resource]||[]).push(p); });
        return '<h3>What can it do?</h3><div class="permwrap" style="max-height:230px">' +
          Object.keys(byRes).map(function (res) {
            return '<div class="permgrp"><b>'+res+'</b>' + byRes[res].map(function (p) {
              return '<label class="chipbox"><input type="checkbox" value="'+p.key+'"'+
                (data.perms.indexOf(p.key)>-1?' checked':'')+'><span>'+p.action+'</span></label>'; }).join('') +
            '</div>'; }).join('') + '</div>';
      }
      if (step===4) return '<h3>Any restrictions?</h3><div class="pickrow">' +
        '<label class="pick"><input type="radio" name="rw-r" value="all"'+(data.restaurants==='all'?' checked':'')+
          '><span><b>Both branches</b><span>Assigned per person when you create them</span></span></label>' +
        '<label class="pick"><input type="radio" name="rw-r" value="one"'+(data.restaurants==='one'?' checked':'')+
          '><span><b>Single branch only</b><span>People in this role work one location</span></span></label></div>';
      return '<h3>Ready to create</h3><dl class="ukv">' +
        '<dt>Name</dt><dd>'+esc(data.name)+'</dd>' +
        '<dt>Level</dt><dd>'+data.hierarchy_level+'</dd>' +
        '<dt>Pages</dt><dd>'+(data.pages.join(', ')||'none')+'</dd>' +
        '<dt>Permissions</dt><dd>'+data.perms.length+' granted</dd>' +
        '<dt>Branches</dt><dd>'+(data.restaurants==='all'?'both':'single')+'</dd></dl>';
    }

    function draw() {
      host.innerHTML = '<div class="udrawer__veil" data-x></div><div class="wiz" role="dialog" aria-modal="true">' +
        '<div class="wiz__steps">' + STEPS.map(function (s,i) {
          return '<span class="'+(i===step?'is-on':(i<step?'is-done':''))+'">'+(i+1)+'. '+s+'</span>'; }).join('') + '</div>' +
        '<div class="wiz__body">' + body() + '</div>' +
        '<div class="wiz__foot">' +
          '<button class="btn btn--ghost btn--sm" type="button" id="rw-back">'+(step===0?'Cancel':'Back')+'</button>' +
          '<button class="btn btn--wine btn--sm" type="button" id="rw-next">'+(step===5?'Create role':'Continue')+'</button>' +
        '</div></div>';
      host.classList.add('is-open');
      host.querySelectorAll('[data-x]').forEach(function (b) { b.onclick = close; });

      if (step===1) d.getElementById('rw-lv').oninput = function () {
        data.hierarchy_level = +this.value || 0;
        host.querySelector('.lvlist').outerHTML = levelPreview(); };
      if (step===2) host.querySelectorAll('.chipbox input').forEach(function (cb) {
        cb.onchange = function () { data.pages = [].slice.call(
          host.querySelectorAll('.chipbox input:checked')).map(function (x){return x.value;}); }; });
      if (step===3) host.querySelectorAll('.chipbox input').forEach(function (cb) {
        cb.onchange = function () { data.perms = [].slice.call(
          host.querySelectorAll('.chipbox input:checked')).map(function (x){return x.value;}); }; });
      if (step===4) host.querySelectorAll('[name=rw-r]').forEach(function (r) {
        r.onchange = function () { data.restaurants = r.value; }; });

      d.getElementById('rw-back').onclick = function () { if (step===0) return close(); step--; draw(); };
      d.getElementById('rw-next').onclick = async function () {
        if (step===0) {
          data.name = (d.getElementById('rw-name').value||'').trim();
          data.description = (d.getElementById('rw-desc').value||'').trim();
          data.color = d.getElementById('rw-color').value;
          if (!data.name) return alert('Give the role a name.');
        }
        if (step===1 && data.hierarchy_level <= ctx.level)
          return alert('The new role must sit below your own authority (level ' + ctx.level + ').');
        if (step<5) { step++; draw(); return; }

        var btn = d.getElementById('rw-next'); btn.disabled = true; btn.textContent='Creating…';
        var key = data.name.toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_|_$/g,'');
        var ins = await Crew.sb.from('roles').insert({
          key:key, name:data.name, description:data.description, color:data.color,
          hierarchy_level:data.hierarchy_level, is_system:false, created_by:ctx.user.id
        }).select().single();
        if (ins.error) { btn.disabled=false; btn.textContent='Create role'; return alert(ins.error.message); }
        var rid = ins.data.id;
        if (data.pages.length) await Crew.sb.from('role_pages').insert(
          data.pages.map(function (p,i) { return { role_id:rid, page_key:p, sort_order:i }; }));
        if (data.perms.length) {
          var ids = S.perms.filter(function (p) { return data.perms.indexOf(p.key)>-1; })
                           .map(function (p) { return { role_id:rid, permission_id:p.id }; });
          await Crew.sb.from('role_permissions').insert(ids);
        }
        await Crew.sb.from('audit_logs').insert({
          actor_id: ctx.user.id, actor_email: ctx.profile.email, action:'role.created',
          resource:'roles', resource_id:rid, after:{name:data.name, level:data.hierarchy_level}});
        close(); await load(); render();
      };
    }
    function close(){ host.classList.remove('is-open'); host.innerHTML=''; }
    draw();
  }

  w.CrewRoles = { load:load, render:render, wizard:wizard };
})(window, document);
