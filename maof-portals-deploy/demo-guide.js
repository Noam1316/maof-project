/* ════════════════════════════════════════════════════════════
   Maof Demo Guide — מסע מודרך אחד על פני כל הפורטלים
   נטען בכל פורטל. פעיל רק כש-?demo=1 קיים ב-URL.
   נושא candidate_id דרך כל השלבים (URL + localStorage).
   ════════════════════════════════════════════════════════════ */
(function () {
  var params = new URLSearchParams(location.search);
  if (params.get('demo') !== '1') return;            // demo mode only

  var step = parseInt(params.get('step') || '0', 10);
  if (isNaN(step) || step < 0) step = 0;

  // candidate_id from URL → persist to localStorage so it survives navigation
  var urlCid = params.get('candidate_id');
  if (urlCid) { try { localStorage.setItem('maof_candidate_id', urlCid); } catch (e) {} }

  var STEPS = [
    { portal: 'soldiers',  title: 'רישום מועמד',
      text: 'מלאו שם · עיר · יחידה · מקצוע ולחצו "שמור". נוצר מועמד אמיתי ב-Supabase.',
      next: 'שמרתי — המשך ←',
      onShow: function () { if (window.showScreen) { try { showScreen('settings'); } catch (e) {} } } },
    { portal: 'eli5',      title: 'מבחן ELI5 · ציון A (הוראה)',
      text: 'מבחן יכולת הסבר. בסיום — ציון ההוראה נשמר על המועמד.',
      next: 'סיימתי — המשך ←' },
    { portal: 'tech-test', title: 'מבחן טכני · ציון B (הייטק)',
      text: '3 שכבות: הגיון · קוד · ארכיטקטורה. מזין את ציון ה-Tech Skills.',
      next: 'סיימתי — המשך ←' },
    { portal: 'education',  title: 'צד מערכת החינוך',
      text: 'המועמד שיצרתם מופיע כאן חי, עם הציונים — מדורג מול הצרכים.',
      next: 'ראיתי — המשך ←' },
    { portal: 'companies',  title: 'צד החברות',
      text: 'אותו מועמד עם score_b אמיתי. לחצו "שבץ" כדי לסגור שיבוץ.',
      next: 'שיבצתי — המשך ←' },
    { portal: '',           title: 'הלולאה נסגרה ✓',
      text: 'השיבוץ נשמר ב-Supabase ומופיע בכל הפורטלים. מועמד → הערכה → שיבוץ — לולאה מלאה.',
      next: 'סיים סיור' }
  ];

  var cur = STEPS[step] || STEPS[0];

  function cid() {
    try { return localStorage.getItem('maof_candidate_id') || ''; } catch (e) { return ''; }
  }

  function go(n) {
    if (n >= STEPS.length) { exitTour(); return; }
    var s = STEPS[n];
    var c = cid();
    var url = '/' + (s.portal ? s.portal + '/' : '') + '?demo=1&step=' + n;
    if (c) url += '&candidate_id=' + encodeURIComponent(c);
    location.href = url;
  }

  function exitTour() {
    location.href = location.pathname;   // strip ?demo params, stay on page
  }

  function render() {
    var total = STEPS.length;
    var bar = document.createElement('div');
    bar.id = 'maof-demo-bar';
    bar.setAttribute('dir', 'rtl');
    bar.style.cssText =
      'position:fixed;bottom:0;left:0;right:0;z-index:99999;' +
      'background:#0a1628;border-top:2px solid #a855f7;' +
      'box-shadow:0 -6px 24px rgba(0,0,0,.45);' +
      'font-family:Heebo,system-ui,Arial,sans-serif;color:#f1f5f9;' +
      'padding:12px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap';

    var chip = '<div style="display:flex;align-items:center;gap:8px;flex-shrink:0">' +
      '<span style="font-size:18px">🎬</span>' +
      '<span style="font-size:11px;font-weight:700;color:#a855f7;font-family:monospace;letter-spacing:1px">סיור מעוף</span>' +
      '<span style="font-size:11px;color:#64748b;font-family:monospace">שלב ' + (step + 1) + '/' + total + '</span>' +
      '</div>';

    var body = '<div style="flex:1;min-width:200px">' +
      '<div style="font-size:14px;font-weight:700;margin-bottom:2px">' + cur.title + '</div>' +
      '<div style="font-size:12px;color:#94a3b8;line-height:1.4">' + cur.text + '</div>' +
      '</div>';

    var nextBtn = '<button id="maof-demo-next" style="flex-shrink:0;background:linear-gradient(135deg,#a855f7,#7aa2f7);' +
      'border:none;border-radius:10px;color:#fff;font-family:Heebo,system-ui,Arial;font-size:14px;font-weight:600;' +
      'padding:10px 22px;cursor:pointer;white-space:nowrap">' + cur.next + '</button>';

    var exitBtn = '<button id="maof-demo-exit" title="צא מהסיור" style="flex-shrink:0;background:transparent;' +
      'border:1px solid #334155;border-radius:8px;color:#64748b;font-size:13px;padding:8px 12px;cursor:pointer">✕</button>';

    // progress dots
    var dots = '<div style="display:flex;gap:5px;flex-shrink:0">';
    for (var i = 0; i < total; i++) {
      dots += '<span style="width:7px;height:7px;border-radius:50%;background:' +
        (i < step ? '#22c55e' : i === step ? '#a855f7' : '#334155') + '"></span>';
    }
    dots += '</div>';

    bar.innerHTML = chip + body + dots + nextBtn + exitBtn;
    document.body.appendChild(bar);
    document.body.style.paddingBottom = (bar.offsetHeight + 8) + 'px';

    document.getElementById('maof-demo-next').onclick = function () { go(step + 1); };
    document.getElementById('maof-demo-exit').onclick = exitTour;

    if (typeof cur.onShow === 'function') { setTimeout(cur.onShow, 400); }
  }

  if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', render);
  } else {
    render();
  }
})();
