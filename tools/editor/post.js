/* Post editor: frontmatter fields plus an Editor.js block body. */

(function () {
  var editor = null;
  var loaded = null;
  var dirty = false;

  function markDirty() {
    if (dirty) return;
    dirty = true;
    Admin.status('Unsaved changes');
  }

  /* Editor.js ships no YouTube-only preset we want, so give Embed just the
     services this site actually uses. */
  var EMBED_SERVICES = {
    youtube: true,
    vimeo: true
  };

  function tools() {
    return {
      header: { class: window.Header, inlineToolbar: true,
                config: { levels: [2, 3, 4], defaultLevel: 2,
                          placeholder: 'Heading' } },
      list: { class: window.List, inlineToolbar: true },
      quote: { class: window.Quote, inlineToolbar: true },
      code: { class: window.CodeTool },
      delimiter: { class: window.Delimiter },
      table: { class: window.Table, inlineToolbar: true },
      embed: { class: window.Embed, config: { services: EMBED_SERVICES } },
      raw: { class: window.RawTool,
             config: { placeholder: 'Markdown kept as written' } },
      marker: { class: window.Marker },
      inlineCode: { class: window.InlineCode },
      image: {
        class: window.ImageTool,
        config: {
          captionPlaceholder: 'Caption',
          uploader: {
            /* raw body plus a filename header: no multipart parsing server side */
            uploadByFile: function (file) {
              return fetch('/admin/api/upload', {
                method: 'POST',
                headers: { 'X-Filename': file.name,
                           'Content-Type': file.type || 'application/octet-stream' },
                body: file
              }).then(function (r) { return r.json(); });
            },
            uploadByUrl: function (url) {
              return Promise.resolve({ success: 1, file: { url: url } });
            }
          }
        }
      }
    };
  }

  /* which frontmatter fields this document type shows */
  var FIELDS = {
    post: { m_title: 'title', m_summary: 'summary', m_date: 'date', m_tag: 'tag' },
    page: { m_title: 'title', m_lede: 'lede', m_nav: 'nav',
            m_order: 'order', m_description: 'description' }
  };

  function fieldMap() { return FIELDS[window.DOC.kind] || FIELDS.post; }

  function fillMeta(meta) {
    var map = fieldMap();
    Object.keys(map).forEach(function (id) {
      var node = Admin.el(id);
      if (!node) return;
      var v = meta[map[id]];
      node.value = (map[id] === 'date') ? String(v || '').slice(0, 10)
                                        : (v == null ? '' : v);
    });
    document.getElementById('ptitle').textContent = meta.title || 'Edit';
  }

  function collectMeta() {
    var map = fieldMap();
    var meta = {};
    Object.keys(map).forEach(function (id) {
      var node = Admin.el(id);
      if (!node) return;
      var v = node.value;
      meta[map[id]] = (map[id] === 'order') ? (parseInt(v, 10) || 0) : v;
    });
    if (window.DOC.kind === 'post') meta.assets = collectAssets();
    return meta;
  }

  function fillAssets(assets) {
    var host = Admin.el('assets');
    if (!assets || !assets.length) return;
    Admin.el('assetgroup').hidden = false;
    assets.forEach(function (a, i) {
      var d = document.createElement('div');
      d.className = 'asset';
      d.innerHTML =
        '<div class="nm">' + esc(a.name || '') + '</div>' +
        '<div class="grid">' +
          '<div><label>Label</label><input data-a="' + i + '" data-k="label" value="' +
            attr(a.label) + '"></div>' +
          '<div><label>Size in bytes</label><input data-a="' + i + '" data-k="bytes" value="' +
            attr(a.bytes) + '"></div>' +
          '<div style="grid-column:1/-1"><label>Download URL</label><input data-a="' + i +
            '" data-k="url" value="' + attr(a.url) + '"></div>' +
          '<div style="grid-column:1/-1"><label>SHA-256 <span class="sub">blank means the page says it was not published</span></label>' +
            '<input data-a="' + i + '" data-k="sha256" value="' + attr(a.sha256) + '"></div>' +
        '</div>';
      host.appendChild(d);
    });
  }

  /* whatever the import could not determine, said once, where the writing happens */
  function showImportWarnings() {
    var msg = null;
    try {
      msg = sessionStorage.getItem('addWarnings');
      sessionStorage.removeItem('addWarnings');
    } catch (e) { return; }
    if (!msg) return;
    var bar = document.createElement('p');
    bar.className = 'warnbar';
    bar.textContent = msg;
    var head = document.querySelector('.col-form .head');
    head.parentNode.insertBefore(bar, head.nextSibling);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
    });
  }
  function attr(s) { return esc(s).replace(/"/g, '&quot;'); }

  function collectAssets() {
    var assets = (loaded.meta.assets || []).map(function (a) {
      return Object.assign({}, a);
    });
    [].slice.call(document.querySelectorAll('#assets [data-a]')).forEach(function (inp) {
      var a = assets[+inp.dataset.a];
      if (!a) return;
      var k = inp.dataset.k;
      a[k] = (k === 'bytes') ? (parseInt(inp.value, 10) || 0) : inp.value;
    });
    return assets;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var api = '/admin/api/' + window.DOC.kind + '/' +
              encodeURIComponent(window.DOC.slug);
    var dir = window.DOC.kind === 'post' ? 'content/updates/' : 'content/pages/';

    fetch(api)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        loaded = data;
        document.getElementById('pfile').textContent = dir + data.slug + '.md';
        showImportWarnings();
        fillMeta(data.meta);
        fillAssets(data.meta.assets);

        editor = new window.EditorJS({
          holder: 'editor',
          tools: tools(),
          data: { blocks: data.blocks },
          placeholder: 'Write the post here',
          onChange: markDirty
        });

        Object.keys(fieldMap()).forEach(function (id) {
          var node = Admin.el(id);
          if (node) node.addEventListener('input', markDirty);
        });
        document.addEventListener('input', function (e) {
          if (e.target.closest && e.target.closest('#assets')) markDirty();
        });

        Admin.warnOnLeave(function () { return dirty; });

        Admin.onSave(api, function () {
            return editor.save().then(function (out) {
              return { meta: collectMeta(), blocks: out.blocks };
            });
          },
          function () {
            dirty = false;
            document.getElementById('ptitle').textContent =
              Admin.el('m_title').value || 'Edit';
          });
      })
      .catch(function (err) { Admin.status(err.message, 'err'); });
  });
})();
