/* Rectangle-only raster resize. Preview is separate; Apply writes only the selected
 * bitmap rectangle, once, using putImageData. No Fill or view-zoom code is replaced. */
(function (root) {
  'use strict';
  const MIN_SCALE = .25, MAX_SCALE = 3;
  const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));
  function limitScale(n) { return Number.isFinite(n) ? clamp(n, MIN_SCALE, MAX_SCALE) : 1; }
  function rectFromPoints(a, b, width, height) {
    if (![a?.x,a?.y,b?.x,b?.y,width,height].every(Number.isFinite) || width < 1 || height < 1) return null;
    const x = clamp(Math.floor(Math.min(a.x,b.x)),0,width), y = clamp(Math.floor(Math.min(a.y,b.y)),0,height);
    const right = clamp(Math.ceil(Math.max(a.x,b.x)),0,width), bottom = clamp(Math.ceil(Math.max(a.y,b.y)),0,height);
    return right > x && bottom > y ? {x,y,width:right-x,height:bottom-y} : null;
  }
  function scaledDestination(width, height, scale) {
    scale = limitScale(scale);
    return {x:width*(1-scale)/2,y:height*(1-scale)/2,width:width*scale,height:height*scale};
  }
  function bitmapPoint(client, box, width, height) {
    if (!box || !(box.width>0 && box.height>0)) return null;
    return {x:clamp((client.clientX-box.left)*width/box.width,0,width),
            y:clamp((client.clientY-box.top)*height/box.height,0,height)};
  }
  const helpers = { MIN_SCALE, MAX_SCALE, limitScale, rectFromPoints, scaledDestination, bitmapPoint };
  if (typeof module !== 'undefined' && module.exports) module.exports = helpers;
  root.SelectionMath = helpers;
  if (typeof document === 'undefined') return;
  const button = document.getElementById('selectionBtn');
  if (!button) return;
  const paper = document.getElementById('canvas');
  const surface = document.getElementById('canvasSurface');
  const wrap = document.querySelector('.canvas-wrap');
  const stage = document.getElementById('canvasViewport');
  const tr = key => root.HappyI18n ? root.HappyI18n.t(key) : key;
  const layer = document.createElement('div');
  layer.id='selectionLayer'; layer.className='selection-layer'; layer.hidden=true;
  layer.setAttribute('aria-hidden','true');
  const preview = document.createElement('canvas');preview.id='selectionPreview';
  const box = document.createElement('div');box.id='selectionBox';box.className='selection-box';box.hidden=true;
  layer.append(preview,box);surface.append(layer);
  const panel = document.createElement('div');panel.id='selectionPanel';panel.className='selection-panel';panel.hidden=true;
  panel.setAttribute('role','group');panel.setAttribute('aria-labelledby','selectionTitle');
  // Static markup; translated strings are written using textContent below.
  panel.innerHTML='<div class="selection-row"><strong id="selectionTitle" data-i18n="selectionTitle"></strong>'+ 
    '<button id="selectionAgain" type="button" data-i18n-title="selectionAgain" data-i18n-aria="selectionAgain">▣</button>'+ 
    '<button id="selectionMinus" type="button" data-i18n-aria="selectionSmaller">−</button>'+ 
    '<output id="selectionPercent" data-i18n-aria="selectionScale">100%</output>'+ 
    '<button id="selectionPlus" type="button" data-i18n-aria="selectionLarger">+</button>'+ 
    '<button id="selectionApply" type="button" class="selection-apply" data-i18n="selectionApply"></button>'+ 
    '<button id="selectionCancel" type="button" data-i18n="selectionCancel"></button></div>'+ 
    '<p id="selectionHelp" role="status" aria-live="polite"></p>';
  wrap.prepend(panel);
  const $ = id => document.getElementById(id);
  const locked = [$('undoBtn'),$('redoBtn'),$('saveBtn')];
  let active=false, rect=null, source=null, original=null, stamp='', scale=1, startPoint=null;
  let sourceWidth=0, sourceHeight=0, selectingId=null, gesture=null, blocked=false, messageKey='selectHint';
  const pointers=new Map();
  let queued=0;
  const distance=(a,b)=>Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY);
  function stop(e) { if(e.cancelable)e.preventDefault();e.stopPropagation(); }
  function releasePointers() {
    const ids=[...pointers.keys()];pointers.clear();selectingId=null;startPoint=null;gesture=null;blocked=false;
    for (const id of ids) { try { if(layer.hasPointerCapture(id))layer.releasePointerCapture(id); } catch(_) {} }
  }
  function syncStrings() {
    panel.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=tr(el.dataset.i18n)});
    panel.querySelectorAll('[data-i18n-aria]').forEach(el=>el.setAttribute('aria-label',tr(el.dataset.i18nAria)));
    panel.querySelectorAll('[data-i18n-title]').forEach(el=>el.title=tr(el.dataset.i18nTitle));
    $('selectionHelp').textContent=tr(messageKey);
  }
  function position() {
    if(!active)return;
    for(const prop of ['left','top','width','height'])layer.style[prop]=paper.style[prop];
    if(!rect){box.hidden=true;preview.hidden=true;return;}
    const sx=paper.getBoundingClientRect().width/paper.width, sy=paper.getBoundingClientRect().height/paper.height;
    const style={left:`${rect.x*sx}px`,top:`${rect.y*sy}px`,width:`${rect.width*sx}px`,height:`${rect.height*sy}px`};
    Object.assign(box.style,style);Object.assign(preview.style,style);box.hidden=false;
  }
  function schedulePosition() { if(!queued)queued=requestAnimationFrame(()=>{queued=0;position()}); }
  function updateControls() {
    $('selectionMinus').disabled=!source || scale<=MIN_SCALE;
    $('selectionPlus').disabled=!source || scale>=MAX_SCALE;
    $('selectionApply').disabled=!source;
    $('selectionAgain').disabled=!rect;
    $('selectionPercent').value=`${Math.round(scale*100)}%`;
    $('selectionPercent').textContent=`${Math.round(scale*100)}%`;
    syncStrings();position();
  }
  function render() {
    if(!source || !rect)return;
    if(preview.width!==rect.width)preview.width=rect.width;
    if(preview.height!==rect.height)preview.height=rect.height;
    const pc=preview.getContext('2d',{willReadFrequently:true});
    pc.clearRect(0,0,preview.width,preview.height);
    if(Math.abs(scale-1)<1e-9)pc.putImageData(original,0,0);
    else {
      const d=scaledDestination(rect.width,rect.height,scale);
      // Nearest-neighbour avoids introducing new gray fringes into line art.
      pc.imageSmoothingEnabled=false;pc.drawImage(source,d.x,d.y,d.width,d.height);
    }
    preview.style.background=background;preview.hidden=false;position();
  }
  function setScale(n) { if(!source)return;scale=limitScale(n);render();updateControls(); }
  function resetSelection() {
    releasePointers();rect=null;source=null;original=null;stamp='';scale=1;preview.hidden=true;box.hidden=true;
    messageKey='selectHint';updateControls();
  }
  function finish(focus=true) {
    if(!active)return;
    active=false;releasePointers();rect=null;source=null;original=null;stamp='';
    panel.hidden=true;layer.hidden=true;preview.hidden=true;box.hidden=true;
    document.body.classList.remove('selection-editing');button.classList.remove('active');button.setAttribute('aria-pressed','false');
    $('saveBtn').disabled=false;buttons();
    if(focus) { if(button.getClientRects().length)button.focus({preventScroll:true});else stage.focus({preventScroll:true}); }
    scheduleLayout();
  }
  function begin() {
    if(active){finish();return;}
    if(!W() || !H())return;
    if(root.HappyStudio)root.HappyStudio.closeDrawer(false);
    canvasInput.reset();end();
    if(cancelPictureRequest)cancelPictureRequest();
    active=true;resetSelection();panel.hidden=false;layer.hidden=false;
    document.body.classList.add('selection-editing');button.classList.add('active');button.setAttribute('aria-pressed','true');
    locked.forEach(el=>{el.disabled=true});
    scheduleLayout();schedulePosition();stage.focus({preventScroll:true});
  }
  function capture(r) {
    try {
      const image=ctx.getImageData(r.x,r.y,r.width,r.height);
      const next=document.createElement('canvas');next.width=r.width;next.height=r.height;
      next.getContext('2d').putImageData(image,0,0);
      // Preview never alters the real canvas. This signature refuses stale commits.
      stamp=paper.toDataURL();sourceWidth=paper.width;sourceHeight=paper.height;
      original=image;source=next;rect=r;scale=1;messageKey='resizeHint';render();updateControls();
    } catch(_) { resetSelection();messageKey='selectionError';syncStrings(); }
  }
  function apply() {
    if(!active || !source || !rect)return false;
    if(paper.width!==sourceWidth || paper.height!==sourceHeight || paper.toDataURL()!==stamp) {
      resetSelection();messageKey='selectionStale';syncStrings();return false;
    }
    if(Math.abs(scale-1)<1e-9){finish();return false;}
    const r=rect, before=original, oldHistory=history.slice(), oldRedo=redo.slice();
    try {
      const result=preview.getContext('2d').getImageData(0,0,r.width,r.height);
      // Bitmap coordinates. putImageData ignores the current drawing transform and
      // compositing mode; no pixel outside this rectangle is written.
      ctx.putImageData(result,r.x,r.y);++restoreTicket;if(root.HappyFill)root.HappyFill.invalidateRect(r,paper.width,paper.height);snap();finish();return true;
    } catch(_) {
      ctx.putImageData(before,r.x,r.y);history=oldHistory;redo=oldRedo;
      messageKey='selectionError';updateControls();return false;
    }
  }
  function point(e){return bitmapPoint(e,paper.getBoundingClientRect(),paper.width,paper.height);}
  function inside(q,r){return q&&r&&q.x>=r.x&&q.y>=r.y&&q.x<=r.x+r.width&&q.y<=r.y+r.height;}
  layer.addEventListener('pointerdown',e=>{
    if(!active || e.button!==0)return;
    stop(e);pointers.set(e.pointerId,{clientX:e.clientX,clientY:e.clientY});
    try{layer.setPointerCapture(e.pointerId)}catch(_){}
    if(blocked)return;
    if(pointers.size>2){gesture=null;blocked=true;return;}
    if(pointers.size===1 && !source) {selectingId=e.pointerId;startPoint=point(e);rect=null;position();return;}
    if(pointers.size===2) {
      if(!source){rect=null;selectingId=null;startPoint=null;blocked=true;position();return;}
      const pair=[...pointers.values()];
      if(pair.every(v=>inside(point(v),rect)))gesture={scale,distance:Math.max(8,distance(...pair)),ids:[...pointers.keys()]};
      else blocked=true;
    }
  },{passive:false});
  layer.addEventListener('pointermove',e=>{
    if(!active || !pointers.has(e.pointerId))return;
    stop(e);pointers.set(e.pointerId,{clientX:e.clientX,clientY:e.clientY});
    if(blocked)return;
    if(gesture){const pair=gesture.ids.map(id=>pointers.get(id));if(pair.every(Boolean))setScale(gesture.scale*distance(...pair)/gesture.distance);}
    else if(e.pointerId===selectingId && startPoint){rect=rectFromPoints(startPoint,point(e),paper.width,paper.height);position();}
  },{passive:false});
  function up(e,cancelled=false) {
    if(!active || !pointers.has(e.pointerId))return;
    stop(e);
    if(!cancelled && !blocked && selectingId===e.pointerId && startPoint) {
      const r=rectFromPoints(startPoint,point(e),paper.width,paper.height),css=paper.getBoundingClientRect();
      if(r && r.width*css.width/paper.width>=10 && r.height*css.height/paper.height>=10)capture(r);
      else {rect=null;messageKey='selectionMin';updateControls();}
    } else if(cancelled && selectingId===e.pointerId && !source){rect=null;messageKey='selectHint';updateControls();}
    pointers.delete(e.pointerId);selectingId=null;startPoint=null;gesture=null;
    blocked=pointers.size>0;
    try{if(layer.hasPointerCapture(e.pointerId))layer.releasePointerCapture(e.pointerId)}catch(_){}
  }
  layer.addEventListener('pointerup',e=>up(e),{passive:false});
  layer.addEventListener('pointercancel',e=>up(e,true),{passive:false});
  layer.addEventListener('lostpointercapture',e=>up(e,true));
  layer.addEventListener('contextmenu',stop);
  $('selectionMinus').addEventListener('click',()=>setScale(Math.round((scale-.25)*100)/100));
  $('selectionPlus').addEventListener('click',()=>setScale(Math.round((scale+.25)*100)/100));
  $('selectionApply').addEventListener('click',apply);
  $('selectionCancel').addEventListener('click',()=>finish());
  $('selectionAgain').addEventListener('click',resetSelection);
  button.addEventListener('click',begin);
  // Choosing another tool/import safely abandons uncommitted preview first.
  document.addEventListener('click',e=>{
    if(!active || e.target.closest('#selectionPanel,#selectionBtn'))return;
    if(e.target.closest('.tool-buttons button,.pageBtn,.swatch,.bg,[data-sticker],#newBtn,#imageUpload,#toolsToggle,[data-open-section]'))finish(false);
  },true);
  document.addEventListener('change',e=>{if(active && e.target.id==='imageUpload')finish(false)},true);
  document.addEventListener('keydown',e=>{if(active&&e.key==='Escape'&&!document.querySelector('dialog[open]')){e.preventDefault();finish();}});
  document.addEventListener('happy-language-change',syncStrings);
  window.addEventListener('blur',()=>releasePointers());
  document.addEventListener('visibilitychange',()=>{if(document.hidden)finish(false)});
  window.addEventListener('resize',()=>{if(active){releasePointers();if(!source){rect=null;position();}schedulePosition();}},{passive:true});
  new MutationObserver(schedulePosition).observe(paper,{attributes:true,attributeFilter:['style']});
  root.HappySelection={begin,cancel:finish,apply,setScale,isActive:()=>active,getState:()=>({active,rect:rect?{...rect}:null,scale,ready:Boolean(source)})};
  syncStrings();
})(typeof globalThis==='undefined'?window:globalThis);
