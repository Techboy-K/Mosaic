/* Full menu — filtered card grid. One category at a time keeps every view short
   and scannable; search cuts across all 250 dishes. */
(function () {
  'use strict';
  var root    = document.getElementById('menu-root');
  if (!root) return;
  var railEl  = document.getElementById('menu-rail');
  var chipEl  = document.getElementById('menu-chips');
  var searchEl= document.getElementById('menu-search');
  var countEl = document.getElementById('menu-count');
  var titleEl = document.getElementById('menu-title');
  var subEl   = document.getElementById('menu-sub');
  var emptyEl = document.getElementById('menu-empty');
  var clearEl = document.getElementById('menu-clear');

  var DATA = null, current = 'all', query = '';
  var PAGE = 48, shown = PAGE;
  var moreWrap = document.getElementById('menu-more-wrap');
  var moreBtn  = document.getElementById('menu-more');

  var esc = function (s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' })[c];
    });
  };

  function allItems() {
    return DATA.categories.reduce(function (a, c) {
      return a.concat(c.items.map(function (i) { return Object.assign({ _cat: c.name }, i); }));
    }, []);
  }

  function visible() {
    var q = query.trim().toLowerCase();
    var pool = q || current === 'all'
      ? allItems()
      : (DATA.categories.filter(function (c) { return c.slug === current; })[0] || { items: [] })
          .items.map(function (i) { return Object.assign({ _cat: '' }, i); });
    if (!q) return pool;
    return pool.filter(function (it) {
      return it.name.toLowerCase().indexOf(q) > -1 ||
             (it.desc || '').toLowerCase().indexOf(q) > -1;
    });
  }

  function card(it) {
    var img = it.img
      ? '<img class="dish__img" src="' + it.img + '" alt="' + esc(it.name) + '" loading="lazy">'
      : '<span class="dish__img dish__img--none" aria-hidden="true"></span>';
    return '<article class="dish" id="dish-' + it.id + '">' +
      '<div class="dish__media">' + img +
        (it._cat ? '<span class="dish__tag">' + esc(it._cat) + '</span>' : '') +
      '</div>' +
      '<div class="dish__body">' +
        '<div class="dish__row"><h3>' + esc(it.name) + '</h3>' +
        '<span class="dish__price num">' + Number(it.price).toFixed(0) + '<i>AED</i></span></div>' +
        (it.desc ? '<p>' + esc(it.desc) + '</p>' : '') +
        '<button class="dish__add" type="button" data-add data-id="' + it.id +
        '" data-name="' + esc(it.name) + '" data-price="' + it.price + '">Add to order</button>' +
      '</div></article>';
  }

  function paint() {
    var items = visible();
    var cat = DATA.categories.filter(function (c) { return c.slug === current; })[0];

    titleEl.textContent = query ? 'Search results'
                                : (current === 'all' ? 'The whole menu' : cat.name);
    subEl.textContent   = query ? '“' + query + '”'
                                : (current === 'all' ? 'All 250 dishes, every category'
                                                     : cat.items.length + ' dishes');
    countEl.textContent = items.length;
    clearEl.hidden = !query;

    var slice = items.slice(0, shown);
    root.innerHTML = slice.map(card).join('');
    emptyEl.hidden = items.length > 0;
    if (moreWrap) {
      moreWrap.hidden = items.length <= shown;
      if (moreBtn) moreBtn.textContent = 'Show more dishes (' + (items.length - shown) + ' left)';
    }

    railEl.querySelectorAll('[data-slug]').forEach(function (b) {
      var on = !query && b.dataset.slug === current;
      b.classList.toggle('is-on', on);
      b.setAttribute('aria-current', on ? 'true' : 'false');
    });
    chipEl.querySelectorAll('[data-slug]').forEach(function (b) {
      b.classList.toggle('is-on', !query && b.dataset.slug === current);
    });
  }

  function buildNav() {
    var rows = [{ slug: 'all', name: 'All dishes', n: allItems().length }]
      .concat(DATA.categories.map(function (c) {
        return { slug: c.slug, name: c.name, n: c.items.length };
      }));
    railEl.innerHTML = rows.map(function (r) {
      return '<button class="rail__item" type="button" data-slug="' + r.slug + '">' +
             '<span>' + esc(r.name) + '</span><span class="num">' + r.n + '</span></button>';
    }).join('');
    chipEl.innerHTML = rows.map(function (r) {
      return '<button class="chip" type="button" data-slug="' + r.slug + '">' +
             esc(r.name) + '<span class="num">' + r.n + '</span></button>';
    }).join('');

    [railEl, chipEl].forEach(function (host) {
      host.addEventListener('click', function (e) {
        var b = e.target.closest('[data-slug]');
        if (!b) return;
        current = b.dataset.slug;
        query = ''; searchEl.value = ''; shown = PAGE;
        paint();
        document.getElementById('menu-main').scrollIntoView({ block: 'start', behavior: 'smooth' });
      });
    });
  }

  fetch('data/menu.json').then(function (r) { return r.json(); }).then(function (d) {
    DATA = d;
    buildNav();
    /* deep link from the home page carousel */
    var m = location.hash.match(/^#dish-(\d+)$/);
    if (m) {
      var id = +m[1];
      d.categories.some(function (c) {
        if (c.items.some(function (i) { return i.id === id; })) { current = c.slug; return true; }
      });
    }
    if (m) shown = 999;
    paint();
    if (m) {
      var t = document.getElementById('dish-' + m[1]);
      if (t) { t.scrollIntoView({ block: 'center' }); t.classList.add('is-target'); }
    }
  }).catch(function () {
    root.innerHTML = '<p class="lede">The menu could not be loaded. Please refresh, or call ' +
                     '<a href="tel:600580580">600 580 580</a>.</p>';
  });

  moreBtn && moreBtn.addEventListener('click', function () {
    shown += PAGE; paint();
    var cards = root.querySelectorAll('.dish');
    var target = cards[Math.max(0, shown - PAGE)];
    if (target) target.scrollIntoView({ block: 'center', behavior: 'smooth' });
  });

  var t;
  searchEl.addEventListener('input', function () {
    clearTimeout(t);
    t = setTimeout(function () { query = searchEl.value; shown = PAGE; paint(); }, 130);
  });
  clearEl.addEventListener('click', function () {
    query = ''; searchEl.value = ''; shown = PAGE; searchEl.focus(); paint();
  });
})();
