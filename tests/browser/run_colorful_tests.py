"""Fixed Colorful UI + original drawing regression. Exact local source injection is available
when browser navigation is restricted. It does not test HTTP, caching or deployment.
Usage: python tests/browser/run_colorful_tests.py --inline
"""
from __future__ import annotations
import argparse,contextlib,hashlib,json,re,sys,time,unittest,os,shutil,functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
import run_browser_tests as old
ROOT=Path(__file__).resolve().parents[2]
PROFILES={**old.PROFILES,
 'phone_small_landscape':dict(viewport=dict(width=667,height=375),device_scale_factor=2,has_touch=True,is_mobile=True),
 'phone_mini_portrait':dict(viewport=dict(width=320,height=568),device_scale_factor=2,has_touch=True,is_mobile=True),
 'phone_large_landscape':dict(viewport=dict(width=932,height=430),device_scale_factor=3,has_touch=True,is_mobile=True)}
old.PROFILES.update(PROFILES)
class ColorfulCases(old.BrowserCases):
 def setUp(self):
  self.context=self.browser.new_context(**PROFILES[self.profile_name],accept_downloads=True)
  self.page=self.context.new_page();self.page.set_default_timeout(15000);self.errors=[]
  self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  self.load_app();self.settle()
  # Legacy behavior tests start in Fit mode; auto-large-view is tested separately.
  self.page.locator('#zoomFitBtn').click();self.settle()
 def load_app(self):
  if not self.inline:self.page.goto(self.base_url,wait_until='load');return
  h=(self.app_root/'index.html').read_text()
  h=re.sub(r'<link[^>]+rel="stylesheet"[^>]*>','',h)
  h=re.sub(r'<script[^>]+src="[^"]+"[^>]*></script>','',h)
  self.page.set_content(h, wait_until="domcontentloaded")
  for f in ['style.css','apple-colorful.css','languages.css','save-picture.css']:self.page.add_style_tag(content=(self.app_root/f).read_text())
  for f in ['i18n.js','canvas-zoom.js','save-picture.js','app.js','mobile-ui.js']:self.page.add_script_tag(content=(self.app_root/f).read_text())
 def compact(self):return self.page.locator('#toolsToggle').is_visible()
 def open_tools(self):
  if self.compact() and not self.page.locator('body').evaluate("e=>e.classList.contains('tools-open')"):
   old.BrowserCases.click(self,'#toolsToggle');self.settle()
 def close_tools(self):
  if self.page.locator('body').evaluate("e=>e.classList.contains('tools-open')"):
   self.page.locator('#closeTools').click();self.settle()
 def click(self,selector):
  loc=self.page.locator(selector)
  inside_tools=loc.evaluate("e=>!!e.closest('.tools')")
  if inside_tools:self.open_tools()
  super().click(selector)
  if inside_tools and selector!='#imageUpload':self.close_tools()
 def color(self,value):
  self.open_tools();self.page.locator('#colorPicker').fill(value);self.close_tools()
 def assert_layout(self):
  # Canvas may exceed its viewport intentionally; chrome must remain on-screen.
  data=self.page.evaluate('''()=>{const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}};return {w:innerWidth,h:innerHeight,boxes:['header','main','.canvas-stage','.canvas-board','.top-actions'].map(box),scroll:[scrollX,scrollY],buttons:[...document.querySelectorAll('.top-actions button')].map(e=>{const r=e.getBoundingClientRect();return [r.x,r.y,r.right,r.bottom,r.width,r.height]})}}''')
  for x in data['boxes']:
   self.assertGreater(x['w'],0);self.assertGreater(x['h'],0);self.assertGreaterEqual(x['x'],-1);self.assertGreaterEqual(x['y'],-1);self.assertLessEqual(x['x']+x['w'],data['w']+1);self.assertLessEqual(x['y']+x['h'],data['h']+1)
  for x,y,r,b,w,h in data['buttons']:
   self.assertGreaterEqual(x,-1);self.assertLessEqual(r,data['w']+1);self.assertLessEqual(b,data['h']+1);self.assertGreaterEqual(w,44);self.assertGreaterEqual(h,44)
  self.assertEqual(data['scroll'],[0,0])
  if self.page.locator('.tools').is_visible():
   self.assertLessEqual(self.page.locator('.tools').evaluate('e=>e.scrollWidth-e.clientWidth'),1)
 def test_08_bucket_after_resize_hits_same_region(self):
  self.enclosed_shape();v=PROFILES[self.profile_name]['viewport']
  self.page.set_viewport_size(dict(width=v['height'],height=v['width']));self.settle();self.click('#zoomFitBtn')
  self.color('#00cc66');self.click('#bucketBtn');self.tap_art(100,100)
  self.assertEqual(self.pixel(100,100),[0,204,102,255]);self.assertEqual(self.pixel(30,30)[3],0)
 def test_10_upload_after_scrolling_opens_native_filechooser(self):
  self.open_tools()
  # Upload is now higher in the drawer; scroll away first to exercise returning to it.
  self.page.locator('.tools').evaluate('e=>{e.scrollTop=e.scrollHeight}')
  self.settle();super().test_10_upload_after_scrolling_opens_native_filechooser()
 def test_11_draw_after_rotation_maps_to_pointer(self):
  v=PROFILES[self.profile_name]['viewport'];self.page.set_viewport_size(dict(width=v['height'],height=v['width']));self.settle();self.click('#zoomFitBtn')
  self.stroke([(70,90),(170,90)]);self.assertGreater(self.pixel(120,90)[3],0);self.assertEqual(self.pixel(120,180)[3],0)
 def test_19_actual_toolbar_touch_scroll_keeps_header(self):
  self.open_tools();super().test_19_actual_toolbar_touch_scroll_keeps_header()
 def test_41_single_fixed_interface_no_style_switcher(self):
  self.assertEqual(self.page.locator('html').get_attribute('data-ui'),'colorful-1')
  self.assertEqual(self.page.locator('#themeBtn,#themeDialog,[data-theme-choice]').count(),0)
  self.assertIsNone(self.page.locator('html').get_attribute('data-theme'))
  self.assertEqual(self.page.evaluate('typeof HappyStudio.setTheme'),'undefined')
  self.assert_layout()

 def test_42_drawer_open_close_does_not_change_zoom_or_pixels(self):
  before=self.digest();self.zoom(2);chrome=self.chrome_boxes();self.open_tools()
  if self.compact():
   self.assertEqual(self.page.locator('#toolsToggle').get_attribute('aria-expanded'),'true');self.assertTrue(self.page.locator('#canvasViewport').evaluate('e=>e.inert'))
   self.page.keyboard.press('Escape');self.assertFalse(self.page.locator('.tools').is_visible())
  self.assertEqual(self.digest(),before);self.assertEqual(self.page.evaluate('canvasView.zoom'),2);self.assertEqual(self.chrome_boxes(),chrome)
 def test_43_quick_palette_and_tool_selection(self):
  if self.compact():
   self.click('[data-open-section="colorsSection"]');self.assertTrue(self.page.locator('.tools').is_visible())
  else:self.open_tools()
  self.click('.swatch:nth-child(7)');self.click('#sparkleBtn');self.stroke([(80,100),(180,100)])
  self.assertEqual(self.page.evaluate('tool'),'sparkle');self.assertGreater(self.pixel(120,100)[3],0)
 def test_44_large_view_is_view_only_and_fit_recovers(self):
  self.stroke([(80,100),(180,100)]);before=self.digest();h=self.page.evaluate('history.length')
  self.click('#zoomLargeBtn');self.assertEqual(self.digest(),before);self.assertEqual(self.page.evaluate('history.length'),h)
  g=self.page.evaluate('canvasView.g');self.assertGreaterEqual(g['width'],g['vw']-.5);self.assertGreaterEqual(g['height'],g['vh']-.5)
  self.click('#zoomFitBtn');self.assertEqual(self.page.evaluate('canvasView.zoom'),1);self.assertEqual(self.digest(),before)
 def test_45_phone_landscape_auto_large_from_portrait_preserves_picture(self):
  # This is a deliberate orientation interaction, not a reinitialized drawing.
  self.page.set_viewport_size(dict(width=393,height=851));self.settle();self.click('#zoomFitBtn')
  self.stroke([(80,100),(160,100)]);before=self.digest();h=self.page.evaluate('history.length')
  self.page.set_viewport_size(dict(width=851,height=393));self.settle()
  self.assertEqual(self.digest(),before);self.assertEqual(self.page.evaluate('history.length'),h)
  self.assertGreater(self.page.evaluate('canvasView.zoom'),1);self.assert_layout()
  self.click('#zoomFitBtn');self.assertEqual(self.page.evaluate('canvasView.zoom'),1)
 def test_46_safe_area_simulation_does_not_cover_buttons(self):
  self.page.set_viewport_size(dict(width=851,height=393));self.settle()
  self.page.add_style_tag(content=':root{--safe-left:59px;--safe-right:59px;--safe-bottom:21px;}');self.settle();self.assert_layout()
  data=self.page.evaluate("""()=>[...document.querySelectorAll('.top-actions button,#toolsToggle')].filter(x=>x.getClientRects().length).map(x=>{let r=x.getBoundingClientRect();return [r.left,r.right,r.bottom]})""")
  for left,right,bottom in data:self.assertGreaterEqual(left,59);self.assertLessEqual(right,851-59);self.assertLessEqual(bottom,393-21)
  self.open_tools();r=self.page.locator('.tools').bounding_box();self.assertGreaterEqual(r['x'],59);self.assertLessEqual(r['x']+r['width'],851-59)
  self.close_tools()

 def test_47_drawer_keyboard_and_focus_return(self):
  self.open_tools()
  if self.compact():
   self.assertEqual(self.page.evaluate('document.activeElement.id'),'closeTools')
   self.page.keyboard.press('Shift+Tab');self.assertTrue(self.page.evaluate("!!document.activeElement.closest('.tools')"));self.page.keyboard.press('Escape')
   self.assertEqual(self.page.evaluate('document.activeElement.id'),'toolsToggle')
  self.assert_layout()

 def test_48_blocked_storage_does_not_affect_fixed_interface(self):
  self.page.evaluate("Object.defineProperty(window,'localStorage',{configurable:true,get(){throw new DOMException('blocked','SecurityError')}})")
  self.open_tools();self.close_tools();self.color('#abcdef');self.click('#brushBtn');self.stroke([(70,80),(150,80)])
  self.assertEqual(self.page.locator('html').get_attribute('data-ui'),'colorful-1')
  self.assertGreater(self.pixel(110,80)[3],0)

 def test_49_ui_uses_single_accent_but_paint_remains_separate(self):
  self.assertEqual(self.page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()"),'#6b36d8')
  self.color('#00cc66');self.click('#brushBtn');self.stroke([(80,100),(180,100)])
  self.assertEqual(self.pixel(120,100),[0,204,102,255])
  self.assertEqual(self.page.locator('#canvas').evaluate('e=>getComputedStyle(e).backgroundColor'),'rgb(255, 255, 255)')

 def test_50_reduced_motion_preserves_art_and_chrome(self):
  self.stroke([(80,80),(180,80)]);before=self.digest();boxes=self.chrome_boxes()
  self.page.emulate_media(reduced_motion='reduce');self.settle()
  self.assertEqual(self.digest(),before);self.assertEqual(self.chrome_boxes(),boxes);self.assert_layout()
  self.assertEqual(self.page.locator('#saveBtn').evaluate('e=>getComputedStyle(e).transitionDuration'),'0s')

 def test_51_selected_controls_have_accessible_labels_and_states(self):
  self.open_tools();self.click('.swatch:nth-child(7)');self.click('#sparkleBtn');self.settle()
  self.assertEqual(self.page.locator('#sparkleBtn').get_attribute('aria-pressed'),'true')
  self.assertEqual(self.page.locator('#brushBtn').get_attribute('aria-pressed'),'false')
  self.assertEqual(self.page.locator('.swatch:nth-child(7)').get_attribute('aria-label'),'Blue')
  self.assertEqual(self.page.locator('.swatch:nth-child(7)').get_attribute('aria-pressed'),'true')
 def test_52_ui_design_does_not_contaminate_saved_background(self):
  self.color('#00cc66');self.click('#brushBtn');self.stroke([(70,80),(150,80)])
  self.click('[data-bg="#fff7df"]')
  self.click('#saveBtn');self.page.wait_for_function("document.getElementById('downloadPicture').getAttribute('aria-disabled')==='false'")
  with self.page.expect_download() as info:self.click('#downloadPicture')
  data=info.value;path=self.evidence/f'{self.profile_name}-fixed-export.png';data.save_as(path)
  from PIL import Image
  im=Image.open(path).convert('RGBA');self.assertEqual(im.getpixel((0,0)),(255,247,223,255))



def main():
 p=argparse.ArgumentParser();p.add_argument('--inline',action='store_true');p.add_argument('--browser',choices=['chromium','webkit'],default='chromium');p.add_argument('--profiles',nargs='+',default=list(PROFILES),choices=list(PROFILES));p.add_argument('--only-new',action='store_true');p.add_argument('--tests',nargs='+',help='Optional exact test names for a recorded rerun');p.add_argument('--evidence',type=Path,default=ROOT/'evidence/colorful');args=p.parse_args();args.evidence.mkdir(parents=True,exist_ok=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(old.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   engine=getattr(pw,args.browser);kw={}
   if args.browser=='chromium' and not Path(engine.executable_path).exists():kw['executable_path']=shutil.which('chromium')
   try:browser=engine.launch(headless=True,**kw)
   except Exception as exc:
    (args.evidence/'unavailable.json').write_text(json.dumps({'browser':args.browser,'error':str(exc)},indent=2));print(exc);return 2
   suite=unittest.TestSuite()
   for profile in args.profiles:
    cls=type(f'{args.browser}_{profile}',(ColorfulCases,),dict(profile_name=profile,browser=browser,inline=args.inline,app_root=ROOT,base_url=f'http://127.0.0.1:{server.server_port}/',evidence=args.evidence))
    for name in unittest.defaultTestLoader.getTestCaseNames(ColorfulCases):
     if args.only_new and int(name.split('_')[1])<41:continue
     if args.tests and name not in args.tests:continue
     suite.addTest(cls(name))
   old.JsonResult.records=[];result=unittest.TextTestRunner(verbosity=2,resultclass=old.JsonResult).run(suite)
   report=dict(browser=args.browser,browser_version=browser.version,transport='exact local source injection' if args.inline else 'local HTTP',hardware='emulated viewport and touch, not physical iOS',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),results=result.records,sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['index.html','style.css','app.js','canvas-zoom.js','mobile-ui.js','apple-colorful.css']})
   (args.evidence/'results.json').write_text(json.dumps(report,indent=2));browser.close();return 0 if result.wasSuccessful() else 1
 finally:server.shutdown();server.server_close()
if __name__=='__main__':sys.exit(main())
