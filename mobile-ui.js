/* Fixed Colorful interface and responsive chrome; never redraws the artwork.
 * Pure helpers are exported for unit tests. Runtime uses the tested CanvasZoom view. */
(function (root) {
  'use strict';
  function isCompact(width, height) { return width <= 700 || (width <= 1024 && height <= 500); }
  function isPhoneLandscape(width, height) { return width > height && width <= 1024 && height <= 500; }
  function coverZoom(pw, ph, vw, vh) {
    if (![pw, ph, vw, vh].every(n => Number.isFinite(n) && n > 0)) return 1;
    return Math.min(4, Math.max(1, Math.max(vw / pw, vh / ph) / Math.min(vw / pw, vh / ph)));
  }
  function panelSections(sectionId) {
    const groups = { toolsSection:['toolsSection'], colorsSection:['colorsSection','backgroundSection'],
      pagesSection:['pagesSection','uploadSection'], stickersSection:['stickersSection'] };
    return Object.hasOwn(groups,sectionId) ? [...groups[sectionId]] : [...groups.toolsSection];
  }
  const api = { isCompact, isPhoneLandscape, coverZoom, panelSections };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.StudioLayout = api;
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  const tools = $('artTools'), toggle = $('toolsToggle'), closeTools = $('closeTools');
  const shade = $('drawerShade'), stage = $('canvasViewport'), dock = document.querySelector('.quick-dock');
  let opener = toggle, pending = 0, compact = false, landscape = false, initialized = false;
  let currentPanel = 'toolsSection';
  const sizes = $('sizesSection'), sizeTools = ['brushBtn','sparkleBtn','outlineBtn','eraserBtn'];
  let sizeOpener = null;
  function collapseSizes() {
    sizes.hidden = true; sizeOpener = null;
    sizeTools.forEach(id => $(id).setAttribute('aria-expanded','false'));
  }
  function revealSizes(button) {
    if(root.HappyFillUI)root.HappyFillUI.close();
    const already = sizeOpener === button && !sizes.hidden;
    collapseSizes();
    if (already) return;
    button.after(sizes); sizes.hidden = false; sizeOpener = button;
    button.setAttribute('aria-expanded','true');
    // Keep the actual size buttons visible, including on a short landscape phone.
    requestAnimationFrame(() => sizes.scrollIntoView({block:'nearest',behavior:'instant'}));
  }
  function showPanel(sectionId) {
    const allowed = panelSections(sectionId);
    currentPanel = allowed[0];
    [...tools.children].filter(el => el.tagName === 'SECTION').forEach(el => {el.hidden = compact && !allowed.includes(el.id);});
    const key = {toolsSection:'drawingTools',colorsSection:'colors',pagesSection:'pages',stickersSection:'stickers'}[currentPanel];
    $('toolsPanelTitle').dataset.i18n = compact ? key : 'drawingTools';
    $('toolsPanelTitle').textContent = root.HappyI18n ? root.HappyI18n.t(compact ? key : 'drawingTools') : 'Drawing tools';
  }
  function cancelInput() { if (canvasInput) canvasInput.reset(); end(); }
  function closeDrawer(focus = true) {
    if(root.HappyFillUI)root.HappyFillUI.close();
    collapseSizes();
    document.body.classList.remove('tools-open');
    toggle.setAttribute('aria-expanded', 'false');
    shade.hidden = true;
    tools.removeAttribute('role'); tools.removeAttribute('aria-modal');
    stage.inert = false; dock.inert = false;
    if (focus && compact) (opener || toggle).focus({ preventScroll: true });
  }
  function openDrawer(sectionId = 'toolsSection', source = toggle) {
    if (!compact) return;
    cancelInput(); opener = source;
    document.body.classList.add('tools-open');
    toggle.setAttribute('aria-expanded', 'true');
    tools.setAttribute('role', 'dialog'); tools.setAttribute('aria-modal', 'true');
    shade.hidden = false; stage.inert = true; dock.inert = true;
    collapseSizes(); showPanel(sectionId); tools.scrollTop = 0;
    closeTools.focus({ preventScroll: true });
  }
  toggle.addEventListener('click', () => {
    if (document.body.classList.contains('tools-open')) closeDrawer(); else openDrawer();
  });
  closeTools.addEventListener('click', () => closeDrawer());
  shade.addEventListener('click', () => closeDrawer());
  document.querySelectorAll('[data-open-section]').forEach(b => b.addEventListener('click', () => openDrawer(b.dataset.openSection, b)));
  // Inline size picker: select the tool FIRST via its existing renderer binding,
  // then disclose just its size choices. Choosing a width closes the panel.
  sizeTools.forEach(id => $(id).addEventListener('click', () => revealSizes($(id))));
  tools.addEventListener('click', e => {
    const button = e.target.closest('button');
    if (!button) return;
    if (sizeTools.includes(button.id) || button.id==='bucketBtn' || button.closest('#fillStylesSection')) return;
    if (button.matches('.brush')) {
      const opener=sizeOpener;collapseSizes();
      if(compact)closeDrawer(false);else (opener || $('brushBtn')).focus({preventScroll:true});
      return;
    }
    if (button.matches('.tool-buttons button,.pageBtn,[data-sticker],.swatch,.bg')) {
      collapseSizes();if(compact)closeDrawer(false);
    }
  });
  $('colorPicker').addEventListener('change', () => {if(compact)closeDrawer(false)});
  // Outside click/Escape dismiss the inline picker without changing the drawing.
  document.addEventListener('click', e => {
    if (!sizes.hidden && !e.target.closest('#sizesSection,[aria-controls="sizesSection"]')) collapseSizes();
  },true);
  document.addEventListener('keydown', e => {
    if(e.key==='Escape' && !sizes.hidden && !compact){e.preventDefault();const opener=sizeOpener;collapseSizes();opener?.focus({preventScroll:true});}
  });
  $('imageUpload').addEventListener('change', () => closeDrawer(false));
  // Inert protects the canvas behind the drawer; focus stays inside the temporary tool panel.
  document.addEventListener('keydown', e => {
    if (!document.body.classList.contains('tools-open') || !compact) return;
    if (e.key === 'Escape') { e.preventDefault(); closeDrawer(); return; }
    if (e.key !== 'Tab') return;
    const focusable = [...tools.querySelectorAll('button,input,[tabindex="0"]')].filter(x => !x.disabled && x.getClientRects().length);
    if (!focusable.length) return;
    const first = focusable[0], last = focusable.at(-1);
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
  // Reflect the real tool/color state for keyboard and screen-reader users.
  // Observe existing classes; do not replace any drawing or color handlers.
  const tr = (key, fallback) => root.HappyI18n ? root.HappyI18n.t(key) : fallback;
  const COLOR_KEYS = ['colorPink','colorRed','colorOrange','colorYellow','colorGreen','colorTeal','colorBlue','colorIndigo','colorPurple','colorBrown','colorBlack','colorWhite','colorLightPink','colorLightGreen','colorLightBlue'];
  const COLOR_NAMES = ['Pink','Red','Orange','Yellow','Green','Teal','Blue','Indigo',
    'Purple','Brown','Black','White','Light pink','Light green','Light blue'];
  function syncSelections() {
    document.querySelectorAll('.tool-buttons button:not(#clearBtn),.brush,.bg,[data-sticker],.swatch')
      .forEach(button => button.setAttribute('aria-pressed', String(button.classList.contains('active'))));
    document.querySelectorAll('.swatch').forEach((button,index) => {
      const name = COLOR_KEYS[index] ? tr(COLOR_KEYS[index], COLOR_NAMES[index]) : `Color ${index + 1}`;
      button.setAttribute('aria-label', name);
      button.title = name;
    });
  }
  syncSelections();
  document.addEventListener('happy-language-change', syncSelections);
  if ('MutationObserver' in window) {
    new MutationObserver(syncSelections).observe(tools, { subtree:true, attributes:true, attributeFilter:['class'] });
  }
  function largeView() {
    if (!canvasView || !canvasView.g) return;
    cancelInput();
    canvasView.controlZoom(coverZoom(W(), H(), stage.clientWidth, stage.clientHeight));
    $('viewNotice').dataset.i18n = 'largeNotice';
    $('viewNotice').textContent = tr('largeNotice', 'Large view · Fit shows the whole picture.');
  }
  $('zoomLargeBtn').addEventListener('click', largeView);
  $('zoomFitBtn').addEventListener('click', () => { delete $('viewNotice').dataset.i18n; $('viewNotice').textContent = ''; });
  function layout() {
    pending = 0;
    const nextCompact = isCompact(innerWidth, innerHeight);
    const nextLandscape = isPhoneLandscape(innerWidth, innerHeight);
    if (initialized && (compact !== nextCompact || landscape !== nextLandscape)) closeDrawer(false);
    const enteredLandscape = nextLandscape && (!initialized || !landscape);
    compact = nextCompact; landscape = nextLandscape; initialized = true;
    showPanel(currentPanel);
    fitCanvas();
    // At the default fit scale only: use the wider phone work area on rotation.
    // Existing manual zoom is kept. Cover is a VIEW: no crop or pixel resize is saved.
    if (enteredLandscape && canvasView.zoom < 1.01) largeView();
  }
  function schedule() { if (!pending) pending = requestAnimationFrame(layout); }
  window.addEventListener('resize', schedule, { passive: true });
  window.addEventListener('orientationchange', schedule, { passive: true });
  window.addEventListener('pageshow', schedule, { passive: true });
  layout();
  root.HappyStudio = { openDrawer, closeDrawer, largeView, collapseSizes };
})(typeof globalThis === 'undefined' ? window : globalThis);
