/* Canvas-only view and touch gestures. No artwork pixels or undo states live here.
 * This file has no dependencies and also exports its helpers for Node unit tests. */
(function (root) {
  'use strict';
  const MIN_ZOOM = 1, MAX_ZOOM = 4;
  const clamp = (n, min, max) => Math.min(max, Math.max(min, n));
  function limitZoom(n) { return Number.isFinite(n) ? clamp(n, MIN_ZOOM, MAX_ZOOM) : MIN_ZOOM; }

  function geometry(pw, ph, vw, vh, zoom) {
    if (![pw, ph, vw, vh].every(n => Number.isFinite(n) && n > 0)) return null;
    const scale = Math.min(vw / pw, vh / ph) * limitZoom(zoom);
    const width = pw * scale, height = ph * scale;
    return { vw, vh, scale, width, height,
      sw: Math.max(vw, width), sh: Math.max(vh, height),
      left: Math.max(0, (vw - width) / 2), top: Math.max(0, (vh - height) / 2) };
  }
  function scrollForAnchor(g, paper, view) {
    return {
      x: clamp(g.left + paper.x * g.scale - view.x, 0, Math.max(0, g.sw - g.vw)),
      y: clamp(g.top + paper.y * g.scale - view.y, 0, Math.max(0, g.sh - g.vh))
    };
  }
  const midpoint = (a, b) => ({ x: (a.clientX + b.clientX) / 2, y: (a.clientY + b.clientY) / 2 });
  const distance = (a, b) => Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);

  class View {
    constructor({ canvas, viewport, surface, getSize, controls, beforeResize = () => {}, beforeControl = () => {} }) {
      Object.assign(this, { canvas, viewport, surface, getSize, controls, beforeResize, beforeControl });
      this.zoom = 1;
      this.g = null;
      viewport.addEventListener('scroll', () => this.updateControls(), { passive: true });
      controls.out.addEventListener('click', () => this.controlZoom(this.zoom / 1.25));
      controls.in.addEventListener('click', () => this.controlZoom(this.zoom * 1.25));
      controls.fit.addEventListener('click', () => this.controlZoom(1));
      for (const [name, property] of [['x', 'scrollLeft'], ['y', 'scrollTop']]) {
        controls[name].addEventListener('input', () => {
          this.beforeControl();
          viewport[property] = Number(controls[name].value);
          this.updateControls();
        });
      }
    }
    local(client) {
      const r = this.viewport.getBoundingClientRect();
      return { x: client.x - r.left - this.viewport.clientLeft, y: client.y - r.top - this.viewport.clientTop };
    }
    paperAt(client) {
      const v = this.local(client), g = this.g;
      return { x: (this.viewport.scrollLeft + v.x - g.left) / g.scale,
        y: (this.viewport.scrollTop + v.y - g.top) / g.scale };
    }
    centerClient() {
      const r = this.viewport.getBoundingClientRect();
      return { x: r.left + this.viewport.clientLeft + this.viewport.clientWidth / 2,
        y: r.top + this.viewport.clientTop + this.viewport.clientHeight / 2 };
    }
    controlZoom(zoom) {
      this.beforeControl();
      this.setZoom(zoom);
    }
    // Pass both anchors during a pinch: distance changes zoom, midpoint changes pan.
    setZoom(zoom, client = this.centerClient(), paper = null) {
      if (!this.g) return;
      const anchor = paper || this.paperAt(client);
      this.zoom = limitZoom(zoom);
      this.render(anchor, this.local(client));
    }
    reflow() {
      const vw = this.viewport.clientWidth, vh = this.viewport.clientHeight;
      if (vw <= 0 || vh <= 0) return;
      const old = this.g, size = this.getSize();
      if (old && Math.abs(old.vw - vw) < 0.01 && Math.abs(old.vh - vh) < 0.01) return;
      const anchor = old ? {
        x: (this.viewport.scrollLeft + old.vw / 2 - old.left) / old.scale,
        y: (this.viewport.scrollTop + old.vh / 2 - old.top) / old.scale
      } : { x: size.width / 2, y: size.height / 2 };
      if (old) this.beforeResize();
      this.render(anchor, { x: vw / 2, y: vh / 2 });
    }
    render(anchor, local) {
      const size = this.getSize();
      const g = geometry(size.width, size.height, this.viewport.clientWidth, this.viewport.clientHeight, this.zoom);
      if (!g) return;
      this.g = g;
      this.surface.style.width = `${g.sw}px`;
      this.surface.style.height = `${g.sh}px`;
      Object.assign(this.canvas.style, { width: `${g.width}px`, height: `${g.height}px`,
        left: `${g.left}px`, top: `${g.top}px` });
      const scroll = scrollForAnchor(g, anchor, local);
      this.viewport.scrollLeft = scroll.x;
      this.viewport.scrollTop = scroll.y;
      this.updateControls();
    }
    updateControls() {
      if (!this.g) return;
      const { controls: c, viewport: v } = this;
      c.label.textContent = `${Math.round(this.zoom * 100)}%`;
      c.out.disabled = this.zoom <= MIN_ZOOM + 1e-6;
      c.in.disabled = this.zoom >= MAX_ZOOM - 1e-6;
      for (const [name, value, max] of [
        ['x', v.scrollLeft, v.scrollWidth - v.clientWidth],
        ['y', v.scrollTop, v.scrollHeight - v.clientHeight]
      ]) {
        const visible = max > 1;
        c[name].max = String(Math.max(0, max));
        c[name].value = String(Math.max(0, value));
        c[name].disabled = !visible;
        c[name].style.visibility = visible ? 'visible' : 'hidden';
      }
    }
  }

  // Only touch enters this controller. Mouse and Pencil keep the existing renderer.
  // A touch tap is committed on UP so placing a second finger cannot fill/stamp.
  class TouchInput {
    constructor({ viewport, view, callbacks }) {
      Object.assign(this, { viewport, view, cb: callbacks });
      this.points = new Map();
      this.mode = 'idle';
      this.pending = null;
      this.gesture = null;
      for (const [name, method] of [['pointerdown', 'down'], ['pointermove', 'move'],
        ['pointerup', 'up'], ['pointercancel', 'cancelPointer'], ['lostpointercapture', 'cancelPointer']]) {
        viewport.addEventListener(name, e => { if (e.pointerType === 'touch') this[method](e); }, { passive: false });
      }
    }
    prevent(e) { if (e.cancelable) e.preventDefault(); }
    capture(id) { try { this.viewport.setPointerCapture(id); } catch (_) {} }
    release(id) { try { if (this.viewport.hasPointerCapture(id)) this.viewport.releasePointerCapture(id); } catch (_) {} }
    down(e) {
      if (e.button !== 0) return;
      this.prevent(e);
      this.points.set(e.pointerId, e);
      this.capture(e.pointerId);
      if (this.mode === 'blocked') return;
      if (this.cb.externalDrawing()) { this.mode = 'blocked'; return; }
      if (this.points.size === 1) {
        this.pending = { event: e, drawable: this.cb.onPaper(e), tapTool: this.cb.isTapTool(), moved: false };
        this.mode = 'pending';
      } else if (this.mode !== 'gesture') {
        if (this.mode === 'drawing') this.cb.rollback();
        this.pending = null;
        this.mode = 'gesture';
        this.beginGesture();
      }
    }
    beginGesture() {
      const pair = [...this.points.values()].slice(0, 2);
      if (pair.length < 2) return;
      const center = midpoint(...pair);
      this.gesture = { ids: pair.map(p => p.pointerId), zoom: this.view.zoom,
        distance: Math.max(8, distance(...pair)), anchor: this.view.paperAt(center) };
    }
    move(e) {
      if (!this.points.has(e.pointerId)) return;
      this.prevent(e);
      this.points.set(e.pointerId, e);
      if (this.mode === 'gesture') {
        const g = this.gesture, pair = g.ids.map(id => this.points.get(id));
        if (pair.some(p => !p)) { this.beginGesture(); return; }
        this.view.setZoom(g.zoom * Math.max(8, distance(...pair)) / g.distance, midpoint(...pair), g.anchor);
      } else if (this.mode === 'pending') {
        const p = this.pending;
        if (distance(p.event, e) > 8) p.moved = true;
        if (!p.drawable || p.tapTool || distance(p.event, e) < 3) return;
        this.cb.begin(p.event); // Save rollback bitmap, then start the normal stroke.
        this.mode = 'drawing';
        this.cb.move(e);
      } else if (this.mode === 'drawing') {
        this.cb.move(e);
      }
    }
    up(e) {
      if (!this.points.has(e.pointerId)) return;
      this.prevent(e);
      if (this.mode === 'drawing') this.cb.finish(e);
      if (this.mode === 'pending' && this.pending.drawable && !this.pending.moved &&
          distance(this.pending.event, e) <= 8) this.cb.tap(e);
      this.remove(e.pointerId);
    }
    remove(id) {
      this.points.delete(id); // Remove BEFORE release, which can dispatch lostpointercapture.
      this.release(id);
      this.pending = null;
      if (this.mode === 'gesture' && this.points.size >= 2) this.beginGesture();
      else if (this.points.size) { this.mode = 'blocked'; this.gesture = null; }
      else { this.mode = 'idle'; this.gesture = null; }
    }
    cancelPointer(e) {
      if (!this.points.has(e.pointerId)) return;
      if (this.mode === 'drawing') this.cb.rollback();
      this.remove(e.pointerId);
    }
    // Blur/rotation/buttons cancel the uncommitted preview, but never an older stroke.
    cancel() {
      if (this.mode === 'drawing') this.cb.rollback();
      this.mode = this.points.size ? 'blocked' : 'idle';
      this.pending = null;
      this.gesture = null;
    }
    reset() {
      this.cancel();
      const ids = [...this.points.keys()];
      this.points.clear();
      ids.forEach(id => this.release(id));
      this.mode = 'idle';
    }
  }
  const api = { MIN_ZOOM, MAX_ZOOM, limitZoom, geometry, scrollForAnchor, midpoint, distance, View, TouchInput };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.CanvasZoom = api;
})(typeof globalThis === 'undefined' ? window : globalThis);
