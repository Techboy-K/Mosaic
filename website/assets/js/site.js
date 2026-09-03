/* Shared behaviour: sticky header, mobile drawer, scroll reveals, counters. */
(function () {
  'use strict';
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* sticky header */
  var head = document.querySelector('.site-head');
  if (head) {
    var onScroll = function () { head.classList.toggle('is-stuck', scrollY > 40); };
    addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }

  /* mobile drawer */
  var drawer = document.getElementById('drawer'),
      open   = document.querySelector('.nav-toggle'),
      close  = document.querySelector('[data-drawer-close]');
  function setDrawer(on) {
    if (!drawer) return;
    drawer.classList.toggle('is-open', on);
    document.body.style.overflow = on ? 'hidden' : '';
    if (open) open.setAttribute('aria-expanded', String(on));
    (on ? close : open) && (on ? close : open).focus();
  }
  open  && open.addEventListener('click', function () { setDrawer(true); });
  close && close.addEventListener('click', function () { setDrawer(false); });
  drawer && drawer.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () { setDrawer(false); });
  });
  addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && drawer && drawer.classList.contains('is-open')) setDrawer(false);
  });

  /* reveal on scroll */
  var rv = document.querySelectorAll('.rv');
  if (rv.length) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.14, rootMargin: '0px 0px -6% 0px' });
    rv.forEach(function (el, i) { el.style.transitionDelay = (i % 4) * 70 + 'ms'; io.observe(el); });
  }

  /* count-up */
  var counters = document.querySelectorAll('[data-count]');
  if (counters.length) {
    var ease = function (t) { return t < .5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2; };
    var cio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        cio.unobserve(e.target);
        var el = e.target, to = +el.dataset.count;
        if (reduce) { el.textContent = to; return; }
        var t0 = performance.now();
        (function step(t) {
          var k = Math.min((t - t0) / 1300, 1);
          el.textContent = Math.round(ease(k) * to);
          if (k < 1) requestAnimationFrame(step);
        })(t0);
      });
    }, { threshold: .5 });
    counters.forEach(function (el) { cio.observe(el); });
  }

  /* in-page anchors */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var id = a.getAttribute('href');
      if (id === '#' || id.length < 2) return;
      var t = document.querySelector(id);
      if (!t) return;
      e.preventDefault();
      t.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    });
  });
})();
