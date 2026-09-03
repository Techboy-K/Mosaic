/* Home page: scroll-scrubbed hero, WebGL dish carousel, scroll-scrubbed story film. */
(function () {
  'use strict';
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var clamp = function (v,a,b) { return v<a?a:v>b?b:v; };
  var lerp  = function (a,b,t) { return a + (b-a)*t; };

  function progress(el) {
    var r = el.getBoundingClientRect(), span = r.height - innerHeight;
    return span <= 0 ? clamp(-r.top / Math.max(1, r.height), 0, 1)
                     : clamp(-r.top / span, 0, 1);
  }
  function nearView(el, m) {
    var r = el.getBoundingClientRect(); m = m || 400;
    return r.bottom > -m && r.top < innerHeight + m;
  }

  /* ---------------------------------------------------------------- frame film
     A folder of stills drawn to a canvas and stepped by scroll position. Scrubs
     far more reliably than seeking a <video>, and each frame is a normal image
     the browser can cache. */
  function FrameFilm(canvas, dir, count, onFirst) {
    var ctx = canvas.getContext('2d', { alpha: false });
    var frames = new Array(count), loaded = 0, ready = false, W = 1440, H = 810;

    function paint(i) {
      var img = frames[i];
      if (!img || !img.complete || !img.naturalWidth) return;
      var cw = canvas.width, ch = canvas.height;
      var s = Math.max(cw / img.naturalWidth, ch / img.naturalHeight);
      var dw = img.naturalWidth * s, dh = img.naturalHeight * s;
      ctx.drawImage(img, (cw - dw) / 2, (ch - dh) / 2, dw, dh);
    }
    function nearest(i) {           /* fall back to the closest frame we have */
      for (var d = 0; d < count; d++) {
        if (frames[i-d] && frames[i-d].complete) return i-d;
        if (frames[i+d] && frames[i+d].complete) return i+d;
      }
      return -1;
    }
    this.size = function () {
      var dpr = Math.min(devicePixelRatio || 1, 2);
      canvas.width  = Math.max(1, Math.round(canvas.clientWidth  * dpr));
      canvas.height = Math.max(1, Math.round(canvas.clientHeight * dpr));
    };
    this.draw = function (p) {
      if (!canvas.width) return;
      if (!ready) { ctx.fillStyle = '#0C0E16'; ctx.fillRect(0,0,canvas.width,canvas.height); return; }
      var i = nearest(clamp(Math.round(p * (count - 1)), 0, count - 1));
      if (i >= 0) paint(i);
    };
    this.load = function () {
      for (var i = 0; i < count; i++) {
        (function (i) {
          var img = new Image();
          img.decoding = 'async';
          img.onload = function () {
            loaded++;
            if (!ready) { ready = true; onFirst && onFirst(); }
          };
          img.onerror = function () { loaded++; };
          img.src = dir + 'f' + String(i).padStart(3, '0') + '.webp';
          frames[i] = img;
        })(i);
      }
    };
  }

  /* ---------------------------------------------------------------- hero */
  var heroSec = document.getElementById('hero');
  var heroCv  = document.getElementById('hero-film');
  var heroCopy= document.getElementById('hero-copy');
  var heroCue = document.getElementById('hero-cue');
  var heroFilm;
  if (heroSec && heroCv) {
    heroFilm = new FrameFilm(heroCv, 'assets/video/hero/', 72, function () {
      heroFilm.size(); heroFilm.draw(progress(heroSec));
      heroSec.classList.add('is-ready');
    });
    heroFilm.size(); heroFilm.load();
  }

  /* ---------------------------------------------------------------- story film */
  var storySec = document.getElementById('story-film-sec');
  var storyCv  = document.getElementById('story-film');
  var storyFilm, lines = [];
  if (storySec && storyCv) {
    lines = [].slice.call(storySec.querySelectorAll('.film-line'));
    storyFilm = new FrameFilm(storyCv, 'assets/video/about/', 60, function () {
      storyFilm.size(); storyFilm.draw(progress(storySec));
    });
    storyFilm.size();
    /* only start pulling 2.6 MB of stills once the section is in reach */
    new IntersectionObserver(function (es, obs) {
      if (es[0].isIntersecting) { storyFilm.load(); obs.disconnect(); }
    }, { rootMargin: '900px' }).observe(storySec);
  }

  /* ---------------------------------------------------------------- 3D dishes */
  var dishSec = document.getElementById('dishes');
  var GL = null, dishData = [], smooth = 0, spin = 0, lastT = performance.now();

  function initDishes() {
    if (!dishSec || typeof THREE === 'undefined') return;
    var canvas = document.getElementById('dish-gl');
    dishData = JSON.parse(dishSec.dataset.dishes || '[]');
    if (!canvas || !dishData.length) return;

    var rend = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    rend.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    rend.outputEncoding = THREE.sRGBEncoding;
    /* No tone mapping. These meshes are photogrammetric: the dish photograph's own
       lighting is already baked into the base colour, so filmic mapping just
       desaturates food that is meant to look hot and crisp. */
    rend.toneMapping = THREE.NoToneMapping;

    var scene = new THREE.Scene();
    var cam = new THREE.PerspectiveCamera(32, 1, 0.05, 100);
    cam.position.set(0, 1.30, 5.4); cam.lookAt(0, 0.34, 0);

    /* A small procedural studio, pre-filtered into an environment map. This is what
       makes the glaze on the food read as wet rather than painted on. */
    (function () {
      var c = document.createElement('canvas'); c.width = 512; c.height = 256;
      var x = c.getContext('2d');
      var g = x.createLinearGradient(0, 0, 0, 256);
      g.addColorStop(0, '#ffffff'); g.addColorStop(.42, '#d8cfc2');
      g.addColorStop(.55, '#5a5348'); g.addColorStop(1, '#14161f');
      x.fillStyle = g; x.fillRect(0, 0, 512, 256);
      x.fillStyle = 'rgba(255,250,240,.95)'; x.beginPath(); x.ellipse(150, 60, 110, 46, 0, 0, 7); x.fill();
      x.fillStyle = 'rgba(255,236,210,.55)'; x.beginPath(); x.ellipse(390, 80, 80, 34, 0, 0, 7); x.fill();
      var t = new THREE.CanvasTexture(c);
      t.mapping = THREE.EquirectangularReflectionMapping;
      t.encoding = THREE.sRGBEncoding;
      var pm = new THREE.PMREMGenerator(rend); pm.compileEquirectangularShader();
      scene.environment = pm.fromEquirectangular(t).texture;
      t.dispose(); pm.dispose();
    })();

    /* Ambient carries almost all of it, so the baked albedo reads at full saturation.
       A whisper of key light and environment restores form without re-lighting the food. */
    scene.add(new THREE.AmbientLight(0xffffff, 0.90));
    var key = new THREE.DirectionalLight(0xFFFAF2, 0.42); key.position.set(2.2, 4.6, 3.4); scene.add(key);
    var rim = new THREE.DirectionalLight(0xF0E2D0, 0.20); rim.position.set(-3.6, 1.8, -2.4); scene.add(rim);

    /* soft contact shadow */
    var sc = document.createElement('canvas'); sc.width = sc.height = 256;
    var g2 = sc.getContext('2d'), grd = g2.createRadialGradient(128,128,6,128,128,124);
    grd.addColorStop(0,'rgba(0,0,0,.5)'); grd.addColorStop(.55,'rgba(0,0,0,.2)'); grd.addColorStop(1,'rgba(0,0,0,0)');
    g2.fillStyle = grd; g2.fillRect(0,0,256,256);
    var shTex = new THREE.CanvasTexture(sc);

    var loader = new THREE.GLTFLoader();
    var slots = dishData.map(function (d, i) {
      var outer = new THREE.Group();
      var shadow = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 2.6),
        new THREE.MeshBasicMaterial({ map: shTex, transparent: true, depthWrite: false }));
      shadow.rotation.x = -Math.PI / 2; shadow.position.y = -0.70;
      outer.add(shadow); outer.visible = false; scene.add(outer);
      return { outer: outer, shadow: shadow, model: null, loading: false, spinner: null };
    });

    function ensure(i) {
      var s = slots[i];
      if (s.model || s.loading) return;
      s.loading = true;
      loader.load(dishData[i].model, function (gltf) {
        var o = gltf.scene;
        var box = new THREE.Box3().setFromObject(o);
        var size = box.getSize(new THREE.Vector3());
        var ctr  = box.getCenter(new THREE.Vector3());
        var k = 1.75 / Math.max(size.x, size.y, size.z);
        o.scale.setScalar(k);
        o.position.set(-ctr.x * k, -ctr.y * k, -ctr.z * k);
        o.traverse(function (n) {
          if (!n.isMesh) return;
          var m = n.material;
          m.envMapIntensity = 0.16;
          /* only impose values where the mesh shipped no map of its own */
          /* the generated roughness map has glossy patches that read as white
             speckles on the plate, so floor the roughness and kill metalness */
          /* Keep the generated roughness map — it is what separates the glossy
             yogurt from the dry bread — but floor it so the plate stops throwing
             white specular speckles, and drop metalness entirely: no food is metal. */
          m.roughness = Math.max(m.roughness || 0, 0.55);
          m.metalness = 0.0;
          m.metalnessMap = null;
          n.frustumCulled = false;
        });
        var pivot = new THREE.Group(); pivot.add(o);
        s.spinner = pivot; s.outer.add(pivot); s.model = o;
        dishSec.classList.add('has-3d');
      }, undefined, function () { s.loading = false; });
    }

    GL = {
      rend: rend, scene: scene, cam: cam, canvas: canvas, slots: slots,
      size: function () {
        var w = canvas.clientWidth, h = canvas.clientHeight;
        if (!w || !h) return;
        rend.setSize(w, h, false);
        cam.aspect = w / h;
        cam.position.z = w < 720 ? 7.4 : (w < 1100 ? 6.2 : 5.4);
        cam.updateProjectionMatrix();
      },
      draw: function (p, dt) {
        spin += dt;
        var n = dishData.length, pos = p * (n - 1);
        for (var i = 0; i < n; i++) {
          var s = slots[i], d = i - pos, ad = Math.abs(d);
          if (ad < 2.6) ensure(i);
          var vis = ad < 2.4;
          s.outer.visible = vis;
          if (!vis) continue;
          s.outer.position.set(d * 3.05, 0.42 - ad * 0.06, -ad * 1.5);
          s.outer.rotation.y = -d * 0.40;
          var k = 1 - Math.min(ad, 2) * 0.26;
          s.outer.scale.setScalar(k);
          var o = clamp(1 - Math.min(ad, 2.2) * 0.44, 0, 1);
          s.shadow.material.opacity = o * 0.85;
          if (s.spinner) s.spinner.rotation.y = reduce ? 0 : spin * 0.22 * clamp(1 - ad, 0, 1);
          if (s.model) s.model.traverse(function (m) {
            if (m.isMesh) { m.material.transparent = o < 0.99; m.material.opacity = o; }
          });
        }
        rend.render(scene, cam);
      }
    };
    GL.size();
    dishSec.classList.add('gl-on');
  }

  /* dish copy */
  var dCat = document.getElementById('dish-cat'), dName = document.getElementById('dish-name'),
      dDesc = document.getElementById('dish-desc'), dPrice = document.getElementById('dish-price'),
      dLink = document.getElementById('dish-link'), dDots = document.getElementById('dish-dots'),
      curDish = -1;

  function setDish(i) {
    if (i === curDish || !dishData[i]) return;
    curDish = i;
    var d = dishData[i];
    dCat.textContent = d.cat + (d.signature ? '  ·  Signature' : '');
    dName.textContent = d.name;
    dDesc.textContent = d.desc;
    dPrice.textContent = d.price;
    if (dLink) dLink.href = 'menu.html#dish-' + d.id;
    if (dDots) [].forEach.call(dDots.children, function (b, k) {
      b.classList.toggle('is-on', k === i);
      b.setAttribute('aria-current', k === i ? 'true' : 'false');
    });
    [dCat, dName, dDesc, dPrice].forEach(function (el) {
      if (!el) return;
      el.style.transition = 'none'; el.style.opacity = '0'; el.style.transform = 'translateY(12px)';
      void el.offsetWidth;
      el.style.transition = 'opacity .42s cubic-bezier(.16,1,.3,1), transform .42s cubic-bezier(.16,1,.3,1)';
      el.style.opacity = '1'; el.style.transform = 'none';
    });
  }

  /* ---------------------------------------------------------------- loop */
  function frame(now) {
    var dt = Math.min((now - lastT) / 1000, 0.05); lastT = now;

    if (heroSec && heroFilm && nearView(heroSec)) {
      var hp = progress(heroSec);
      heroFilm.draw(hp);
      var out = clamp((hp - 0.55) / 0.40, 0, 1);
      heroCopy.style.opacity = String(1 - out);
      heroCopy.style.transform = 'translateY(' + (-out * 60) + 'px)';
      if (heroCue) heroCue.style.opacity = String(1 - clamp(hp / 0.09, 0, 1));
    }

    if (dishSec && GL && nearView(dishSec)) {
      var mp = progress(dishSec);
      smooth = lerp(smooth, mp, reduce ? 1 : 0.11);
      GL.draw(smooth, dt);
      setDish(clamp(Math.round(smooth * (dishData.length - 1)), 0, dishData.length - 1));
    }

    if (storySec && storyFilm && nearView(storySec)) {
      var sp = progress(storySec);
      storyFilm.draw(clamp(sp * 1.05, 0, 1));
      var seg = 1 / lines.length;
      lines.forEach(function (el, i) {
        var local = clamp((sp - i * seg) / seg, 0, 1);
        var into = clamp(local / 0.26, 0, 1), away = clamp((local - 0.74) / 0.26, 0, 1);
        el.style.opacity = String(into * (1 - away));
        el.style.transform = 'translateY(' + ((1 - into) * 30 - away * 30) + 'px)';
      });
    }
    requestAnimationFrame(frame);
  }

  function resize() {
    heroFilm  && (heroFilm.size(),  heroFilm.draw(progress(heroSec)));
    storyFilm && (storyFilm.size(), storyFilm.draw(progress(storySec)));
    GL && GL.size();
  }
  addEventListener('resize', resize, { passive: true });

  initDishes();
  requestAnimationFrame(frame);
})();
