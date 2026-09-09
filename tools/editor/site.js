/* Landing page form. Sends only the fields that actually changed, so a save
   never rewrites a line the editor did not touch. */

(function () {
  var fields = [];
  var dirty = false;

  document.addEventListener('DOMContentLoaded', function () {
    fields = [].slice.call(document.querySelectorAll('[data-path]'));
    fields.forEach(function (f) {
      f.dataset.original = f.value;
      f.addEventListener('input', function () {
        var changed = f.value !== f.dataset.original;
        f.classList.toggle('changed', changed);
        dirty = fields.some(function (x) { return x.value !== x.dataset.original; });
        Admin.status(dirty ? 'Unsaved changes' : '');
      });
    });

    Admin.warnOnLeave(function () { return dirty; });

    Admin.onSave('/admin/api/site', function () {
      var updates = {};
      fields.forEach(function (f) {
        if (f.value !== f.dataset.original) updates[f.dataset.path] = f.value;
      });
      if (!Object.keys(updates).length) throw new Error('Nothing changed');
      return { updates: updates };
    }, function () {
      fields.forEach(function (f) {
        f.dataset.original = f.value;
        f.classList.remove('changed');
      });
      dirty = false;
    });
  });
})();
