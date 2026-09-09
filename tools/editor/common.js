/* Shared bits for the admin pages. */

window.Admin = (function () {
  var statusEl = null;
  var saveEl = null;

  function el(id) { return document.getElementById(id); }

  function status(msg, kind) {
    if (!statusEl) statusEl = el('status');
    if (!statusEl) return;
    statusEl.textContent = msg || '';
    statusEl.className = kind || '';
  }

  function refreshPreview() {
    var f = el('preview');
    if (!f) return;
    // cache-bust so the rebuilt page is what loads, not the one already there
    var src = f.getAttribute('src').split('#')[0].split('&t=')[0];
    f.setAttribute('src', src + '&t=' + Date.now());
  }

  function post(url, payload) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(function (r) {
      return r.json().then(function (j) {
        if (!r.ok || j.error) throw new Error(j.error || ('HTTP ' + r.status));
        return j;
      });
    });
  }

  /** Wire the save button to a function returning the payload. */
  function onSave(url, buildPayload, after) {
    saveEl = el('save');
    if (!saveEl) return;
    saveEl.addEventListener('click', function () {
      saveEl.disabled = true;
      status('Saving...');
      Promise.resolve(buildPayload()).then(function (payload) {
        return post(url, payload);
      }).then(function (res) {
        status('Saved, rebuilt in ' + res.ms + ' ms', 'ok');
        refreshPreview();
        if (after) after();
      }).catch(function (err) {
        status(err.message, 'err');
      }).then(function () {
        saveEl.disabled = false;
      });
    });
  }

  function warnOnLeave(isDirty) {
    window.addEventListener('beforeunload', function (e) {
      if (isDirty()) { e.preventDefault(); e.returnValue = ''; }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var r = el('refresh');
    if (r) r.addEventListener('click', refreshPreview);
    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        var s = el('save');
        if (s && !s.disabled) s.click();
      }
    });
  });

  return { el: el, status: status, post: post, onSave: onSave,
           refreshPreview: refreshPreview, warnOnLeave: warnOnLeave };
})();
