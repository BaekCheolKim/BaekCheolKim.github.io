// site.js: the homepage's "Latest" filters and search.
//
// How to edit:
// - Search: it loads search.json (written by build.py) on the first keystroke
//   and shows entries whose title, summary or text contain every typed word.
// - Type filters: the buttons above "Latest" carry data-kind="til" and so on;
//   build.py writes them, this file shows and hides the matching rows.
(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };
  var each = function (list, fn) { Array.prototype.forEach.call(list, fn); };
  var esc = function (s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  };
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var shortDate = function (iso) {   // 2026-11-25 -> 25 Nov 2026, as build.py writes it
    var p = iso.split('-');
    return parseInt(p[2], 10) + ' ' + MONTHS[parseInt(p[1], 10) - 1] + ' ' + p[0];
  };

  // ------------------------------------------------------------ "Latest": filters and search
  var q = $('q');
  var stream = $('stream');
  if (q && stream) {
    var LABEL = { til: 'TIL', article: 'Article', tool: 'Tool', work: 'Work' };
    var list = $('stream-list');
    var results = $('results');
    var empty = $('empty');
    var tabs = stream.querySelectorAll('.tabs button');
    var kind = 'all';
    var index = null;
    var loading = false;
    var timer = 0;

    // The first visible row of a list has no top border.
    var markFirst = function (rows) {
      var n = 0;
      each(rows, function (r) { r.classList.toggle('first', !r.hidden && n === 0); if (!r.hidden) n++; });
      return n;
    };

    // Used when search.json cannot be loaded, for example when a page is opened from disk.
    var domIndex = function () {
      var out = [];
      each(list.querySelectorAll('.row'), function (r) {
        var a = r.querySelector('.t');
        var meta = r.querySelector('.meta');
        out.push({ t: a.textContent, u: a.getAttribute('href'), k: r.getAttribute('data-kind'),
                   d: r.querySelector('time').getAttribute('datetime'), c: '',
                   s: meta ? meta.textContent : '', x: '' });
      });
      return out;
    };

    var row = function (d) {
      return '<li class="row" data-kind="' + esc(d.k) + '"><time datetime="' + esc(d.d) + '">' +
        esc(shortDate(d.d)) + '</time><span class="Label Label--' + esc(d.k) + '">' + (LABEL[d.k] || '') +
        '</span><div class="what"><a class="t" href="' + esc(d.u) + '">' + esc(d.t) + '</a>' +
        (d.s ? '<p class="meta">' + esc(d.s) + '</p>' : '') + '</div></li>';
    };

    var showStream = function () {
      results.hidden = true;
      list.hidden = false;
      var shown = 0;
      each(list.querySelectorAll('.month'), function (m) {
        var rows = m.querySelectorAll('.row');
        each(rows, function (r) { r.hidden = !(kind === 'all' || r.getAttribute('data-kind') === kind); });
        var n = markFirst(rows);
        m.hidden = n === 0;
        shown += n;
      });
      empty.hidden = shown > 0;
    };

    var showResults = function (words) {
      var hits = [];
      index.forEach(function (d) {
        if (kind !== 'all' && d.k !== kind) return;
        var title = d.t.toLowerCase();
        var hay = title + ' ' + d.s.toLowerCase() + ' ' + d.c.toLowerCase() + ' ' + d.x.toLowerCase();
        for (var i = 0; i < words.length; i++) if (hay.indexOf(words[i]) === -1) return;
        var score = 0;
        words.forEach(function (w) { if (title.indexOf(w) !== -1) score++; });
        hits.push({ d: d, score: score });
      });
      hits.sort(function (a, b) { return b.score - a.score || (a.d.d < b.d.d ? 1 : a.d.d > b.d.d ? -1 : 0); });
      results.innerHTML = hits.map(function (h) { return row(h.d); }).join('');
      markFirst(results.children);
      list.hidden = true;
      results.hidden = hits.length === 0;
      empty.hidden = hits.length > 0;
    };

    var apply = function () {
      var words = q.value.toLowerCase().split(/\s+/).filter(Boolean);
      if (!words.length) { showStream(); return; }
      if (index) { showResults(words); return; }
      if (loading) return;
      loading = true;
      fetch('search.json')
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (data) { index = data; })
        .catch(function () { index = domIndex(); })
        .then(apply);
    };

    each(tabs, function (b) {
      b.addEventListener('click', function () {
        kind = b.getAttribute('data-kind');
        each(tabs, function (t) { t.setAttribute('aria-pressed', String(t === b)); });
        apply();
      });
    });
    q.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(apply, 60); });
    q.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { q.value = ''; apply(); q.blur(); }
    });

    // "/" anywhere on the homepage jumps to the search box.
    document.addEventListener('keydown', function (e) {
      if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
      var t = e.target;
      if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT|BUTTON)$/.test(t.tagName))) return;
      e.preventDefault();
      q.focus();
    });
    // The header's Search link scrolls to the box instead of reloading the page.
    each(document.querySelectorAll('.head-aux a[href$="#search"]'), function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        q.focus();
        stream.scrollIntoView({ block: 'start' });
      });
    });
    if (location.hash === '#search') { q.focus(); stream.scrollIntoView({ block: 'start' }); }
  }
})();
