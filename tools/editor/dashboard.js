/* Dashboard: add a post from a release or as an announcement, and delete one. */

(function () {
  var mode = 'import';

  function el(id) { return document.getElementById(id); }

  function setMode(next) {
    mode = next;
    [].slice.call(document.querySelectorAll('.tab')).forEach(function (t) {
      t.classList.toggle('on', t.dataset.mode === next);
    });
    [].slice.call(document.querySelectorAll('.pane')).forEach(function (p) {
      p.hidden = p.dataset.pane !== next;
    });
    err('');
    var focus = next === 'import' ? el('a_url') : el('a_title');
    if (focus) focus.focus();
  }

  function err(msg) {
    var e = el('adderr');
    e.textContent = msg || '';
    e.hidden = !msg;
  }

  function busy(button, on, label) {
    button.disabled = on;
    button.textContent = on ? label : button.dataset.label;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var addDlg = el('adddlg');
    var delDlg = el('deldlg');
    var addGo = el('addgo');
    var delGo = el('delgo');
    if (delGo) delGo.dataset.label = delGo.textContent;

    if (addDlg && addGo) {
      addGo.dataset.label = addGo.textContent;
      el('addbtn').addEventListener('click', function () {
        err('');
        addDlg.showModal();
        setMode('import');
      });
      el('addcancel').addEventListener('click', function () { addDlg.close(); });
      [].slice.call(document.querySelectorAll('.tab')).forEach(function (t) {
        t.addEventListener('click', function () { setMode(t.dataset.mode); });
      });
      addGo.addEventListener('click', onAdd);
    }

    function onAdd() {
      var payload = { mode: mode };
      if (mode === 'import') {
        payload.url = el('a_url').value.trim();
        payload.track = el('a_track').value;
        if (!payload.url) return err('Paste a release URL first.');
      } else {
        payload.title = el('a_title').value.trim();
        if (!payload.title) return err('Give the announcement a title.');
      }
      err('');
      busy(addGo, true, mode === 'import' ? 'Fetching...' : 'Creating...');
      Admin.post('/admin/api/create', payload).then(function (res) {
        /* land straight in the editor: a new post always needs writing */
        if (res.warnings && res.warnings.length) {
          try { sessionStorage.setItem('addWarnings', res.warnings.join(' ')); }
          catch (e) { /* private mode, not worth failing over */ }
        }
        location.href = '/admin/post/' + encodeURIComponent(res.slug);
      }).catch(function (e) {
        busy(addGo, false);
        err(e.message);
      });
    }

    if (!delDlg || !delGo) return;

    var pending = null;
    [].slice.call(document.querySelectorAll('.del')).forEach(function (b) {
      b.addEventListener('click', function () {
        pending = { kind: b.dataset.kind, slug: b.dataset.slug };
        el('delwhat').textContent = '"' + b.dataset.title + '"';
        delDlg.showModal();
      });
    });
    el('delcancel').addEventListener('click', function () {
      pending = null;
      delDlg.close();
    });
    delGo.addEventListener('click', function () {
      if (!pending) return;
      busy(delGo, true, 'Deleting...');
      Admin.post('/admin/api/delete', pending).then(function () {
        location.reload();
      }).catch(function (e) {
        busy(delGo, false);
        el('delwhat').textContent = e.message;
      });
    });
  });
})();
