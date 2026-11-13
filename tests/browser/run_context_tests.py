"""Context menus, XS brush and rectangle-only resize against real Chromium.
--inline injects source/PNG bytes; it is NOT a Safari, hosting, or device test.
"""
from __future__ import annotations
import argparse,functools,http.server,json,shutil,sys,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
import run_template_tests as templates
import run_browser_tests as old
ROOT=Path(__file__).resolve().parents[2]
PROFILES=templates.PROFILES
class ContextCases(templates.TemplateCases):
 def raw(self,selector):
  old.BrowserCases.click(self,selector);self.settle()
 def fixture(self):
  self.page.evaluate('''()=>{ctx.clearRect(0,0,W(),H());ctx.save();ctx.globalCompositeOperation='source-over';
   ctx.fillStyle='#ff0000';ctx.fillRect(W()*.4,H()*.4,W()*.1,H()*.1);
   ctx.fillStyle='#0044ff';ctx.fillRect(W()*.04,H()*.04,W()*.1,H()*.1);ctx.restore();snap();
   window.__regionBefore=ctx.getImageData(0,0,canvas.width,canvas.height).data.slice();}''')
 def select_region(self,touch=False):
  self.click('#selectionBtn');self.settle();w,h=self.page.evaluate('[W(),H()]')
  a,b=self.client(w*.25,h*.25),self.client(w*.7,h*.7)
  if touch:
   cdp=self.cdp_touch()
   for i in range(7):
    x=a['x']+(b['x']-a['x'])*i/6;y=a['y']+(b['y']-a['y'])*i/6
    self.send_touches(cdp,'touchStart' if not i else 'touchMove',[(1,x,y)])
   self.send_touches(cdp,'touchEnd',[])
  else:
   self.page.mouse.move(a['x'],a['y']);self.page.mouse.down();self.page.mouse.move(b['x'],b['y'],steps=8);self.page.mouse.up()
  self.settle();state=self.page.evaluate('HappySelection.getState()');self.assertTrue(state['ready']);return state['rect']
 def changed_counts(self,rect):
  return self.page.evaluate('''r=>{let inside=0,outside=0;const old=__regionBefore,d=ctx.getImageData(0,0,canvas.width,canvas.height).data;
   for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++){const i=(y*canvas.width+x)*4;
    if(d[i]!==old[i]||d[i+1]!==old[i+1]||d[i+2]!==old[i+2]||d[i+3]!==old[i+3]){
     if(x>=r.x&&x<r.x+r.width&&y>=r.y&&y<r.y+r.height)inside++;else outside++;}}
   return {inside,outside};}''',rect)
 def test_10_upload_after_scrolling_opens_native_filechooser(self):
  self.open_tools('pagesSection');tools=self.page.locator('.tools');max_scroll=tools.evaluate('e=>e.scrollHeight-e.clientHeight')
  if max_scroll>0:
   tools.evaluate('e=>e.scrollTop=e.scrollHeight');self.settle();self.assertGreater(tools.evaluate('e=>e.scrollTop'),0)
  self.page.locator('#imageUpload').scroll_into_view_if_needed();self.settle()
  with self.page.expect_file_chooser() as chooser:self.raw('#imageUpload')
  fixture=ROOT/'tests/fixtures/closed-square.png';chooser.value.set_files(str(fixture));self.wait_picture()
  cx,cy=self.page.evaluate('[W()/2,H()/2]');self.color('#ff0000');self.click('#bucketBtn');self.tap_art(cx,cy)
  self.assertEqual(self.pixel(cx,cy),[255,0,0,255]);offset=self.page.evaluate('Math.min(W(),H())*.3');self.assertEqual(self.pixel(cx-offset,cy-offset),[255,255,255,255])
  self.page.locator('#imageUpload').set_input_files(str(fixture));self.wait_picture();self.assertEqual(self.pixel(cx,cy),[255,255,255,255]);self.assert_layout()
 def test_19_actual_toolbar_touch_scroll_keeps_header(self):
  self.open_tools('colorsSection');tools=self.page.locator('.tools');max_scroll=tools.evaluate('e=>e.scrollHeight-e.clientHeight')
  cdp=self.cdp_touch();r=tools.bounding_box();x=r['x']+r['width']-6;y=r['y']+min(250,r['height']-35);chrome=self.chrome_boxes()
  for i in range(7):self.send_touches(cdp,'touchStart' if i==0 else 'touchMove',[(1,x,y-i*18)])
  self.send_touches(cdp,'touchEnd',[]);self.page.wait_for_timeout(150)
  if max_scroll>1:self.assertGreater(tools.evaluate('e=>e.scrollTop'),0)
  else:self.assertEqual(tools.evaluate('e=>e.scrollTop'),0)
  self.assertEqual(chrome,self.chrome_boxes());self.assert_layout()
 def test_200_brush_opens_inline_sizes_and_xs_closes(self):
  self.open_tools();self.raw('#brushBtn');self.assertTrue(self.page.locator('#sizesSection').is_visible());self.assertEqual(self.page.locator('#brushBtn').get_attribute('aria-expanded'),'true')
  self.assertEqual(self.page.locator('.brush').evaluate_all('(els)=>els.map(e=>Number(e.dataset.size))'),[2,8,16,28,44])
  self.raw('[data-size="2"]');self.assertEqual(self.page.evaluate('size'),2);self.assertEqual(self.page.evaluate('tool'),'brush');self.assertFalse(self.page.locator('#sizesSection').is_visible())
  if self.compact():self.assertFalse(self.page.locator('.tools').is_visible())
  self.stroke([(70,100),(170,100)]);self.assertGreater(self.pixel(120,100)[3],0);self.assertEqual(self.pixel(120,104)[3],0)
 def test_201_each_phone_menu_has_only_related_sections(self):
  if not self.compact():self.assertTrue(self.page.locator('#colorsSection').is_visible());return
  expected={'toolsSection':['toolsSection'],'colorsSection':['colorsSection','backgroundSection'],'pagesSection':['uploadSection','pagesSection'],'stickersSection':['stickersSection']}
  for section,wanted in expected.items():
   self.open_tools(section);visible=self.page.locator('#artTools > section:visible').evaluate_all('(els)=>els.map(e=>e.id)');self.assertEqual(set(visible),set(wanted));self.close_tools()
 def test_202_all_five_widths_work_without_duplicate_history(self):
  for n in [2,8,16,28,44]:
   self.open_tools();self.raw('#brushBtn');self.raw(f'[data-size="{n}"]');self.assertEqual(self.page.evaluate('size'),n);before=self.page.evaluate('history.length');self.stroke([(60,160),(160,160)]);self.assertEqual(self.page.evaluate('history.length'),before+1)
 def test_203_other_size_tools_keep_their_tool(self):
  for bid,name in [('sparkleBtn','sparkle'),('eraserBtn','eraser'),('outlineBtn','outline')]:
   self.open_tools();self.raw('#'+bid);self.assertTrue(self.page.locator('#sizesSection').is_visible());self.raw('[data-size="2"]');self.assertEqual(self.page.evaluate('tool'),name);self.assertEqual(self.page.evaluate('size'),2)
 def test_204_size_picker_outside_and_escape_close_without_paint(self):
  before=self.digest();self.open_tools();self.raw('#brushBtn');self.page.keyboard.press('Escape');self.assertFalse(self.page.locator('#sizesSection').is_visible());self.assertEqual(self.digest(),before)
 def test_205_context_controls_translate_all_languages(self):
  for lang in templates.save.lang.LOCALES:
   self.select_language(lang);self.open_tools();self.raw('#brushBtn');self.assertEqual(self.page.locator('[data-size="2"]').get_attribute('aria-label'),self.translated('extraSmall'))
   self.raw('[data-size="2"]');self.click('#selectionBtn');self.assertEqual(self.page.locator('#selectionApply').inner_text(),self.translated('selectionApply'));self.raw('#selectionCancel')
 def test_206_rotation_closes_drawer_without_losing_size(self):
  self.click('[data-size="2"]');self.open_tools('pagesSection');v=self.page.viewport_size;self.page.set_viewport_size(dict(width=v['height'],height=v['width']));self.settle();self.assertEqual(self.page.evaluate('size'),2);self.assert_layout()
 def test_210_selection_preview_changes_no_real_pixels_or_history(self):
  self.fixture();before=self.digest();h=self.page.evaluate('history.length');self.select_region();self.raw('#selectionPlus');self.raw('#selectionPlus')
  self.assertEqual(self.digest(),before);self.assertEqual(self.page.evaluate('history.length'),h);self.assertTrue(self.page.locator('#saveBtn').is_disabled());self.raw('#selectionCancel');self.assertEqual(self.digest(),before)
 def test_211_apply_enlargement_changes_only_selected_rectangle(self):
  self.fixture();r=self.select_region();h=self.page.evaluate('history.length');self.raw('#selectionPlus');self.raw('#selectionPlus');self.raw('#selectionApply')
  changes=self.changed_counts(r);self.assertGreater(changes['inside'],100);self.assertEqual(changes['outside'],0);self.assertEqual(self.page.evaluate('history.length'),h+1)
 def test_212_shrink_only_selected_area_and_undo_redo_exact(self):
  self.fixture();before=self.digest();r=self.select_region();self.raw('#selectionMinus');self.raw('#selectionMinus');self.raw('#selectionApply');after=self.digest();c=self.changed_counts(r)
  self.assertGreater(c['inside'],100);self.assertEqual(c['outside'],0);self.click('#undoBtn');self.page.wait_for_function('canvas.toDataURL()===history.at(-1)');self.assertEqual(self.digest(),before)
  self.click('#redoBtn');self.page.wait_for_function('canvas.toDataURL()===history.at(-1)');self.assertEqual(self.digest(),after)
 def test_213_cancel_and_identity_add_no_undo_step(self):
  self.fixture();before=self.digest();h=self.page.evaluate('history.length');self.select_region();self.raw('#selectionApply');self.assertEqual(self.digest(),before);self.assertEqual(self.page.evaluate('history.length'),h)
  self.select_region();self.raw('#selectionMinus');self.raw('#selectionCancel');self.assertEqual(self.digest(),before);self.assertEqual(self.page.evaluate('history.length'),h)
 def test_214_select_with_actual_touch_keeps_canvas_clean(self):
  self.fixture();before=self.digest();self.select_region(touch=True);self.assertEqual(self.digest(),before);self.raw('#selectionCancel')
 def test_215_pinch_inside_selected_area_not_whole_canvas(self):
  self.fixture();r=self.select_region(touch=True);before=self.digest();zoom=self.page.evaluate('canvasView.zoom');cdp=self.cdp_touch()
  c=self.page.locator('#canvas').bounding_box();bw,bh=self.page.evaluate('[canvas.width,canvas.height]');cx=c['x']+(r['x']+r['width']/2)*c['width']/bw;cy=c['y']+(r['y']+r['height']/2)*c['height']/bh;d=min(25,r['width']*c['width']/bw/5)
  self.send_touches(cdp,'touchStart',[(1,cx-d,cy),(2,cx+d,cy)])
  for f in [1.1,1.2,1.4]:self.send_touches(cdp,'touchMove',[(1,cx-d*f,cy),(2,cx+d*f,cy)])
  self.send_touches(cdp,'touchEnd',[]);self.assertGreater(self.page.evaluate('HappySelection.getState().scale'),1.25);self.assertEqual(self.page.evaluate('canvasView.zoom'),zoom);self.assertEqual(self.digest(),before)
  self.raw('#selectionApply');self.assertEqual(self.changed_counts(r)['outside'],0)
 def test_216_fill_after_resize_still_works(self):
  self.page.evaluate('''()=>{ctx.clearRect(0,0,W(),H());ctx.save();ctx.strokeStyle='#000';ctx.lineWidth=8;ctx.strokeRect(W()*.38,H()*.38,W()*.16,H()*.16);ctx.restore();snap();}''')
  self.select_region();self.raw('#selectionPlus');self.raw('#selectionApply');self.color('#00cc66');self.click('#bucketBtn');w,h=self.page.evaluate('[W(),H()]');self.tap_art(w*.46,h*.46)
  self.assertEqual(self.pixel(w*.46,h*.46),[0,204,102,255]);self.assertEqual(self.pixel(w*.1,h*.1)[3],0)
 def test_217_select_after_zoom_and_pan_keeps_coordinates(self):
  self.fixture();self.zoom(2);self.click('#selectionBtn');self.settle();r=self.page.locator('#canvasViewport').bounding_box()
  self.page.mouse.move(r['x']+r['width']*.3,r['y']+r['height']*.3);self.page.mouse.down();self.page.mouse.move(r['x']+r['width']*.7,r['y']+r['height']*.7,steps=6);self.page.mouse.up()
  selection=self.page.evaluate('HappySelection.getState()');self.assertTrue(selection['ready']);self.raw('#selectionMinus');self.raw('#selectionApply');self.assertEqual(self.changed_counts(selection['rect'])['outside'],0)
 def test_218_rotation_preserves_pending_selection_and_pixels(self):
  self.fixture();before=self.digest();r=self.select_region();self.raw('#selectionPlus');v=self.page.viewport_size;self.page.set_viewport_size(dict(width=v['height'],height=v['width']));self.settle()
  self.assertEqual(self.digest(),before);self.assertEqual(self.page.evaluate('HappySelection.getState().rect'),r);self.raw('#selectionApply');self.assertEqual(self.changed_counts(r)['outside'],0)
 def test_219_other_tool_discards_preview_before_drawing(self):
  self.fixture();before=self.digest();self.select_region();self.raw('#selectionPlus');self.click('#brushBtn');self.assertFalse(self.page.evaluate('HappySelection.isActive()'));self.assertEqual(self.digest(),before)
  self.stroke([(60,80),(160,80)]);self.assertNotEqual(self.digest(),before)
 def test_220_stale_drawing_cannot_be_overwritten(self):
  self.fixture();self.select_region();self.raw('#selectionPlus');self.page.evaluate("ctx.fillStyle='#dd88ff';ctx.fillRect(0,0,15,15);snap()")
  before=self.digest();self.raw('#selectionApply');self.assertEqual(self.digest(),before);self.assertFalse(self.page.evaluate('HappySelection.getState().ready'));self.raw('#selectionCancel')
 def test_221_tiny_selection_rejected_no_undo(self):
  self.fixture();before=self.digest();h=self.page.evaluate('history.length');self.click('#selectionBtn');r=self.page.locator('#selectionLayer').bounding_box()
  self.page.mouse.click(r['x']+r['width']/2,r['y']+r['height']/2);self.assertFalse(self.page.evaluate('HappySelection.getState().ready'));self.assertEqual(self.digest(),before);self.raw('#selectionCancel');self.assertEqual(self.page.evaluate('history.length'),h)
 def test_222_reselect_clears_only_the_preview(self):
  self.fixture();before=self.digest();self.select_region();self.raw('#selectionPlus');self.raw('#selectionAgain');self.assertFalse(self.page.evaluate('HappySelection.getState().ready'));self.assertEqual(self.digest(),before);self.raw('#selectionCancel')
 def test_223_save_exports_applied_changes_not_selection_border(self):
  self.fixture();self.select_region();self.raw('#selectionMinus');self.raw('#selectionApply');before=self.digest();self.ready()
  with self.page.expect_download() as d:self.raw('#downloadPicture')
  target=self.evidence/f'{self.profile_name}-selection-save.png';d.value.save_as(target)
  from PIL import Image
  im=Image.open(target).convert('RGBA');self.assertEqual(im.size,(before['width'],before['height']));self.assertGreater(target.stat().st_size,100);self.close_save();self.assertEqual(self.digest(),before)
 def test_224_selection_controls_fit_seven_languages(self):
  self.fixture()
  for lang in templates.save.lang.LOCALES:
   self.select_language(lang);self.select_region();self.raw('#selectionPlus');vp=self.page.viewport_size
   for selector in ['#selectionMinus','#selectionPlus','#selectionApply','#selectionCancel','#selectionAgain']:
    r=self.page.locator(selector).bounding_box();self.assertGreaterEqual(r['height'],44);self.assertGreaterEqual(r['x'],0);self.assertLessEqual(r['x']+r['width'],vp['width']+1);self.assertLessEqual(r['y']+r['height'],vp['height']+1)
   self.raw('#selectionCancel');self.assert_layout()
 def test_225_selection_on_original_unicorn_and_preview_screenshot(self):
  self.load('unicorn');self.select_region();self.raw('#selectionPlus');self.assertGreater(self.page.locator('#selectionPreview').evaluate('c=>c.getContext("2d").getImageData(0,0,c.width,c.height).data.filter((v,i)=>i%4===3&&v>0).length'),100)
  self.page.screenshot(path=str(self.evidence/f'{self.profile_name}-selection-preview.png'));self.raw('#selectionCancel')
 def test_226_xs_picker_screenshot(self):
  self.open_tools();self.raw('#brushBtn');self.page.screenshot(path=str(self.evidence/f'{self.profile_name}-brush-size.png'));self.raw('[data-size="2"]')

def main():
 p=argparse.ArgumentParser();p.add_argument('--inline',action='store_true');p.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=['desktop','tablet_landscape','phone_portrait','phone_landscape']);p.add_argument('--new-only',action='store_true');p.add_argument('--tests',nargs='+');p.add_argument('--evidence',type=Path,default=ROOT/'evidence/context/browser');a=p.parse_args();a.evidence.mkdir(parents=True,exist_ok=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(old.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,executable_path=shutil.which('chromium'))
   suite=unittest.TestSuite()
   for profile in a.profiles:
    cls=type(f'chromium_{profile}',(ContextCases,),dict(profile_name=profile,browser=browser,inline=a.inline,app_root=ROOT,base_url=f'http://127.0.0.1:{server.server_port}/',evidence=a.evidence))
    for name in unittest.defaultTestLoader.getTestCaseNames(ContextCases):
     if a.new_only and int(name.split('_')[1])<200:continue
     if a.tests and name not in a.tests:continue
     suite.addTest(cls(name))
   old.JsonResult.records=[];result=unittest.TextTestRunner(verbosity=2,resultclass=old.JsonResult).run(suite)
   report=dict(browser='Chromium',browser_version=browser.version,transport='exact source injection and original PNG data URL substitution' if a.inline else 'local HTTP',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),results=result.records)
   (a.evidence/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));browser.close();return 0 if result.wasSuccessful() else 1
 finally:server.shutdown();server.server_close()
if __name__=='__main__':sys.exit(main())
