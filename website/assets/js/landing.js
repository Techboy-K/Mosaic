/* Scroll-driven landing film.
   One video runs behind every section; scroll position maps to video time.
   Each overlay is pinned to the moment its subject is actually on screen, and
   sits on the side of the frame the dish is NOT occupying. */
(function (w, d) {
  'use strict';
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var clamp = function (v,a,b){ return v<a?a:v>b?b:v; };
  var lerp  = function (a,b,t){ return a+(b-a)*t; };

  var vid   = d.getElementById('film');
  var stage = d.getElementById('stage');
  var track = d.getElementById('track');
  if (!vid || !track) return;

  /* Beats read off the cut: [enter, hold-start, hold-end, exit] in seconds.
     The hold is where the shot is still, so copy appears then and only then. */
  var BEATS = [
    { id:'welcome',  in:0.0,  a:0.4,  b:2.6,  out:3.4 },
    { id:'table',    in:3.4,  a:4.0,  b:5.6,  out:7.2 },
    { id:'d1',       in:7.6,  a:8.1,  b:9.9,  out:10.4 },
    { id:'d2',       in:10.4, a:10.9, b:11.9, out:12.3 },
    { id:'d3',       in:12.3, a:12.8, b:14.1, out:14.6 },
    { id:'d4',       in:14.6, a:15.0, b:16.2, out:16.7 },
    { id:'d5',       in:16.7, a:17.1, b:18.1, out:18.6 },
    { id:'d6',       in:18.6, a:19.0, b:20.0, out:20.5 },
    { id:'menucta',  in:20.5, a:20.9, b:21.8, out:22.2 },
    { id:'awards',   in:22.2, a:22.7, b:24.0, out:24.4 },
    { id:'mosaic',   in:24.4, a:24.9, b:25.8, out:26.15 },
    { id:'spread',   in:26.15,a:26.8, b:28.1, out:28.45 },
    { id:'book',     in:28.45,a:29.4, b:33.0, out:33.34 }
  ];

  var DUR = 33.34, target = 0, current = 0, ready = false;

  function onMeta() {
    DUR = vid.duration || DUR;
    ready = true;
    d.body.classList.add('film-ready');
    paint(progress());
  }
  /* metadata can already be in by the time this runs, in which case the event
     never fires again — check readyState rather than relying on the listener */
  if (vid.readyState >= 1) onMeta();
  vid.addEventListener('loadedmetadata', onMeta);
  vid.addEventListener('error', function () {
    d.body.classList.add('film-failed');   // poster stays, copy still readable
  });
  /* a paused video still needs one play() on some browsers before it will seek */
  vid.play().then(function(){ vid.pause(); }).catch(function(){});

  function progress() {
    var span = track.offsetHeight - innerHeight;
    return span <= 0 ? 0 : clamp(-track.getBoundingClientRect().top / span, 0, 1);
  }

  function paint(p) {
    var t = p * DUR;
    BEATS.forEach(function (b) {
      var el = d.getElementById('beat-' + b.id);
      if (!el) return;
      var o;
      if (t < b.in || t > b.out) o = 0;
      else if (t < b.a) o = (t - b.in) / Math.max(0.01, b.a - b.in);
      else if (t <= b.b) o = 1;
      else o = 1 - (t - b.b) / Math.max(0.01, b.out - b.b);
      o = clamp(o, 0, 1);
      el.style.opacity = o;
      el.style.transform = 'translateY(' + ((1 - o) * 18) + 'px)';
      el.style.pointerEvents = o > 0.6 ? 'auto' : 'none';
      el.setAttribute('aria-hidden', o < 0.15 ? 'true' : 'false');
    });
    var cue = d.getElementById('film-cue');
    if (cue) cue.style.opacity = clamp(1 - p / 0.04, 0, 1);
    var bar = d.getElementById('film-bar');
    if (bar) bar.style.transform = 'scaleX(' + p + ')';
  }

  function frame() {
    var p = progress();
    target = p * DUR;
    current = reduce ? target : lerp(current, target, 0.12);
    if (ready && Math.abs(current - (vid.currentTime || 0)) > 0.012) {
      try { vid.currentTime = current; } catch (e) {}
    }
    paint(p);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  /* jump straight to a beat from the section rail */
  d.querySelectorAll('[data-jump]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var b = BEATS.filter(function (x) { return x.id === a.dataset.jump; })[0];
      if (!b) return;
      var mid = (b.a + b.b) / 2 / DUR;
      var span = track.offsetHeight - innerHeight;
      scrollTo({ top: track.offsetTop + mid * span, behavior: reduce ? 'auto' : 'smooth' });
    });
  });
})(window, document);
