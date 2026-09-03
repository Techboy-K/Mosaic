# -*- coding: utf-8 -*-
import importlib.util as u
s=u.spec_from_file_location('b','build-crew.py'); B=u.module_from_spec(s); s.loader.exec_module(B)

ORDER_JS = '<script src="../assets/js/crew/orders.js"></script>'

# ─────────────────────────────────────────────── login
B.page('index.html', 'Crew sign in — Mosaic', """
<div class="crew-login">
  <form class="crew-login__card" id="login-form" autocomplete="on">
    <div class="crew-login__logo">
      <img src="../assets/img/brand/logo.webp" alt="">
      <b>MOSAIC</b><span>Crew portal</span>
    </div>
    <div class="crew-err" id="login-err" hidden></div>
    <label class="fld"><span>Email</span>
      <input id="login-email" type="email" autocomplete="username" required
             placeholder="you@gmail.com" inputmode="email"></label>
    <label class="fld"><span>Password</span>
      <input id="login-pass" type="password" autocomplete="current-password" required
             placeholder="••••••••••"></label>
    <button class="btn btn--wine" type="submit" id="login-go" style="width:100%">Sign in</button>
    <button class="btn btn--ghost" type="button" id="login-reset" style="width:100%">
      Forgot password</button>
    <p class="crew-note">Staff access only. Every action in this portal is recorded
       against your account.</p>
  </form>
</div>
""", scripts="""<script>
(function(){
  var f=document.getElementById('login-form'), err=document.getElementById('login-err'),
      go=document.getElementById('login-go');
  function fail(m){ err.textContent=m; err.hidden=false; }

  Crew.load().then(function(c){ if(c) location.replace(Crew.homeFor(c)); });

  f.addEventListener('submit', async function(e){
    e.preventDefault(); err.hidden=true;
    go.disabled=true; go.textContent='Signing in…';
    var r = await Crew.signIn(document.getElementById('login-email').value.trim(),
                              document.getElementById('login-pass').value);
    if(!r.ok){
      go.disabled=false; go.textContent='Sign in';
      /* deliberately vague: never confirm whether an address exists */
      fail(/Invalid/i.test(r.message) ? 'That email and password do not match.' : r.message);
      return;
    }
    var next=new URLSearchParams(location.search).get('next');
    location.replace(next && /^[a-z0-9-]+\\.html$/.test(next) ? '/crew/'+next : Crew.homeFor(r.ctx));
  });

  document.getElementById('login-reset').addEventListener('click', async function(){
    var em=document.getElementById('login-email').value.trim();
    if(!em){ fail('Enter your email first, then press Forgot password.'); return; }
    await Crew.sb.auth.resetPasswordForEmail(em,{redirectTo:location.origin+'/crew/reset.html'});
    err.textContent='If that address has an account, a reset link is on its way.';
    err.hidden=false;
  });
})();
</script>""")

# ─────────────────────────────────────────────── permission denied
B.page('denied.html', 'No access — Mosaic Crew', """
<div id="crew-shell"></div>
<main><div class="crew-deny"><div>
  <h1 style="font-size:26px;">You don&rsquo;t have access to that page</h1>
  <p style="color:var(--muted);font-size:14px;">Your role doesn&rsquo;t include it.
     If you think that&rsquo;s wrong, ask a supervisor or an admin.</p>
  <a class="btn btn--wine" href="/crew/index.html" id="deny-home">Back to your pages</a>
</div></div></main>
""", scripts="""<script>(async function(){
  var c=await Crew.load();
  if(c){ CrewShell.render(c); document.getElementById('deny-home').href=Crew.homeFor(c); }
})();</script>""")

# ─────────────────────────────────────────────── dashboard
B.shell_page('dashboard.html','Dashboard — Mosaic Crew','dashboard', """
  <header class="dh">
    <div><h1 id="dash-hi">Dashboard</h1><p id="dash-sub"></p></div>
    <div class="dh__right"><span id="dash-clock"></span><span id="dash-day"></span></div>
  </header>

  <div id="dash-alerts"></div>

  <div class="dgrid">
    <section class="dcard dcard--wide">
      <div class="dcard__h"><h2>Service right now</h2><a href="/crew/monitor.html">Open monitor &rarr;</a></div>
      <div id="dash-branches" class="dbranches"></div>
    </section>

    <section class="dcard">
      <div class="dcard__h"><h2>Today</h2></div>
      <div id="dash-today" class="dstats"></div>
    </section>

    <section class="dcard">
      <div class="dcard__h"><h2>On shift</h2><a href="/crew/users.html">Staff &rarr;</a></div>
      <div id="dash-team" class="dteam"></div>
    </section>

    <section class="dcard dcard--wide">
      <div class="dcard__h"><h2>Recent activity</h2><a href="/crew/audit.html">Full log &rarr;</a></div>
      <div id="dash-feed" class="dfeed"></div>
    </section>
  </div>

  <h2 class="dsec">Everything you can open</h2>
  <div class="dash-links" id="dash-links"></div>
""", scripts=ORDER_JS + """<script>
window.pageInit = async function(c){
  var defs = await CrewOrders.statusDefs();
  var h=new Date().getHours();
  document.getElementById('dash-hi').textContent =
    (h<12?'Good morning':h<18?'Good afternoon':'Good evening')+', '+
    ((c.profile.full_name||'').split(' ')[0] || 'there');
  document.getElementById('dash-sub').textContent =
    c.roles.map(function(r){return r.name;}).join(' · ')+' · '+
    (c.restaurants.length>1?'both branches':(c.restaurants[0]?c.restaurants[0].name:'no branch'));
  function clock(){
    var n=new Date();
    document.getElementById('dash-clock').textContent=n.toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'});
    document.getElementById('dash-day').textContent=n.toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long'});
  }
  clock(); setInterval(clock,20000);

  /* stroke icons on a 24px grid, one visual family — no emoji */
  var IC={
    orders:'<path d="M4 5h16v14H4z"/><path d="M8 9h8"/><path d="M8 13h5"/>',
    'new-order':'<circle cx="12" cy="12" r="8.5"/><path d="M12 8v8"/><path d="M8 12h8"/>',
    'quick-notes':'<path d="M5 3.5h9l5 5v12H5z"/><path d="M14 3.5V9h5"/><path d="M8.5 13h7"/><path d="M8.5 16.5h4"/>',
    kitchen:'<path d="M6 3v7a3 3 0 0 0 6 0V3"/><path d="M9 10v11"/><path d="M17 3c-1.5 2-2 4-2 6.5S16 14 17 14V3Z"/><path d="M17 14v7"/>',
    monitor:'<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/>',
    bookings:'<rect x="3.2" y="5" width="17.6" height="16" rx="2"/><path d="M3.2 10h17.6"/><path d="M8 3v4"/><path d="M16 3v4"/>',
    history:'<path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1"/><path d="M3.5 4.5V9H8"/><path d="M12 7.5V12l3 2"/>',
    menu:'<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h10"/>',
    users:'<circle cx="9" cy="8" r="3.4"/><path d="M2.8 20a6.4 6.4 0 0 1 12.4 0"/><path d="M16.5 5.2a3.4 3.4 0 0 1 0 5.6"/><path d="M18 14.4a6.4 6.4 0 0 1 3.2 5.6"/>',
    roles:'<path d="M12 3.5 21 19H3Z"/><path d="M8 14h8"/>',
    restaurants:'<path d="M3.5 10 12 3.5 20.5 10V20h-17Z"/><path d="M9.5 20v-6h5v6"/>',
    reports:'<path d="M4 20V9"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M21 20H3"/>',
    audit:'<path d="M6 3.5h12v17l-6-3-6 3Z"/><path d="M9.5 9h5"/><path d="M9.5 12.5h5"/>',
    settings:'<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.2 5.2l2.1 2.1M16.7 16.7l2.1 2.1M18.8 5.2l-2.1 2.1M7.3 16.7l-2.1 2.1"/>'
  };
  function icon(k){ return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '+
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'+(IC[k]||'')+'</svg>'; }

  var GROUPS=[['Service',['orders','new-order','quick-notes','kitchen']],
              ['Floor',['monitor','bookings','history']],
              ['Menu',['menu']],['People',['users','roles']],
              ['Business',['restaurants','reports','audit','settings']]];
  var NAMES={orders:'Orders','new-order':'New order','quick-notes':'Quick notes',kitchen:'Kitchen',
    monitor:'Monitor',bookings:'Bookings',history:'History',menu:'Menu',users:'Staff',roles:'Roles',
    restaurants:'Restaurants',reports:'Reports',audit:'Audit log',settings:'Settings'};
  var BLURB={orders:'Your active tables','new-order':'Take an order','quick-notes':'Fast manual capture',
    kitchen:'The pass',monitor:'Every order, live',bookings:'Reservations',history:'Completed orders',
    menu:'Dishes and prices',users:'Who works here',roles:'Permissions and hierarchy',
    restaurants:'Branch details',reports:'Numbers',audit:'Who changed what',settings:'System'};

  document.getElementById('dash-links').innerHTML = GROUPS.map(function(g){
    var items=g[1].filter(function(k){return c.pages.indexOf(k)>-1;});
    if(!items.length) return '';
    return '<div class="dlgroup"><h3>'+g[0]+'</h3><div class="dlrow">'+
      items.map(function(k){
        return '<a class="dtile" href="'+k+'.html">'+
          '<span class="dtile__i">'+icon(k)+'</span>'+
          '<span class="dtile__t"><b>'+NAMES[k]+'</b><i>'+(BLURB[k]||'')+'</i></span>'+
        '</a>'; }).join('')+
    '</div></div>'; }).join('');

  async function refresh(){
    var LIVE=['DRAFT','SUBMITTED','SENT_TO_KITCHEN','IN_PREPARATION','READY','SERVED','NEEDS_ATTENTION'];
    var rows=await CrewOrders.fetchOrders(LIVE);
    var since=new Date(); since.setHours(0,0,0,0);
    var today=((await Crew.sb.from('orders')
      .select('status,priority,created_at,completed_at,restaurant_id')
      .gte('created_at',since.toISOString())).data)||[];

    var urgent=rows.filter(function(o){return o.priority==='URGENT';}).length;
    var late=rows.filter(function(o){return (Date.now()-new Date(o.created_at))/60000>25;}).length;
    var att=rows.filter(function(o){return o.status==='NEEDS_ATTENTION';}).length;
    document.getElementById('dash-alerts').innerHTML = (urgent||late||att)
      ? '<div class="dalerts">'+
        (att?'<a class="dalert dalert--bad" href="/crew/monitor.html"><b>'+att+'</b> need attention</a>':'')+
        (urgent?'<a class="dalert dalert--bad" href="/crew/monitor.html"><b>'+urgent+'</b> urgent</a>':'')+
        (late?'<a class="dalert dalert--warn" href="/crew/monitor.html"><b>'+late+'</b> over 25 minutes</a>':'')+
        '</div>'
      : '<div class="dalerts"><span class="dalert dalert--ok">Everything is on track</span></div>';

    var ids=[]; rows.forEach(function(o){ if(ids.indexOf(o.restaurant_id)===-1) ids.push(o.restaurant_id); });
    (c.restaurants||[]).forEach(function(r){ if(ids.indexOf(r.id)===-1) ids.push(r.id); });
    ids.sort(function(a,b){return CrewOrders.restName(a).localeCompare(CrewOrders.restName(b));});
    document.getElementById('dash-branches').innerHTML = ids.map(function(rid){
      var m=rows.filter(function(o){return o.restaurant_id===rid;});
      var t=today.filter(function(o){return o.restaurant_id===rid;});
      return '<a class="dbranch" href="/crew/monitor.html">'+
        '<div class="dbranch__t"><b>'+CrewOrders.esc(CrewOrders.restName(rid))+'</b>'+
          '<span>'+t.length+' today</span></div>'+
        '<div class="dbranch__n">'+m.length+'<i>live</i></div>'+
        '<div class="dbranch__bar">'+
          ['SUBMITTED','SENT_TO_KITCHEN','IN_PREPARATION','READY'].map(function(k){
            var n=m.filter(function(o){return o.status===k;}).length;
            return '<span'+(n?' class="on"':'')+' style="--c:'+defs[k].colour+'">'+
              '<em>'+n+'</em>'+defs[k].label+'</span>'; }).join('')+
        '</div></a>'; }).join('') || '<p class="crew-empty">No branches assigned.</p>';

    var done=today.filter(function(o){return o.completed_at;});
    var avg=done.length?Math.round(done.reduce(function(s,o){
      return s+(new Date(o.completed_at)-new Date(o.created_at))/60000;},0)/done.length):0;
    document.getElementById('dash-today').innerHTML=
      [['Orders taken',today.length],['Completed',done.length],
       ['Still live',rows.length],['Avg minutes',avg||'—']]
      .map(function(x){return '<div class="dstat"><b>'+x[1]+'</b><span>'+x[0]+'</span></div>';}).join('');
  }

  async function team(){
    var el=document.getElementById('dash-team');
    if(!Crew.can('users.view')){ el.innerHTML='<p class="crew-empty">Not visible to your role.</p>'; return; }
    var p=(await Crew.sb.from('profiles')
      .select('id,full_name,email,avatar_path,is_active,last_login_at')).data||[];
    var ur=(await Crew.sb.from('user_roles').select('user_id, roles(name,color,hierarchy_level)')).data||[];
    var rm={}; ur.forEach(function(x){rm[x.user_id]=x.roles;});
    var list=p.filter(function(u){return u.is_active;})
      .sort(function(a,b){return ((rm[a.id]||{}).hierarchy_level||999)-((rm[b.id]||{}).hierarchy_level||999);})
      .slice(0,8);
    el.innerHTML=list.map(function(u){
      var r=rm[u.id]||{name:'—',color:'#7A7F8C'};
      var on=u.last_login_at && (Date.now()-new Date(u.last_login_at))<8*3600*1000;
      return '<a class="dteam__r" href="/crew/users.html">'+
        (u.avatar_path?'<img src="'+u.avatar_path+'" alt="">'
          :'<span class="dteam__av" style="background:'+r.color+'">'+
            (u.full_name||u.email).slice(0,1).toUpperCase()+'</span>')+
        '<span class="dteam__n"><b>'+CrewOrders.esc((u.full_name||u.email.split('@')[0]))+'</b>'+
        '<i>'+CrewOrders.esc(r.name)+'</i></span>'+
        '<span class="dteam__d'+(on?' is-on':'')+'"></span></a>'; }).join('')
      || '<p class="crew-empty">No active staff.</p>';
  }

  async function feed(){
    var el=document.getElementById('dash-feed');
    if(!Crew.can('audit.view')){ el.innerHTML='<p class="crew-empty">Not visible to your role.</p>'; return; }
    var a=(await Crew.sb.from('audit_logs').select('*')
      .order('created_at',{ascending:false}).limit(6)).data||[];
    el.innerHTML=a.length? a.map(function(x){
      return '<div class="dfeed__r"><span class="dfeed__a">'+
        CrewOrders.esc((x.actor_email||'system').split('@')[0])+'</span>'+
        '<code>'+x.action+'</code>'+
        '<time>'+new Date(x.created_at).toLocaleTimeString('en-GB',
          {hour:'2-digit',minute:'2-digit'})+'</time></div>'; }).join('')
      : '<p class="crew-empty">Nothing logged yet.</p>';
  }

  await refresh(); team(); feed();
  CrewOrders.watch(refresh);
  setInterval(refresh,45000);
};
</script>""")

# ─────────────────────────────────────────────── staff (kanban + wizard)
B.shell_page('users.html','Staff — Mosaic Crew','users', """
  <div class="crew-title">
    <div><h1 id="u-title">Staff</h1><p>Pick a branch to see who works there.
      Drag a card to change someone&rsquo;s role &mdash; the server checks your authority regardless.</p></div>
    <div style="display:flex;gap:9px;">
      <button class="btn btn--ghost btn--sm" type="button" id="u-back" hidden>All branches</button>
      <button class="btn btn--wine btn--sm" type="button" id="u-new">Add staff</button>
    </div>
  </div>
  <div class="bk-tabs" id="u-branchtabs"></div>
  <div id="u-board"></div>
  <div id="u-drawer"></div>
  <div id="u-wizard"></div>
""", scripts="""<script src="../assets/js/crew/upload.js"></script>\n<script src="../assets/js/crew/users.js"></script>
<script>
window.pageInit = async function(c){
  await CrewUsers.load(); CrewUsers.render();
  var btn = document.getElementById('u-new');
  if (!Crew.can('users.create')) { btn.hidden = true; return; }
  btn.onclick = function(){ openWizard(c); };

  function openWizard(ctx){
    var S = CrewUsers.state;
    var assignable = S.roles.filter(CrewUsers.mayAssign);
    if (!assignable.length){ alert('There are no roles below your authority to assign.'); return; }
    var step = 0, data = { mode:'invite', restaurant_ids: [], role_id: assignable[0].id };
    var STEPS = ['Person','Role','Branches','Access','Sign-in','Review'];
    var host = document.getElementById('u-wizard');

    function pw(){ var a='ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%';
      return Array.from(crypto.getRandomValues(new Uint32Array(16)))
        .map(function(n){return a[n%a.length];}).join(''); }

    function body(){
      var role = S.roles.filter(function(r){return r.id===data.role_id;})[0]||{};
      if (step===0) return '<h3>Who is this?</h3>'+
        '<label class="fld"><span>Full name</span><input id="w-name" value="'+(data.full_name||'')+'" placeholder="Rania Haddad"></label>'+
        '<label class="fld"><span>Email</span><input id="w-email" type="email" value="'+(data.email||'')+'" placeholder="name@gmail.com"></label>'+
        '<p class="hint">A Gmail address works well for invites. Kitchen staff without email can be given a temporary password at step 5.</p>';
      if (step===1) return '<h3>What do they do?</h3>'+
        '<p class="hint">Only roles below your own authority are listed.</p><div class="pickrow">'+
        assignable.map(function(r){ return '<label class="pick"><input type="radio" name="w-role" value="'+r.id+'"'+
          (r.id===data.role_id?' checked':'')+'><span style="flex:1"><b>'+r.name+'</b><span>'+
          (r.description||'')+'</span></span></label>'; }).join('')+'</div>';
      if (step===2) return '<h3>Which branches?</h3><div class="pickrow">'+
        S.restaurants.map(function(r){ return '<label class="pick"><input type="checkbox" value="'+r.id+'"'+
          (data.restaurant_ids.indexOf(r.id)>-1?' checked':'')+'><span><b>'+r.name+'</b></span></label>';
        }).join('')+'</div>';
      if (step===3) return '<h3>What they&rsquo;ll be able to do</h3>'+
        '<p class="hint">Granted by the <b>'+role.name+'</b> role and enforced in the database.</p>'+
        '<div class="permwrap" id="w-perms">Loading&hellip;</div>';
      if (step===4) return '<h3>How do they sign in?</h3><div class="pickrow">'+
        '<label class="pick"><input type="radio" name="w-mode" value="invite"'+(data.mode==='invite'?' checked':'')+
          '><span><b>Email them an invite</b><span>They set their own password. Recommended.</span></span></label>'+
        '<label class="pick"><input type="radio" name="w-mode" value="temp"'+(data.mode==='temp'?' checked':'')+
          '><span><b>Temporary password</b><span>For staff without email. They must change it on first login.</span></span></label>'+
        '</div>'+(data.mode==='temp'
          ? '<label class="fld"><span>Temporary password</span><input id="w-pass" value="'+(data.password||pw())+'"></label>'
          : '');
      var rn = S.restaurants.filter(function(r){return data.restaurant_ids.indexOf(r.id)>-1;})
                 .map(function(r){return r.name;}).join(', ') || 'none';
      return '<h3>Ready to create</h3><dl class="ukv">'+
        '<dt>Name</dt><dd>'+(data.full_name||'—')+'</dd>'+
        '<dt>Email</dt><dd>'+(data.email||'—')+'</dd>'+
        '<dt>Role</dt><dd>'+role.name+'</dd>'+
        '<dt>Branches</dt><dd>'+rn+'</dd>'+
        '<dt>Sign-in</dt><dd>'+(data.mode==='invite'?'Emailed invite':'Temporary password')+'</dd></dl>';
    }

    function draw(){
      host.innerHTML='<div class="udrawer__veil" data-x></div><div class="wiz" role="dialog" aria-modal="true">'+
        '<div class="wiz__steps">'+STEPS.map(function(s,i){
          return '<span class="'+(i===step?'is-on':(i<step?'is-done':''))+'">'+(i+1)+'. '+s+'</span>';}).join('')+'</div>'+
        '<div class="wiz__body">'+body()+'</div>'+
        '<div class="wiz__foot">'+
          '<button class="btn btn--ghost btn--sm" type="button" id="w-back">'+(step===0?'Cancel':'Back')+'</button>'+
          '<button class="btn btn--wine btn--sm" type="button" id="w-next">'+(step===5?'Create staff member':'Continue')+'</button>'+
        '</div></div>';
      host.classList.add('is-open');
      host.querySelectorAll('[data-x]').forEach(function(b){b.onclick=close;});

      if (step===1) host.querySelectorAll('[name=w-role]').forEach(function(r){
        r.onchange=function(){ data.role_id=r.value; }; });
      if (step===2) host.querySelectorAll('.pick input').forEach(function(cb){
        cb.onchange=function(){
          data.restaurant_ids = [].slice.call(host.querySelectorAll('.pick input:checked'))
            .map(function(x){return x.value;}); }; });
      if (step===3) Crew.sb.from('role_permissions').select('permissions(key)')
        .eq('role_id', data.role_id).then(function(r){
          var el=document.getElementById('w-perms'); if(!el) return;
          el.innerHTML = (r.data||[]).map(function(x){
            return '<span class="badge badge--own">'+x.permissions.key+'</span>';}).join('')
            || '<span style="font-size:12px;color:var(--faint)">No permissions on this role yet.</span>'; });
      if (step===4) host.querySelectorAll('[name=w-mode]').forEach(function(r){
        r.onchange=function(){ data.mode=r.value; draw(); }; });

      document.getElementById('w-back').onclick=function(){
        if(step===0) return close();
        step--; draw(); };
      document.getElementById('w-next').onclick=async function(){
        if(step===0){
          data.full_name=(document.getElementById('w-name').value||'').trim();
          data.email=(document.getElementById('w-email').value||'').trim();
          if(!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(data.email)) return alert('Enter a valid email address.');
          if(!data.full_name) return alert('Enter their name.');
        }
        if(step===4 && data.mode==='temp'){
          data.password=document.getElementById('w-pass').value;
          if((data.password||'').length<10) return alert('Temporary password must be at least 10 characters.');
        }
        if(step<5){ step++; draw(); return; }
        var btn=document.getElementById('w-next'); btn.disabled=true; btn.textContent='Creating…';
        var r=await CrewUsers.fn('create_user', data);
        if(r.error){ btn.disabled=false; btn.textContent='Create staff member'; alert(r.error); return; }
        close(); await CrewUsers.load(); CrewUsers.render();
        alert(data.mode==='invite'
          ? 'Invite sent to '+data.email+'.'
          : 'Created. Temporary password:\\n\\n'+data.password+'\\n\\nGive this to them directly — it is not shown again.');
      };
    }
    function close(){ host.classList.remove('is-open'); host.innerHTML=''; }
    draw();
  }
};
</script>""")
print('crew: users')

# ─────────────────────────────────────────────── roles
B.shell_page('roles.html','Roles — Mosaic Crew','roles', """
  <div class="crew-title">
    <div><h1>Roles</h1><p>The hierarchy is data, not code. Create a role and it appears
      in navigation for everyone who holds it &mdash; no deploy.</p></div>
    <button class="btn btn--wine btn--sm" type="button" id="r-new">Create role</button>
  </div>
  <div class="panel-c" id="r-pyramid"></div>
  <div class="panel-c tscroll" style="margin-top:16px;padding:6px 14px 14px;" id="r-table"></div>
  <div id="r-wizard"></div>
""", scripts="""<script src="../assets/js/crew/roles.js"></script>
<script>
window.pageInit = async function(c){
  await CrewRoles.load(); CrewRoles.render();
  var b=document.getElementById('r-new');
  if(!Crew.can('roles.create')){ b.hidden=true; return; }
  b.onclick=function(){ CrewRoles.wizard(c); };
};
</script>""")

# ─────────────────────────────────────────────── restaurants
B.shell_page('restaurants.html','Restaurants — Mosaic Crew','restaurants', """
  <div class="crew-title"><div><h1>Restaurants</h1>
    <p>Both branches run one menu. Staff see only the branches they are assigned to.</p></div></div>
  <div id="rest-list" class="grid grid--2" style="gap:14px;"></div>
""", scripts="""<script>
window.pageInit = async function(c){
  var r = await Crew.sb.from('restaurants').select('*').order('name');
  var counts = await Crew.sb.from('user_restaurants').select('restaurant_id');
  var n={}; (counts.data||[]).forEach(function(x){n[x.restaurant_id]=(n[x.restaurant_id]||0)+1;});
  var may = Crew.can('restaurants.edit');
  document.getElementById('rest-list').innerHTML = (r.data||[]).map(function(x){
    return '<div class="panel-c" style="padding:20px;display:flex;flex-direction:column;gap:10px;">'+
      '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;">'+
        '<h2 style="font-size:20px;">'+x.name+'</h2>'+
        '<span class="badge '+(x.is_active?'badge--ok':'badge--off')+'">'+(x.is_active?'open':'closed')+'</span></div>'+
      '<p style="font-size:13px;color:var(--muted);">'+(x.address||'')+'</p>'+
      '<p style="font-size:13px;">'+(x.phone||'')+' &middot; '+(n[x.id]||0)+' staff</p>'+
      (may?'<label class="fld"><span>Phone</span><input value="'+(x.phone||'')+'" data-rid="'+x.id+'" data-f="phone"></label>'+
           '<label class="fld"><span>Address</span><input value="'+(x.address||'')+'" data-rid="'+x.id+'" data-f="address"></label>'+
           '<button class="btn btn--wine btn--sm" data-save="'+x.id+'">Save</button>':'')+
    '</div>'; }).join('');
  document.querySelectorAll('[data-save]').forEach(function(b){
    b.onclick=async function(){
      var id=b.dataset.save, patch={};
      document.querySelectorAll('[data-rid="'+id+'"]').forEach(function(i){patch[i.dataset.f]=i.value;});
      var u=await Crew.sb.from('restaurants').update(patch).eq('id',id);
      if(u.error) return alert(u.error.message);
      await Crew.sb.from('audit_logs').insert({actor_id:c.user.id,actor_email:c.profile.email,
        action:'restaurant.updated',resource:'restaurants',resource_id:id,after:patch});
      b.textContent='Saved'; setTimeout(function(){b.textContent='Save';},1500);
    };});
};
</script>""")
print('crew: roles, restaurants')

# ─────────────────────────────────────────────── waiter: my orders
B.shell_page('orders.html','Orders — Mosaic Crew','orders', """
  <div class="crew-title"><div><h1>Orders</h1><p id="o-sub">Your active orders</p></div>
    <a class="btn btn--wine btn--sm" href="/crew/new-order.html">New order</a></div>
  <div id="o-sound"></div>
  <div class="oq" id="o-list"><p class="crew-empty">Loading…</p></div>
""", scripts=ORDER_JS + """<script>
window.pageInit = async function(c){
  await CrewOrders.statusDefs();
  document.getElementById('o-sound').innerHTML = CrewOrders.soundBar();
  var ACTIVE=['DRAFT','SUBMITTED','READY','SERVED','NEEDS_ATTENTION'];
  async function draw(){
    var rows = await CrewOrders.fetchOrders(ACTIVE, {mine:true});
    document.getElementById('o-sub').textContent =
      rows.length ? rows.length+' active' : 'Nothing active right now';
    document.getElementById('o-list').innerHTML = CrewOrders.renderGrouped(rows, function(o){
          if(o.status==='DRAFT')  return '<button class="btn btn--wine" data-go="SUBMITTED" data-id="'+o.id+'">Submit</button>';
          if(o.status==='SUBMITTED') return '<button class="btn btn--wine" data-go="SENT_TO_KITCHEN" data-id="'+o.id+'">Send to kitchen</button>';
          if(o.status==='READY')  return '<button class="btn btn--wine" data-go="SERVED" data-id="'+o.id+'">Mark served</button>';
          if(o.status==='SERVED') return '<button class="btn btn--ghost" data-go="COMPLETED" data-id="'+o.id+'">Complete</button>';
          return '<span class="ocard__age">With the kitchen</span>';
        }, 'No active orders. Tap <b>New order</b> to start one.');
    document.querySelectorAll('[data-go]').forEach(function(b){
      b.onclick=async function(){ b.disabled=true;
        await CrewOrders.move(b.dataset.id, b.dataset.go); draw(); };});
  }
  await draw();
  CrewOrders.watch(draw);
  document.addEventListener('orders:changed', draw);
  document.addEventListener('crew:restaurant', draw);
  setInterval(draw, 60000);
};
</script>""")

# ─────────────────────────────────────────────── waiter: new order
B.shell_page('new-order.html','New order — Mosaic Crew','new-order', """
  <div class="crew-title"><div><h1>New order</h1><p>Tap to add. Built for speed.</p></div>
    <a class="btn btn--ghost btn--sm" href="/crew/quick-notes.html">Quick note instead</a></div>
  <div class="no-grid">
    <div>
      <div class="no-tools">
        <input id="no-search" type="search" placeholder="Search the menu…" aria-label="Search menu">
        <div class="no-cats" id="no-cats"></div>
      </div>
      <div class="no-items" id="no-items"><p class="crew-empty">Loading menu…</p></div>
    </div>
    <aside class="no-cart panel-c">
      <h2>This order</h2>
      <label class="fld"><span>Table</span><input id="no-table" placeholder="e.g. 12"></label>
      <div id="no-lines"><p class="crew-empty" style="padding:20px 0">Nothing yet</p></div>
      <label class="fld"><span>Notes for the kitchen</span>
        <textarea id="no-notes" placeholder="Allergies, timing, birthday…"></textarea></label>
      <div class="no-total"><span>Total</span><b id="no-total">AED 0</b></div>
      <button class="btn btn--wine" id="no-submit" style="width:100%">Submit order</button>
    </aside>
  </div>
""", scripts=ORDER_JS + """<script>
window.pageInit = async function(c){
  var cart={}, cats=[], items=[], active='all';
  var r = await Promise.all([
    Crew.sb.from('menu_categories').select('*').eq('is_active',true).order('sort_order'),
    Crew.sb.from('menu_items').select('*').eq('is_available',true).order('sort_order')
  ]);
  cats=r[0].data||[]; items=r[1].data||[];
  var byCat={}; items.forEach(function(i){(byCat[i.category_id]=byCat[i.category_id]||[]).push(i);});

  document.getElementById('no-cats').innerHTML =
    '<button class="nochip is-on" data-c="all">All</button>' +
    cats.map(function(x){ return '<button class="nochip" data-c="'+x.id+'">'+CrewOrders.esc(x.name)+'</button>'; }).join('');

  function visible(){
    var q=(document.getElementById('no-search').value||'').toLowerCase();
    return items.filter(function(i){
      if(active!=='all' && i.category_id!==active) return false;
      return !q || i.name.toLowerCase().indexOf(q)>-1;
    });
  }
  function drawItems(){
    document.getElementById('no-items').innerHTML = visible().map(function(i){
      var n=cart[i.id]?cart[i.id].qty:0;
      return '<button class="noitem'+(n?' is-in':'')+'" data-add="'+i.id+'">'+
        '<span>'+CrewOrders.esc(i.name)+'</span>'+
        '<i>'+Number(i.price).toFixed(0)+'</i>'+
        (n?'<em>'+n+'</em>':'')+'</button>'; }).join('')
        || '<p class="crew-empty">Nothing matches.</p>';
    document.querySelectorAll('[data-add]').forEach(function(b){
      b.onclick=function(){
        var it=items.filter(function(x){return x.id===b.dataset.add;})[0];
        cart[it.id]=cart[it.id]||{item:it,qty:0,notes:''};
        cart[it.id].qty++; drawItems(); drawCart(); };});
  }
  function drawCart(){
    var ks=Object.keys(cart);
    document.getElementById('no-lines').innerHTML = ks.length ? ks.map(function(k){
      var l=cart[k];
      return '<div class="noline"><b>'+l.qty+'&times;</b><span>'+CrewOrders.esc(l.item.name)+
        '<input placeholder="note" value="'+CrewOrders.esc(l.notes)+'" data-note="'+k+'"></span>'+
        '<button data-less="'+k+'" aria-label="One fewer">&minus;</button>'+
        '<button data-more="'+k+'" aria-label="One more">+</button></div>'; }).join('')
      : '<p class="crew-empty" style="padding:20px 0">Nothing yet</p>';
    var t=ks.reduce(function(s,k){return s+cart[k].qty*Number(cart[k].item.price);},0);
    document.getElementById('no-total').textContent='AED '+t.toFixed(0);
    document.querySelectorAll('[data-more]').forEach(function(b){b.onclick=function(){cart[b.dataset.more].qty++;drawItems();drawCart();};});
    document.querySelectorAll('[data-less]').forEach(function(b){b.onclick=function(){
      var k=b.dataset.less; if(--cart[k].qty<=0) delete cart[k]; drawItems(); drawCart();};});
    document.querySelectorAll('[data-note]').forEach(function(i){i.oninput=function(){cart[i.dataset.note].notes=i.value;};});
  }
  document.getElementById('no-search').oninput=drawItems;
  document.getElementById('no-cats').onclick=function(e){
    var b=e.target.closest('[data-c]'); if(!b) return;
    active=b.dataset.c;
    document.querySelectorAll('.nochip').forEach(function(x){x.classList.toggle('is-on',x===b);});
    drawItems(); };
  drawItems(); drawCart();

  document.getElementById('no-submit').onclick=async function(){
    var ks=Object.keys(cart); if(!ks.length) return alert('Add at least one item.');
    var rid = (CrewShell.restaurant()!=='all' ? CrewShell.restaurant() : (c.restaurants[0]||{}).id);
    if(!rid) return alert('Pick a branch first.');
    var btn=this; btn.disabled=true; btn.textContent='Submitting…';
    var o=await Crew.sb.from('orders').insert({
      restaurant_id:rid, table_label:document.getElementById('no-table').value||null,
      created_by:c.user.id, owner_id:c.user.id,
      notes:document.getElementById('no-notes').value||null }).select().single();
    if(o.error){ btn.disabled=false; btn.textContent='Submit order'; return alert(o.error.message); }
    await Crew.sb.from('order_items').insert(ks.map(function(k){
      return { order_id:o.data.id, item_id:cart[k].item.id, name:cart[k].item.name,
               unit_price:cart[k].item.price, qty:cart[k].qty, notes:cart[k].notes||null }; }));
    await Crew.sb.rpc('transition_order',{p_order:o.data.id,p_to:'SUBMITTED',p_meta:{}});
    await Crew.sb.rpc('transition_order',{p_order:o.data.id,p_to:'SENT_TO_KITCHEN',p_meta:{}});
    location.href='orders.html';
  };
};
</script>""")
print('crew: orders, new-order')

# ─────────────────────────────────────────────── waiter: quick notes fallback
B.shell_page('quick-notes.html','Quick notes — Mosaic Crew','quick-notes', """
  <div class="crew-title"><div><h1>Quick note</h1>
    <p>Backup capture. Type it as you would on paper &mdash; this is <b>not</b> a structured
       order until someone converts it.</p></div></div>
  <div class="panel-c" style="padding:18px;max-width:520px;display:flex;flex-direction:column;gap:12px;">
    <label class="fld"><span>Table</span><input id="qn-table" placeholder="12"></label>
    <label class="fld"><span>The order</span>
      <textarea id="qn-text" rows="9" style="min-height:200px;font-size:16px"
        placeholder="2 Ribeye&#10;1 Caesar salad&#10;1 Coke&#10;No onions"></textarea></label>
    <button class="btn btn--wine" id="qn-save" style="width:100%">Save note</button>
    <p class="crew-note" style="text-align:left">Saved notes appear for supervisors and can be
       turned into a real order later.</p>
  </div>
  <div style="margin-top:20px"><h2 style="font-size:16px;margin-bottom:10px">Your recent notes</h2>
    <div class="oq" id="qn-list"></div></div>
""", scripts=ORDER_JS + """<script>
window.pageInit = async function(c){
  await CrewOrders.statusDefs();
  async function draw(){
    var r=await Crew.sb.from('orders').select('*, order_items(*)')
      .eq('is_quick_note',true).eq('created_by',c.user.id)
      .order('created_at',{ascending:false}).limit(12);
    document.getElementById('qn-list').innerHTML=(r.data||[]).length
      ? (r.data).map(function(o){return CrewOrders.card(o,null);}).join('')
      : '<p class="crew-empty">No notes yet.</p>';
  }
  document.getElementById('qn-save').onclick=async function(){
    var txt=document.getElementById('qn-text').value.trim();
    if(!txt) return alert('Write the order first.');
    var rid=(CrewShell.restaurant()!=='all'?CrewShell.restaurant():(c.restaurants[0]||{}).id);
    if(!rid) return alert('Pick a branch first.');
    var b=this; b.disabled=true; b.textContent='Saving…';
    var o=await Crew.sb.from('orders').insert({
      restaurant_id:rid, created_by:c.user.id, owner_id:c.user.id,
      table_label:document.getElementById('qn-table').value||null,
      is_quick_note:true, quick_note_text:txt }).select().single();
    b.disabled=false; b.textContent='Save note';
    if(o.error) return alert(o.error.message);
    document.getElementById('qn-text').value=''; document.getElementById('qn-table').value='';
    draw();
  };
  draw();
};
</script>""")

# ─────────────────────────────────────────────── chef
B.shell_page('kitchen.html','Kitchen — Mosaic Crew','kitchen', """
  <div class="crew-title"><div><h1 id="k-title">Kitchen</h1><p id="k-sub"></p></div>
    <div id="k-scope"></div></div>
  <div id="k-sound"></div>
  <div id="k-list"><p class="crew-empty">Loading…</p></div>
""", scripts=ORDER_JS + """<script>
window.pageInit = async function(c){
  var defs = await CrewOrders.statusDefs();
  document.getElementById('k-sound').innerHTML = CrewOrders.soundBar();

  /* A chef owns two states and should not be shown anything else. A supervisor
     and above oversee the whole pass, so an order they mark ready must not
     vanish on them — they keep the full pipeline in view. */
  var oversees = Crew.can('orders.view_all');
  var COOK  = ['SENT_TO_KITCHEN','IN_PREPARATION','NEEDS_ATTENTION'];
  var FULL  = ['SUBMITTED','SENT_TO_KITCHEN','IN_PREPARATION','READY','SERVED','NEEDS_ATTENTION'];
  var scope = oversees ? (localStorage.getItem('mosaic.kitchen.scope') || 'full') : 'cook';

  if (oversees) {
    document.getElementById('k-scope').innerHTML =
      '<div class="segbtn" role="group" aria-label="What to show">' +
        '<button type="button" data-s="full" aria-pressed="'+(scope==='full')+'">Whole pass</button>' +
        '<button type="button" data-s="cook" aria-pressed="'+(scope==='cook')+'">Kitchen only</button>' +
      '</div>';
    document.querySelectorAll('[data-s]').forEach(function(b){
      b.onclick=function(){ scope=b.dataset.s;
        localStorage.setItem('mosaic.kitchen.scope',scope); draw(); };});
  }

  function actions(o){
    if(o.status==='SUBMITTED')
      return '<button class="btn btn--ghost" data-go="SENT_TO_KITCHEN" data-id="'+o.id+'">Send to kitchen</button>';
    if(o.status==='SENT_TO_KITCHEN')
      return '<button class="btn btn--wine" data-go="IN_PREPARATION" data-id="'+o.id+'">Start</button>';
    if(o.status==='IN_PREPARATION')
      return '<button class="btn btn--wine" data-go="READY" data-id="'+o.id+'">Ready</button>';
    if(o.status==='READY')
      return oversees
        ? '<span class="kwait">Waiting for a waiter</span>' +
          '<button class="btn btn--ghost" data-go="IN_PREPARATION" data-id="'+o.id+'">Back to kitchen</button>'
        : '';
    if(o.status==='SERVED') return '<span class="kwait">Served</span>';
    return '<button class="btn btn--ghost" data-go="IN_PREPARATION" data-id="'+o.id+'">Take it</button>';
  }

  async function draw(){
    var want = scope==='full' ? FULL : COOK;
    var rows = await CrewOrders.fetchOrders(want);
    document.getElementById('k-title').textContent = scope==='full' ? 'The pass' : 'Kitchen';

    if(scope==='cook'){
      var n=rows.length;
      document.getElementById('k-sub').textContent = n ? n+' in the queue' : 'Queue is clear';
      document.getElementById('k-list').innerHTML =
        CrewOrders.renderGrouped(rows, actions, 'Nothing to cook. Enjoy the quiet.');
    } else {
      /* lanes across the whole pass, so a supervisor watches an order all the
         way from the waiter to the table instead of losing it at each handoff */
      var LANES=['SUBMITTED','SENT_TO_KITCHEN','IN_PREPARATION','READY','SERVED'];
      var att=rows.filter(function(o){return o.status==='NEEDS_ATTENTION';});
      document.getElementById('k-sub').textContent =
        rows.length+' live'+(att.length?' · '+att.length+' need attention':'');
      document.getElementById('k-list').innerHTML =
        (att.length? '<section class="klane klane--att"><header><b>Needs attention</b><i>'+att.length+
          '</i></header><div class="klane__b">'+att.map(function(o){
            return CrewOrders.card(o,actions,{hideStatus:true}); }).join('')+'</div></section>' : '')+
        '<div class="kb">'+LANES.map(function(k){
          var col=rows.filter(function(o){return o.status===k;});
          return '<section class="kbcol" data-k="'+k+'"><header style="--c:'+defs[k].colour+'">'+
            '<b>'+defs[k].label+'</b><i>'+col.length+'</i></header><div class="kbcol__b">'+
            (col.length? col.map(function(o){
              return CrewOrders.card(o,actions,{hideStatus:true}); }).join('')
              : '<p class="kbcol__e">&mdash;</p>')+
          '</div></section>'; }).join('')+'</div>';
    }

    document.querySelectorAll('[data-go]').forEach(function(b){
      b.onclick=async function(e){ e.stopPropagation(); b.disabled=true;
        await CrewOrders.move(b.dataset.id,b.dataset.go); draw(); };});
  }

  await draw(); CrewOrders.watch(draw);
  document.addEventListener('orders:changed',draw);
  setInterval(draw,45000);
};
</script>""")
print('crew: quick-notes, kitchen')

# ─────────────────────────────────────────────── supervisor command centre
B.shell_page('monitor.html','Monitor — Mosaic Crew','monitor', """
  <div class="crew-title"><div><h1 id="mo-title">Command centre</h1>
    <p id="mo-sub">Pick a branch. Overrides are logged against you.</p></div>
    <button class="btn btn--ghost btn--sm" id="mo-back" hidden>All branches</button></div>
  <div id="mo-sound"></div>
  <div id="mo-branches" class="mo-branches"></div>
  <div id="mo-board" hidden></div>
  <div id="mo-drawer"></div>
""", scripts=ORDER_JS + """<script>
window.pageInit = async function(c){
  var defs = await CrewOrders.statusDefs();
  document.getElementById('mo-sound').innerHTML = CrewOrders.soundBar();
  /* the state machine is defined in Postgres; mirror it here only to grey out
     illegal drop targets. transition_order() still has the final say. */
  var ALLOWED={};
  (await Crew.sb.from('order_transitions').select('from_status,to_status')).data
    ?.forEach(function(t){ (ALLOWED[t.from_status]=ALLOWED[t.from_status]||[]).push(t.to_status); });
  var LIVE=['SUBMITTED','SENT_TO_KITCHEN','IN_PREPARATION','READY','SERVED','NEEDS_ATTENTION'];
  var COLS=['SUBMITTED','SENT_TO_KITCHEN','IN_PREPARATION','READY','SERVED','NEEDS_ATTENTION'];
  var branch=null, rows=[];

  async function pull(){
    rows = await CrewOrders.fetchOrders(LIVE.concat(['DRAFT']));
  }

  function branchView(){
    var ids=[]; rows.forEach(function(o){ if(ids.indexOf(o.restaurant_id)===-1) ids.push(o.restaurant_id); });
    (c.restaurants||[]).forEach(function(r){ if(ids.indexOf(r.id)===-1) ids.push(r.id); });
    ids.sort(function(a,b){return CrewOrders.restName(a).localeCompare(CrewOrders.restName(b));});
    document.getElementById('mo-branches').innerHTML = ids.map(function(rid){
      var mine=rows.filter(function(o){return o.restaurant_id===rid;});
      var urgent=mine.filter(function(o){return o.priority==='URGENT';}).length;
      var late=mine.filter(function(o){return (Date.now()-new Date(o.created_at))/60000>25;}).length;
      return '<button class="mo-branch" data-b="'+rid+'">'+
        '<h2>'+CrewOrders.esc(CrewOrders.restName(rid))+'</h2>'+
        '<b>'+mine.length+'</b><span>live orders</span>'+
        '<div class="mo-branch__f">'+
          COLS.slice(0,4).map(function(k){
            var n=mine.filter(function(o){return o.status===k;}).length;
            return '<i><em>'+n+'</em>'+defs[k].label+'</i>'; }).join('')+
        '</div>'+
        (urgent?'<span class="mo-flag mo-flag--u">'+urgent+' urgent</span>':'')+
        (late?'<span class="mo-flag mo-flag--l">'+late+' over 25 min</span>':'')+
      '</button>'; }).join('');
    document.querySelectorAll('[data-b]').forEach(function(b){
      b.onclick=function(){ branch=b.dataset.b; show(); };});
  }

  var mine=[];
  function boardView(){
    mine=rows.filter(function(o){return o.restaurant_id===branch;});
    document.getElementById('mo-board').innerHTML =
      '<div class="kb">'+COLS.map(function(k){
        var col=mine.filter(function(o){return o.status===k;});
        return '<section class="kbcol" data-k="'+k+'"><header style="--c:'+defs[k].colour+'">'+
          '<b>'+defs[k].label+'</b><i>'+col.length+'</i></header><div class="kbcol__b">'+
          '<span class="kbdrop">Not a legal move</span>'+
          (col.length? col.map(function(o){
            return CrewOrders.card(o,null,{hideStatus:true,hideBranch:true}); }).join('')
            : '<p class="kbcol__e">&mdash;</p>')+
        '</div></section>'; }).join('')+'</div>';
    var board=document.querySelector('#mo-board .kb');
    var dragId=null;

    document.querySelectorAll('#mo-board .ocard').forEach(function(el){
      var o=mine.filter(function(x){return x.id===el.dataset.id;})[0];
      el.onclick=function(e){ if(!el.classList.contains('is-drag')) detail(el.dataset.id); };
      if(!Crew.can('orders.change_status')) return;
      el.draggable=true;
      el.addEventListener('dragstart',function(e){
        dragId=el.dataset.id; el.classList.add('is-drag');
        e.dataTransfer.effectAllowed='move';
        try{ e.dataTransfer.setData('text/plain', dragId); }catch(_){}
        board.classList.add('is-dragging');
        /* mark the columns this order may legally reach, from the DB's own
           transition table — the UI never invents a legal move */
        document.querySelectorAll('.kbcol').forEach(function(col){
          var ok = ALLOWED[o.status] && ALLOWED[o.status].indexOf(col.dataset.k)>-1;
          col.classList.toggle('is-nodrop', !ok || col.dataset.k===o.status);
        });
      });
      el.addEventListener('dragend',function(){
        el.classList.remove('is-drag'); dragId=null;
        board.classList.remove('is-dragging');
        document.querySelectorAll('.kbcol').forEach(function(c){
          c.classList.remove('is-over','is-nodrop'); });
      });
    });

    document.querySelectorAll('.kbcol').forEach(function(col){
      col.addEventListener('dragover',function(e){
        if(col.classList.contains('is-nodrop')) return;
        e.preventDefault(); col.classList.add('is-over'); });
      col.addEventListener('dragleave',function(){ col.classList.remove('is-over'); });
      col.addEventListener('drop',async function(e){
        e.preventDefault(); col.classList.remove('is-over');
        if(!dragId || col.classList.contains('is-nodrop')) return;
        var o=mine.filter(function(x){return x.id===dragId;})[0];
        var to=col.dataset.k;
        if(!o || o.status===to) return;
        var r=await CrewOrders.move(o.id,to,{via:'kanban-drag'});
        if(r && r.error){ alert(r.error.message||r.error); }
        await pull(); show();
      });
    });
  }

  function show(){
    var on=!!branch;
    document.getElementById('mo-branches').hidden=on;
    document.getElementById('mo-board').hidden=!on;
    document.getElementById('mo-back').hidden=!on;
    document.getElementById('mo-title').textContent = on? CrewOrders.restName(branch) : 'Command centre';
    document.getElementById('mo-sub').textContent = on
      ? 'Tap any order to open it'
      : 'Pick a branch. Overrides are logged against you.';
    on? boardView() : branchView();
  }

  async function detail(id){
    var o=rows.filter(function(x){return x.id===id;})[0]; if(!o) return;
    var ev=await Crew.sb.from('order_events').select('*').eq('order_id',id).order('created_at');
    var host=document.getElementById('mo-drawer');
    var legal=Object.keys(defs).filter(function(k){return k!==o.status;});
    host.innerHTML='<div class="udrawer__veil" data-x></div><aside class="udrawer__p">'+
      '<header><h2>Order #'+o.number+'</h2><button type="button" data-x aria-label="Close">&times;</button></header>'+
      '<div class="udrawer__b">'+
        '<div class="odt"><span class="ostat" style="background:'+defs[o.status].colour+'">'+
          defs[o.status].label+'</span>'+
          (o.priority!=='NORMAL'?'<span class="opri opri--'+o.priority.toLowerCase()+'">'+
            (o.priority==='URGENT'?'Urgent':'High')+'</span>':'')+'</div>'+
        '<dl class="ukv">'+
          '<dt>Branch</dt><dd>'+CrewOrders.esc(CrewOrders.restName(o.restaurant_id))+'</dd>'+
          '<dt>Table</dt><dd>'+CrewOrders.esc(o.table_label||'—')+'</dd>'+
          '<dt>Opened</dt><dd>'+CrewOrders.age(o.created_at)+' ago</dd>'+
        '</dl>'+
        (o.is_quick_note
          ? '<div class="ocard__note"><b>Quick note</b><br>'+
             CrewOrders.esc(o.quick_note_text||'').replace(/\\n/g,'<br>')+'</div>'
          : '<ul class="ocard__items">'+(o.order_items||[]).map(function(i){
              return '<li><b>'+i.qty+'&times;</b><span>'+CrewOrders.esc(i.name)+
                (i.notes?'<i>'+CrewOrders.esc(i.notes)+'</i>':'')+'</span></li>';}).join('')+'</ul>')+
        (o.notes?'<div class="ocard__note">'+CrewOrders.esc(o.notes)+'</div>':'')+
        '<hr class="hair">'+
        '<label class="fld"><span>Move to</span><select id="od-to">'+
          '<option value="">Choose a state…</option>'+
          legal.map(function(k){return '<option value="'+k+'">'+defs[k].label+'</option>';}).join('')+
        '</select></label>'+
        '<label class="fld"><span>Priority</span><select id="od-pri">'+
          ['NORMAL','HIGH','URGENT'].map(function(p){
            return '<option value="'+p+'"'+(p===o.priority?' selected':'')+'>'+p+'</option>';}).join('')+
        '</select></label>'+
        '<h3 style="font-size:14px;margin-top:6px">History</h3>'+
        '<ol class="htl">'+(ev.data||[]).map(function(e){
          return '<li><time>'+new Date(e.created_at).toLocaleTimeString('en-GB',
            {hour:'2-digit',minute:'2-digit'})+'</time> '+
            (e.action==='status_change'
              ? (defs[e.from_status]||{}).label+' &rarr; <b>'+(defs[e.to_status]||{}).label+'</b>'
              : e.action==='undo' ? '<b>undone</b>'
              : e.action==='priority_change' ? 'priority '+(e.metadata||{}).from+' &rarr; '+(e.metadata||{}).to
              : e.action)+(e.actor_role?' <i>by '+e.actor_role+'</i>':'')+'</li>';}).join('')+'</ol>'+
      '</div></aside>';
    host.classList.add('is-open');
    host.querySelectorAll('[data-x]').forEach(function(b){b.onclick=function(){host.classList.remove('is-open');};});
    document.getElementById('od-to').onchange=async function(){
      if(!this.value) return;
      if(!confirm('Override order #'+o.number+' to '+defs[this.value].label+'? This is logged.')){
        this.value=''; return; }
      await CrewOrders.move(o.id,this.value,{override:true});
      host.classList.remove('is-open'); await pull(); show(); };
    document.getElementById('od-pri').onchange=async function(){
      var r=await Crew.sb.rpc('set_order_priority',{p_order:o.id,p_priority:this.value});
      if(r.error) return alert(r.error.message);
      host.classList.remove('is-open'); await pull(); show(); };
  }

  document.getElementById('mo-back').onclick=function(){ branch=null; show(); };
  async function refresh(){ await pull(); show(); }
  await refresh();
  CrewOrders.watch(refresh);
  document.addEventListener('orders:changed',refresh);
  document.addEventListener('crew:restaurant',refresh);
  setInterval(refresh,30000);
};
</script>""")

# ─────────────────────────────────────────────── order history
B.shell_page('history.html','History — Mosaic Crew','history', """
  <div class="crew-title"><div><h1>History</h1><p>Every state change, immutable.</p></div></div>
  <div class="panel-c" style="padding:14px;"><div id="h-list">Loading…</div></div>
""", scripts=ORDER_JS + """<script>
window.pageInit = async function(c){
  var defs=await CrewOrders.statusDefs();
  var r=await Crew.sb.from('orders').select('*, order_items(*)')
    .order('created_at',{ascending:false}).limit(40);
  var ids=(r.data||[]).map(function(o){return o.id;});
  var ev = ids.length ? await Crew.sb.from('order_events').select('*')
    .in('order_id',ids).order('created_at') : {data:[]};
  var byOrder={}; (ev.data||[]).forEach(function(e){(byOrder[e.order_id]=byOrder[e.order_id]||[]).push(e);});
  document.getElementById('h-list').innerHTML=(r.data||[]).length
    ? (r.data).map(function(o){
      var evs=byOrder[o.id]||[];
      return '<details class="hrow"><summary><b>#'+o.number+'</b> '+
        (o.table_label?CrewOrders.esc(o.table_label)+' · ':'')+
        '<span class="ostat" style="background:'+(defs[o.status]||{}).colour+'">'+
        (defs[o.status]||{}).label+'</span> <i>'+new Date(o.created_at)
          .toLocaleString('en-GB',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})+
        '</i></summary><ol class="htl">'+
        evs.map(function(e){
          return '<li><time>'+new Date(e.created_at).toLocaleTimeString('en-GB',
            {hour:'2-digit',minute:'2-digit'})+'</time> '+
            (e.action==='status_change'
              ? (e.from_status||'—')+' &rarr; <b>'+e.to_status+'</b>'
              : e.action==='undo' ? '<b>undone</b> back to '+e.to_status
              : e.action==='priority_change' ? 'priority '+(e.metadata||{}).from+' &rarr; '+(e.metadata||{}).to
              : e.action)+
            (e.actor_role?' <i>by '+e.actor_role+'</i>':'')+'</li>'; }).join('')+
        '</ol></details>'; }).join('')
    : '<p class="crew-empty">No orders yet.</p>';
};
</script>""")

# ─────────────────────────────────────────────── audit log
B.shell_page('audit.html','Audit log — Mosaic Crew','audit', """
  <div class="crew-title"><div><h1>Audit log</h1>
    <p>Append-only. Update and delete are revoked at the database level &mdash;
       nobody can rewrite this, including a system owner.</p></div></div>
  <div class="panel-c tscroll" style="padding:6px 14px 14px;"><div id="a-list">Loading…</div></div>
""", scripts="""<script>
window.pageInit = async function(c){
  var r=await Crew.sb.from('audit_logs').select('*').order('created_at',{ascending:false}).limit(200);
  if(r.error){ document.getElementById('a-list').innerHTML='<p class="crew-empty">'+r.error.message+'</p>'; return; }
  document.getElementById('a-list').innerHTML=(r.data||[]).length
    ? '<table class="rtable"><thead><tr><th>When</th><th>Who</th><th>Action</th><th>Target</th><th>Detail</th></tr></thead><tbody>'+
      r.data.map(function(a){
        return '<tr><td>'+new Date(a.created_at).toLocaleString('en-GB',
            {day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})+'</td>'+
          '<td>'+(a.actor_email||'system')+'<br><small>'+(a.actor_role||'')+'</small></td>'+
          '<td><code>'+a.action+'</code></td><td>'+a.resource+'</td>'+
          '<td><small>'+(a.after?JSON.stringify(a.after).slice(0,90):'')+'</small></td></tr>'; }).join('')+
      '</tbody></table>'
    : '<p class="crew-empty">Nothing logged yet.</p>';
};
</script>""")

# ─────────────────────────────────────────────── reports + settings (light)
B.shell_page('reports.html','Reports — Mosaic Crew','reports', """
  <div class="crew-title"><div><h1>Reports</h1><p>Operational snapshot.</p></div></div>
  <div class="qgrid" id="rep-stats"></div>
  <div class="panel-c" style="margin-top:16px;padding:20px;"><div id="rep-body"></div></div>
""", scripts="""<script>
window.pageInit = async function(c){
  var o=await Crew.sb.from('orders').select('status,priority,created_at,completed_at,restaurant_id');
  var rows=o.data||[];
  var done=rows.filter(function(x){return x.completed_at;});
  var avg=done.length? Math.round(done.reduce(function(s,x){
    return s+(new Date(x.completed_at)-new Date(x.created_at))/60000;},0)/done.length):0;
  document.getElementById('rep-stats').innerHTML=
    [['Orders total',rows.length],['Completed',done.length],
     ['Urgent',rows.filter(function(x){return x.priority==='URGENT';}).length],
     ['Avg minutes',avg]].map(function(s){
      return '<div class="qcell"><b>'+s[1]+'</b><span>'+s[0]+'</span></div>';}).join('');
  var by={}; rows.forEach(function(x){by[x.status]=(by[x.status]||0)+1;});
  document.getElementById('rep-body').innerHTML='<h2 style="font-size:16px;margin-bottom:10px">By status</h2>'+
    Object.keys(by).map(function(k){return '<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--crew-line);font-size:13.5px"><span>'+k+'</span><b>'+by[k]+'</b></div>';}).join('');
};
</script>""")

B.shell_page('settings.html','Settings — Mosaic Crew','settings', """
  <div class="crew-title"><div><h1>Settings</h1></div></div>
  <div class="panel-c" style="padding:20px;max-width:520px;display:flex;flex-direction:column;gap:14px;">
    <h2 style="font-size:16px">Notification sound</h2>
    <label class="pick"><input type="checkbox" id="set-sound"><span><b>Play a sound</b>
      <span>Short tones for new orders and ready plates</span></span></label>
    <label class="fld"><span>Volume</span><input type="range" id="set-vol" min="0" max="1" step="0.05"></label>
    <button class="btn btn--ghost btn--sm" id="set-test" style="align-self:flex-start">Test sound</button>
  </div>
""", scripts=ORDER_JS + """<script>
window.pageInit = function(c){
  var s=CrewOrders.Sound;
  var cb=document.getElementById('set-sound'), vol=document.getElementById('set-vol');
  cb.checked=s.enabled; vol.value=s.volume;
  cb.onchange=function(){ s.unlock(); s.setEnabled(cb.checked); };
  vol.oninput=function(){ s.setVolume(parseFloat(vol.value)); };
  document.getElementById('set-test').onclick=function(){ s.unlock(); s.play('order_ready'); };
};
</script>""")

B.shell_page('profile.html','My profile — Mosaic Crew',None, """
  <div class="crew-title"><div><h1>My profile</h1></div></div>
  <div class="panel-c" style="padding:20px;max-width:520px;display:flex;flex-direction:column;gap:14px;">
    <div class="imgpick">
      <div class="imgpick__prev imgpick__prev--round" id="pf-prev"><span>No photo</span></div>
      <div class="imgpick__act">
        <label class="btn btn--ghost btn--sm">Change photo
          <input type="file" id="pf-img" accept="image/jpeg,image/png,image/webp" hidden></label>
        <p id="pf-imgmsg" class="crew-note" style="text-align:left;margin:0"></p>
      </div>
    </div>
    <dl class="ukv" id="pf-kv"></dl><hr class="hair">
    <label class="fld"><span>Full name</span><input id="pf-name"></label>
    <button class="btn btn--wine btn--sm" id="pf-save" style="align-self:flex-start">Save</button>
    <hr class="hair">
    <h2 style="font-size:16px">Change password</h2>
    <label class="fld"><span>New password</span><input id="pf-pw" type="password" placeholder="At least 10 characters"></label>
    <button class="btn btn--ghost btn--sm" id="pf-pwsave" style="align-self:flex-start">Update password</button>
  </div>
""", scripts="""<script src="../assets/js/crew/upload.js"></script>
<script>
window.pageInit = function(c){
  var prev=document.getElementById('pf-prev');
  if(c.profile.avatar_path) prev.innerHTML='<img src="'+c.profile.avatar_path+'" alt="">';
  var fi=document.getElementById('pf-img');
  fi.onchange=async function(){
    var msg=document.getElementById('pf-imgmsg'); msg.textContent='Uploading…';
    var r=await CrewUpload.image(fi.files[0],'avatars',{prefix:c.user.id,maxPx:512});
    if(r.error){ msg.textContent=r.error; msg.style.color='var(--bad)'; return; }
    var up=await Crew.sb.from('profiles').update({avatar_path:r.url}).eq('id',c.user.id);
    if(up.error){ msg.textContent=up.error.message; msg.style.color='var(--bad)'; return; }
    prev.innerHTML='<img src="'+r.url+'" alt="">';
    msg.textContent='Saved'; msg.style.color='var(--ok)';
  };
  document.getElementById('pf-kv').innerHTML =
    '<dt>Email</dt><dd>'+c.profile.email+'</dd>'+
    '<dt>Role</dt><dd>'+c.roles.map(function(r){return r.name;}).join(', ')+'</dd>'+
    '<dt>Branches</dt><dd>'+(c.restaurants.map(function(r){return r.name;}).join(', ')||'none')+'</dd>'+
    '<dt>Last login</dt><dd>'+(c.profile.last_login_at? new Date(c.profile.last_login_at)
      .toLocaleString('en-GB',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}):'—')+'</dd>';
  document.getElementById('pf-name').value=c.profile.full_name||'';
  document.getElementById('pf-save').onclick=async function(){
    var r=await Crew.sb.from('profiles').update({full_name:document.getElementById('pf-name').value})
      .eq('id',c.user.id);
    this.textContent=r.error?'Failed':'Saved'; };
  document.getElementById('pf-pwsave').onclick=async function(){
    var pw=document.getElementById('pf-pw').value;
    if(pw.length<10) return alert('At least 10 characters.');
    var r=await Crew.sb.auth.updateUser({password:pw});
    alert(r.error?r.error.message:'Password updated.'); };
};
</script>""")

B.page('reset.html','Set your password — Mosaic Crew', """
<div class="crew-login"><form class="crew-login__card" id="rs-form">
  <div class="crew-login__logo"><img src="../assets/img/brand/logo.webp" alt="">
    <b>MOSAIC</b><span>Set your password</span></div>
  <div class="crew-err" id="rs-err" hidden></div>
  <label class="fld"><span>New password</span>
    <input id="rs-pw" type="password" required placeholder="At least 10 characters"></label>
  <button class="btn btn--wine" type="submit" style="width:100%">Save and sign in</button>
</form></div>
""", scripts="""<script>
document.getElementById('rs-form').addEventListener('submit', async function(e){
  e.preventDefault();
  var pw=document.getElementById('rs-pw').value, err=document.getElementById('rs-err');
  if(pw.length<10){ err.textContent='At least 10 characters.'; err.hidden=false; return; }
  var r=await Crew.sb.auth.updateUser({password:pw});
  if(r.error){ err.textContent=r.error.message; err.hidden=false; return; }
  var c=await Crew.load();
  location.replace(c?Crew.homeFor(c):'index.html');
});
</script>""")
print('crew: monitor, history, audit, reports, settings, profile, reset')

# ─────────────────────────────────────────────── menu CMS
B.shell_page('menu.html','Menu — Mosaic Crew','menu', """
  <div class="crew-title"><div><h1>Menu</h1>
    <p>The operational menu. Changes here drive the waiter's order screen straight away;
       the public website updates when you publish.</p></div>
    <div style="display:flex;gap:8px">
      <button class="btn btn--ghost btn--sm" id="m-new">Add item</button>
      <button class="btn btn--wine btn--sm" id="m-publish">Publish to website</button></div></div>
  <div class="mcms">
    <aside class="mcat-list" id="m-cats"></aside>
    <div><div id="m-items" class="panel-c" style="overflow:hidden"></div></div>
  </div>
  <div id="m-edit"></div>
""", scripts="""<script src="../assets/js/crew/upload.js"></script>
<script>
window.pageInit = async function(c){
  var cats=[], items=[], active=null, may=Crew.can('menu.edit');
  if(!may){ document.getElementById('m-new').hidden=true;
            document.getElementById('m-publish').hidden=true; }

  async function load(){
    var r=await Promise.all([
      Crew.sb.from('menu_categories').select('*').order('sort_order'),
      Crew.sb.from('menu_items').select('*').order('sort_order')]);
    cats=r[0].data||[]; items=r[1].data||[];
    if(!active && cats.length) active=cats[0].id;
  }
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(x){
    return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[x];});}

  function draw(){
    document.getElementById('m-cats').innerHTML=cats.map(function(x){
      var n=items.filter(function(i){return i.category_id===x.id;}).length;
      return '<button data-cat="'+x.id+'" class="'+(x.id===active?'is-on':'')+'">'+
        esc(x.name)+'<i>'+n+'</i></button>'; }).join('');
    var mine=items.filter(function(i){return i.category_id===active;});
    document.getElementById('m-items').innerHTML= mine.length? mine.map(function(i){
      return '<div class="mitem-row'+(i.is_available?'':' is-off')+'" data-item="'+i.id+'">'+
        (i.image_path?'<img src="../'+i.image_path+'" alt="" loading="lazy">':'<span class="ph"></span>')+
        '<div><b>'+esc(i.name)+'</b><small>'+esc(i.description||'')+'</small></div>'+
        '<span class="pr">'+Number(i.price).toFixed(0)+'</span>'+
        (may?'<span class="edithint">&#9998; Edit</span>':'')+
        (may?'<button class="mtoggle" aria-pressed="'+i.is_available+'" data-av="'+i.id+
             '" aria-label="Availability"></button>':'')+
      '</div>'; }).join('') : '<p class="crew-empty">No items in this category.</p>';

    document.querySelectorAll('[data-cat]').forEach(function(b){
      b.onclick=function(){ active=b.dataset.cat; draw(); };});
    document.querySelectorAll('[data-av]').forEach(function(b){
      b.onclick=async function(e){
        e.stopPropagation();
        var id=b.dataset.av, now=b.getAttribute('aria-pressed')==='true';
        var r=await Crew.sb.from('menu_items').update({is_available:!now}).eq('id',id);
        if(r.error) return alert(r.error.message);
        items.filter(function(i){return i.id===id;})[0].is_available=!now;
        await Crew.sb.from('audit_logs').insert({actor_id:c.user.id,actor_email:c.profile.email,
          action:'menu.availability',resource:'menu_items',resource_id:id,after:{is_available:!now}});
        draw(); };});
    if(may) document.querySelectorAll('[data-item]').forEach(function(row){
      row.onclick=function(){ edit(items.filter(function(i){return i.id===row.dataset.item;})[0]); };});
  }

  function edit(it){
    var isNew=!it;
    it=it||{name:'',description:'',price:0,category_id:active,is_available:true};
    var host=document.getElementById('m-edit');
    host.innerHTML='<div class="udrawer__veil" data-x></div><aside class="udrawer__p" role="dialog" aria-modal="true">'+
      '<header><h2>'+(it.id?'Edit dish':'New dish')+'</h2>'+
        '<button type="button" data-x aria-label="Close">&times;</button></header>'+
      '<div class="udrawer__b"><div class="medit">'+
        '<div class="medit__grid">'+
          '<div class="medit__photo">'+
            '<div class="imgpick"><div class="imgpick__prev" id="me-prev">'+
              (it.image_path?'<img src="'+(/^https?:/.test(it.image_path)?it.image_path:'../'+it.image_path)+'" alt="">':'<span>No photo</span>')+
            '</div><div class="imgpick__act">'+
              '<label class="btn btn--ghost btn--sm">Choose photo'+
                '<input type="file" id="me-img" accept="image/jpeg,image/png,image/webp" hidden></label>'+
              '<p id="me-imgmsg" class="crew-note" style="text-align:center;margin:0">JPEG, PNG or WebP</p>'+
            '</div></div>'+
          '</div>'+
          '<div class="medit__fields">'+
            '<label class="fld"><span>Dish name</span>'+
              '<input id="me-name" value="'+esc(it.name||'')+'" placeholder="Hommos Beiruti"></label>'+
            '<label class="fld"><span>Description</span>'+
              '<textarea id="me-desc" placeholder="What is in it, in one line">'+esc(it.description||'')+'</textarea></label>'+
            '<div class="medit__row2">'+
              '<label class="fld"><span>Price (AED)</span>'+
                '<input id="me-price" type="number" step="1" min="0" value="'+(it.price!=null?it.price:'')+'"></label>'+
              '<label class="fld"><span>Category</span><select id="me-cat">'+
                cats.map(function(k){return '<option value="'+k.id+'"'+
                  (k.id===(it.category_id||active)?' selected':'')+'>'+esc(k.name)+'</option>';}).join('')+
              '</select></label>'+
            '</div>'+
          '</div>'+
        '</div>'+
        '<div class="medit__toggle">'+
          '<span><b>Show on the menu</b><span>Hidden dishes stay in the system but cannot be ordered.</span></span>'+
          '<label class="sw"><input type="checkbox" id="me-av"'+(it.is_available!==false?' checked':'')+'><i></i></label>'+
        '</div>'+
        '<div class="medit__foot">'+
          '<button class="btn btn--wine btn--sm" type="button" id="me-save">Save changes</button>'+
          (it.id?'<button class="btn btn--ghost btn--sm" type="button" id="me-dup">Duplicate</button>':'')+
          (it.id?'<button class="btn btn--ghost btn--sm medit__danger" type="button" id="me-del">Delete</button>':'')+
        '</div>'+
      '</div></div></aside>';
    host.classList.add('is-open');
    host.querySelectorAll('[data-x]').forEach(function(b){b.onclick=function(){host.classList.remove('is-open');};});

    var newImagePath = null;
    var fi=document.getElementById('me-img');
    fi.onchange=async function(){
      var msg=document.getElementById('me-imgmsg');
      msg.textContent='Uploading…';
      var r=await CrewUpload.image(fi.files[0],'menu-images',{prefix:'dishes',maxPx:1400});
      if(r.error){ msg.textContent=r.error; msg.style.color='var(--bad)'; return; }
      newImagePath=r.url;
      msg.textContent='Uploaded ('+Math.round(r.size/1024)+' KB)'; msg.style.color='var(--ok)';
      document.getElementById('me-prev').innerHTML='<img src="'+r.url+'" alt="">';
    };

    function payload(){ return {
      name:document.getElementById('me-name').value.trim(),
      description:document.getElementById('me-desc').value.trim(),
      price:parseFloat(document.getElementById('me-price').value)||0,
      category_id:document.getElementById('me-cat').value,
      is_available:document.getElementById('me-av').checked,
      image_path: newImagePath || it.image_path || null }; }

    document.getElementById('me-save').onclick=async function(){
      var p=payload(); if(!p.name) return alert('Name is required.');
      var r = isNew ? await Crew.sb.from('menu_items').insert(p)
                    : await Crew.sb.from('menu_items').update(p).eq('id',it.id);
      if(r.error) return alert(r.error.message);
      await Crew.sb.from('audit_logs').insert({actor_id:c.user.id,actor_email:c.profile.email,
        action:isNew?'menu.created':'menu.updated',resource:'menu_items',
        resource_id:it.id||null,after:p});
      host.classList.remove('is-open'); await load(); draw(); };

    if(!isNew){
      document.getElementById('me-dup').onclick=async function(){
        var p=payload(); p.name=p.name+' (copy)';
        var r=await Crew.sb.from('menu_items').insert(p);
        if(r.error) return alert(r.error.message);
        host.classList.remove('is-open'); await load(); draw(); };
      document.getElementById('me-del').onclick=async function(){
        if(!confirm('Delete "'+it.name+'"? This cannot be undone.')) return;
        var r=await Crew.sb.from('menu_items').delete().eq('id',it.id);
        if(r.error) return alert(r.error.message);
        await Crew.sb.from('audit_logs').insert({actor_id:c.user.id,actor_email:c.profile.email,
          action:'menu.deleted',resource:'menu_items',resource_id:it.id,before:{name:it.name}});
        host.classList.remove('is-open'); await load(); draw(); };
    }
  }

  document.getElementById('m-new').onclick=function(){ edit(null); };
  document.getElementById('m-publish').onclick=async function(){
    var b=this; b.disabled=true; b.textContent='Building…';
    var out={currency:'AED',categories:cats.map(function(x){
      return {name:x.name,slug:x.slug,count:0,items:items
        .filter(function(i){return i.category_id===x.id && i.is_available;})
        .map(function(i){return {id:i.external_id||i.id,name:i.name,desc:i.description,
          price:Number(i.price),img:i.image_path,url:'',inStock:i.is_available};})};})};
    out.categories.forEach(function(c2){c2.count=c2.items.length;});
    var blob=new Blob([JSON.stringify(out)],{type:'application/json'});
    var a=document.createElement('a'); a.href=URL.createObjectURL(blob);
    a.download='menu.json'; a.click();
    await Crew.sb.from('audit_logs').insert({actor_id:c.user.id,actor_email:c.profile.email,
      action:'menu.published',resource:'menu',after:{items:items.filter(function(i){return i.is_available;}).length}});
    b.disabled=false; b.textContent='Publish to website';
    alert('menu.json downloaded. Drop it into website/data/ to update the public site.');
  };

  await load(); draw();
};
</script>""")
print('crew: menu')

# ─────────────────────────────────────────────── bookings
B.shell_page('bookings.html','Bookings — Mosaic Crew','bookings', """
  <div class="crew-title"><div><h1>Bookings</h1>
    <p id="bk-sub">Tables reserved through the website and by phone.</p></div></div>
  <div class="bk-tabs" id="bk-tabs"></div>
  <div id="bk-list"><p class="crew-empty">Loading…</p></div>
""", scripts=ORDER_JS + """<script>
window.pageInit = async function(c){
  await CrewOrders.statusDefs();
  var may = Crew.can('bookings.manage');
  var filter='today', rows=[];
  var LABEL={PENDING:'Pending',CONFIRMED:'Confirmed',SEATED:'Seated',
             COMPLETED:'Done',NO_SHOW:'No show',CANCELLED:'Cancelled'};

  function todayISO(){ var d=new Date(); d.setMinutes(d.getMinutes()-d.getTimezoneOffset());
    return d.toISOString().slice(0,10); }

  async function load(){
    var q=Crew.sb.from('bookings').select('*')
      .order('booking_date').order('booking_time');
    if(filter==='today') q=q.eq('booking_date',todayISO());
    else if(filter==='upcoming') q=q.gt('booking_date',todayISO());
    else if(filter==='pending') q=q.eq('status','PENDING');
    var r=await q;
    if(r.error){ document.getElementById('bk-list').innerHTML=
      '<p class="crew-empty">'+r.error.message+'</p>'; return; }
    rows=r.data||[];
  }

  function tabs(){
    document.getElementById('bk-tabs').innerHTML=
      [['today','Today'],['upcoming','Upcoming'],['pending','Awaiting confirmation'],['all','All']]
      .map(function(t){ return '<button class="bk-tab'+(filter===t[0]?' is-on':'')+
        '" data-f="'+t[0]+'">'+t[1]+'</button>'; }).join('');
    document.querySelectorAll('[data-f]').forEach(function(b){
      b.onclick=async function(){ filter=b.dataset.f; await load(); draw(); };});
  }

  function draw(){
    tabs();
    document.getElementById('bk-sub').textContent = rows.length
      ? rows.length+' booking'+(rows.length===1?'':'s')
      : 'Nothing in this view';
    if(!rows.length){ document.getElementById('bk-list').innerHTML=
      '<p class="crew-empty">No bookings here.</p>'; return; }

    // split by branch, same as orders — two rooms must never be conflated
    var ids=[]; rows.forEach(function(b){ if(ids.indexOf(b.restaurant_id)===-1) ids.push(b.restaurant_id); });
    ids.sort(function(a,b){return CrewOrders.restName(a).localeCompare(CrewOrders.restName(b));});
    document.getElementById('bk-list').innerHTML = ids.map(function(rid){
      var mine=rows.filter(function(b){return b.restaurant_id===rid;});
      return '<section class="obranch"><header class="obranch__h">'+
        '<h2>'+CrewOrders.esc(CrewOrders.restName(rid))+'</h2><span>'+mine.length+'</span></header>'+
        '<div class="bkgrid">'+mine.map(card).join('')+'</div></section>'; }).join('');

    document.querySelectorAll('[data-set]').forEach(function(b){
      b.onclick=async function(){
        var id=b.dataset.set, to=b.dataset.to;
        if(to==='CANCELLED' && !confirm('Cancel this booking?')) return;
        var u=await Crew.sb.from('bookings').update({status:to, handled_by:c.user.id}).eq('id',id);
        if(u.error) return alert(u.error.message);
        await load(); draw(); };});
  }

  function card(b){
    var t=b.booking_time.slice(0,5);
    var acts='';
    if(may){
      if(b.status==='PENDING')   acts='<button class="prim" data-set="'+b.id+'" data-to="CONFIRMED">Confirm</button>'+
                                      '<button data-set="'+b.id+'" data-to="CANCELLED">Cancel</button>';
      else if(b.status==='CONFIRMED') acts='<button class="prim" data-set="'+b.id+'" data-to="SEATED">Seat</button>'+
                                      '<button data-set="'+b.id+'" data-to="NO_SHOW">No show</button>';
      else if(b.status==='SEATED') acts='<button class="prim" data-set="'+b.id+'" data-to="COMPLETED">Complete</button>';
    }
    return '<article class="bkcard" data-s="'+b.status+'">'+
      '<div class="bkcard__h"><span class="bkcard__w">'+t+'</span>'+
        '<span class="ostat" style="background:'+
          ({PENDING:'#B4761B',CONFIRMED:'#2F6F4F',SEATED:'#39497C',COMPLETED:'#5A6070',
            NO_SHOW:'#B3261E',CANCELLED:'#B3261E'})[b.status]+'">'+LABEL[b.status]+'</span></div>'+
      '<dl><dt>Guest</dt><dd>'+CrewOrders.esc(b.guest_name)+'</dd>'+
        '<dt>Party</dt><dd>'+b.party_size+' &middot; '+CrewOrders.esc(b.booking_type)+'</dd>'+
        '<dt>Phone</dt><dd><a href="tel:'+CrewOrders.esc(b.guest_phone)+'">'+CrewOrders.esc(b.guest_phone)+'</a></dd>'+
        '<dt>Date</dt><dd>'+new Date(b.booking_date+'T12:00:00')
          .toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short'})+'</dd></dl>'+
      (b.notes?'<div class="ocard__note">'+CrewOrders.esc(b.notes)+'</div>':'')+
      '<span class="bkcard__r">Ref '+CrewOrders.esc(b.reference)+'</span>'+
      (acts?'<div class="bkcard__acts">'+acts+'</div>':'')+
    '</article>';
  }

  await load(); draw();
  Crew.sb.channel('crew-bookings')
    .on('postgres_changes',{event:'*',schema:'public',table:'bookings'},
        async function(){ await load(); draw(); }).subscribe();
};
</script>""")
print('crew: bookings')
