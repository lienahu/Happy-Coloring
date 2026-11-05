/* Local-only export. Prepare a PNG first; SHARE is a separate real tap.
 * Do not call navigator.share after waiting for toBlob/fetch/user activation.
 * Keep the preview URL alive for touch-and-hold and Open image.
 */
(function (root) {
  'use strict';
  const FILE_NAME = 'my-coloring.png';
  function composePicture(source, background, createCanvas) {
    if (!source || !Number.isInteger(source.width) || !Number.isInteger(source.height) ||
        source.width < 1 || source.height < 1) throw new Error('Invalid picture dimensions');
    const result = createCanvas();
    result.width = source.width; result.height = source.height;
    const context = result.getContext('2d');
    if (!context) throw new Error('Canvas unavailable');
    context.globalCompositeOperation = 'source-over';
    // Explicit white fallback, never the purple interface background.
    context.fillStyle = '#ffffff';
    if (typeof background === 'string') context.fillStyle = background;
    context.fillRect(0, 0, result.width, result.height);
    context.drawImage(source, 0, 0);
    return result;
  }
  function pngBlob(picture, timeoutMs = 15000) {
    return new Promise((resolve, reject) => {
      let finished = false;
      const finish = (error, value) => {
        if (finished) return;
        finished = true; clearTimeout(timer);
        error ? reject(error) : resolve(value);
      };
      const timer = setTimeout(() => finish(new Error('PNG export timed out')), timeoutMs);
      try {
        picture.toBlob(blob => {
          if (!blob || !blob.size || blob.type !== 'image/png') {
            finish(new Error('PNG export failed')); return;
          }
          finish(null, blob);
        }, 'image/png');
      } catch (error) { finish(error); }
    });
  }
  function makeFile(blob, FileType) {
    try { return typeof FileType === 'function' ? new FileType([blob], FILE_NAME, {type:'image/png'}) : null; }
    catch (_) { return null; }
  }
  function canShareFile(nav, secure, file) {
    if (!secure || !file || !nav || typeof nav.share !== 'function' || typeof nav.canShare !== 'function') return false;
    try { return nav.canShare({files:[file]}) === true; } catch (_) { return false; }
  }
  function shareErrorKey(error) {
    return error && error.name === 'AbortError' ? 'saveCancelled' : 'saveShareError';
  }
  const helpers = {composePicture, pngBlob, makeFile, canShareFile, shareErrorKey, FILE_NAME};
  if (typeof module !== 'undefined' && module.exports) module.exports = helpers;
  if (typeof document === 'undefined') return;

  let ui, opener, sourceCanvas, paperBackground, file = null, objectURL = null;
  let exportId = 0, sharing = false, statusKey = 'savePreparing', pending = false;
  const retired = new Map();
  const tr = key => root.HappyI18n ? root.HappyI18n.t(key) : key;
  function status(key) {
    statusKey = key;
    if (ui) ui.status.textContent = tr(key);
  }
  function setLinks(enabled) {
    for (const link of [ui.download, ui.open]) {
      link.setAttribute('aria-disabled', String(!enabled));
      link.tabIndex = enabled ? 0 : -1;
      if (enabled) link.href = objectURL; else link.removeAttribute('href');
    }
  }
  function updateText() {
    if (!ui) return;
    ui.preview.alt = tr('savePreview');
    ui.status.textContent = tr(statusKey);
  }
  function ensureUI() {
    if (ui) return;
    const $ = id => document.getElementById(id);
    ui = {dialog:$('saveDialog'), close:$('closeSave'), preview:$('savePreview'),
      share:$('sharePicture'), download:$('downloadPicture'), open:$('openPicture'),
      status:$('saveStatus'), retry:$('retrySave')};
    ui.close.addEventListener('click', () => ui.dialog.close());
    ui.dialog.addEventListener('close', () => {
      ++exportId; pending = false; sharing = false;
      ui.dialog.removeAttribute('aria-busy');
      // Do not revoke here: Safari's image menu/open tab may still need the URL.
      if (opener && opener.isConnected) opener.focus({preventScroll:true});
    });
    ui.dialog.addEventListener('click', event => {
      if (event.target !== ui.dialog) return;
      const r = ui.dialog.getBoundingClientRect();
      if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) ui.dialog.close();
    });
    ui.retry.addEventListener('click', () => prepare());
    ui.share.addEventListener('click', () => {
      if (pending || sharing || !file || !canShareFile(root.navigator, root.isSecureContext, file)) return;
      const ticket = exportId;
      sharing = true; ui.share.disabled = true; status('saveSharing');
      const done = key => {
        if (ticket !== exportId || !ui.dialog.open) return;
        sharing = false;
        ui.share.disabled = !canShareFile(root.navigator, root.isSecureContext, file);
        status(key);
      };
      try {
        // Deliberately synchronous until this call. The File is ALREADY ready.
        const result = root.navigator.share({files:[file]});
        Promise.resolve(result).then(() => done('saveShared'), error => done(shareErrorKey(error)));
      } catch (error) { done(shareErrorKey(error)); }
      // No auto-download on cancel/error; the preview and explicit links stay usable.
    });
    for (const [link, key] of [[ui.download,'saveDownloadRequested'],[ui.open,'saveOpenRequested']]) {
      link.addEventListener('click', event => {
        if (link.getAttribute('aria-disabled') === 'true') { event.preventDefault(); return; }
        status(key);
        // A genuine hyperlink activation; no asynchronous synthetic link.click().
      });
    }
    document.addEventListener('happy-language-change', updateText);
  }
  function retireURL(url) {
    if (!url) return;
    // A previous tab or started download gets time to consume its Blob.
    const timer = setTimeout(() => { root.URL.revokeObjectURL(url); retired.delete(url); }, 60000);
    retired.set(url, timer);
  }
  async function prepare() {
    if (pending) return;
    const ticket = ++exportId;
    pending = true; file = null; sharing = false;
    ui.share.disabled = true; setLinks(false); ui.retry.hidden = true;
    ui.preview.hidden = true; ui.preview.removeAttribute('src');
    ui.dialog.setAttribute('aria-busy', 'true'); status('savePreparing');
    retireURL(objectURL); objectURL = null;
    try {
      // Copy the FULL bitmap synchronously before the asynchronous PNG encoding.
      const snapshot = composePicture(sourceCanvas, paperBackground, () => document.createElement('canvas'));
      const blob = await pngBlob(snapshot);
      if (ticket !== exportId || !ui.dialog.open) return;
      objectURL = root.URL.createObjectURL(blob);
      file = makeFile(blob, root.File);
      ui.preview.src = objectURL; ui.preview.hidden = false;
      setLinks(true);
      const supported = canShareFile(root.navigator, root.isSecureContext, file);
      ui.share.disabled = !supported;
      status(supported ? 'saveReady' : (root.isSecureContext ? 'saveNoShare' : 'saveHttpHint'));
    } catch (_) {
      if (ticket !== exportId || !ui.dialog.open) return;
      status('saveExportError'); ui.retry.hidden = false;
    } finally {
      if (ticket === exportId) { pending = false; ui.dialog.removeAttribute('aria-busy'); }
    }
  }
  function open(source, background, trigger) {
    ensureUI();
    if (ui.dialog.open) return;
    if (root.HappyStudio) root.HappyStudio.closeDrawer(false);
    opener = trigger || document.activeElement;
    sourceCanvas = source; paperBackground = background;
    updateText();
    ui.dialog.showModal(); ui.close.focus({preventScroll:true});
    prepare();
  }
  // pagehide with persisted=true enters the back/forward cache: keep previews alive.
  root.addEventListener('pagehide', event => {
    if (event.persisted) return;
    if (objectURL) root.URL.revokeObjectURL(objectURL);
    for (const [url,timer] of retired) { clearTimeout(timer); root.URL.revokeObjectURL(url); }
    retired.clear();
  });
  root.HappySave = {open};
})(typeof globalThis === 'undefined' ? window : globalThis);
