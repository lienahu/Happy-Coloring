"""15 Fill patterns + 30 lazy library templates, with inherited E1 regressions.
Normal use: local HTTP. --inline uses exact app sources; intercepts catalog/image
reads with local original bytes because container navigation may be blocked.
Interception is TEST INFRASTRUCTURE, not a Safari or real-network claim.
"""
from __future__ import annotations
import argparse,base64,functools,http.server,json,shutil,sys,threading,time,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
import run_context_tests as context
import run_browser_tests as old
ROOT=Path(__file__).resolve().parents[2]
PROFILES=context.PROFILES
CATALOG=json.loads((ROOT/'assets/template-library/catalog.json').read_text())
PROBES=json.loads((ROOT/'tests/fixtures/library-probes.json').read_text())
STYLES=['solid','sparkle','horizontal','vertical','diagonalLeft','diagonalRight','waves','dots','stars','triangles','hearts','flowers','checker','grid','diamonds']
class FillLibraryCases(context.ContextCases):
 def load_app(self):
  super().load_app()
  if self.inline:
   def read_asset(src):
    p=(ROOT/src).resolve()
    if not p.is_relative_to(ROOT) or not p.exists():return ''
    return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
   # Re-creating a page in storage tests needs fresh binding only once per page.
   if not getattr(self,'_bound_page',None)==self.page:
    self.page.expose_function('__readLibraryAsset',read_asset);self._bound_page=self.page
   self.page.evaluate('''catalog=>{
    window.__catalog=catalog;window.__libRequests=[];window.__catalogCalls=0;window.__catalogFail=false;
    const f=window.fetch.bind(window);
    window.fetch=(url,...args)=>{
     if(String(url).startsWith('assets/template-library/catalog.json')){
      __catalogCalls++;return Promise.resolve(new Response(JSON.stringify(__catalogFail?{}:__catalog),{status:__catalogFail?503:200,headers:{'Content-Type':'application/json'}}));
     }return f(url,...args);
    };
    const proto=HTMLImageElement.prototype,base=Object.getOwnPropertyDescriptor(proto,'src');
    window.__libDelay=0;window.__libFail=false;
    Object.defineProperty(proto,'src',{configurable:true,get:base.get,set(v){
     if(String(v).startsWith('assets/template-library/')){
      __libRequests.push(String(v));const im=this,delay=__libDelay,fail=__libFail;
      __readLibraryAsset(String(v)).then(data=>setTimeout(()=>base.set.call(im,fail?'data:image/png;base64,broken':data),delay));
     }else base.set.call(this,v);
    }});
   }''',CATALOG)
 def pattern(self,name):
  self.open_tools();self.raw('#bucketBtn')
  if not self.page.locator('#fillStylesSection').is_visible():self.raw('#bucketBtn')
  self.raw(f'[data-fill-style="{name}"]')
 def square(self):
  self.page.evaluate('''()=>{HappyFill.reset();ctx.save();ctx.globalCompositeOperation='source-over';ctx.clearRect(0,0,W(),H());ctx.fillStyle='#ffffff';ctx.fillRect(45,45,180,180);ctx.strokeStyle='#000';ctx.lineWidth=6;ctx.strokeRect(45,45,180,180);ctx.restore();snap();}''')
 def open_gallery(self,level='easy',page=0):
  if not self.page.locator('#templateLibraryDialog').evaluate('e=>e.open'):self.click('#openTemplateLibrary')
  self.page.wait_for_function('HappyLibrary.getState().count===30');self.raw(f'[data-level="{level}"]');self.settle()
  if page:self.raw('#libraryNext')
  self.page.wait_for_function('document.querySelectorAll(".library-card").length>0');self.settle()
 def close_gallery(self):self.raw('#closeTemplateLibrary')
 def choose(self,item):
  subset=[e for e in CATALOG['items'] if e['level']==item['level']];self.open_gallery(item['level'],subset.index(item)//6)
  self.raw(f'[data-template-id="{item["id"]}"]');self.page.wait_for_function('!document.getElementById("templateLibraryDialog").open');self.wait_picture()
 def exact_inside(self,style,color='#ff4f87'):
  return self.page.evaluate('''({style,color})=>{
    const d=ctx.getImageData(0,0,canvas.width,canvas.height).data,t=FillPatterns.makeTile(style,color,canvas.width/W());let bad=0,n=0;
    const ratio=canvas.width/W();for(let y=Math.ceil(52*ratio);y<Math.floor(217*ratio);y++)for(let x=Math.ceil(52*ratio);x<Math.floor(217*ratio);x++){
      const i=(y*canvas.width+x)*4,j=((y%t.height)*t.width+x%t.width)*4;
      if(d[i]!==t.data[j]||d[i+1]!==t.data[j+1]||d[i+2]!==t.data[j+2]||d[i+3]!==t.data[j+3])bad++;n++;}
    return {bad,n};}''',dict(style=style,color=color))
 def test_300_fill_picker_has_15_choices_and_closes_after_selection(self):
  before=self.digest();self.open_tools();self.raw('#bucketBtn');self.assertTrue(self.page.locator('#fillStylesSection').is_visible());self.assertEqual(self.page.locator('[data-fill-style]').count(),15)
  self.raw('[data-fill-style="stars"]');self.assertEqual(self.page.evaluate('tool'),'bucket');self.assertEqual(self.page.evaluate('HappyFill.getStyle()'),'stars');self.assertFalse(self.page.locator('#fillStylesSection').is_visible());self.assertEqual(before,self.digest())
  if self.compact():self.assertFalse(self.page.locator('.tools').is_visible())
 def test_301_all_15_styles_fill_inside_closed_square_only(self):
  for style in STYLES:
   with self.subTest(style=style):
    self.square();self.color('#ff4f87');self.pattern(style);h=self.page.evaluate('history.length');self.tap_art(100,100);self.assertEqual(self.exact_inside(style)['bad'],0);self.assertEqual(self.pixel(20,20)[3],0);self.assertEqual(self.pixel(45,100)[:3],[0,0,0]);self.assertEqual(self.page.evaluate('history.length'),min(21,h+1))
 def test_302_refill_dots_to_stars_to_solid_replaces_entire_region(self):
  self.square();self.color('#ff4f87')
  for style in ['dots','stars','waves','hearts','solid']:
   self.pattern(style);self.tap_art(100,100);self.assertEqual(self.exact_inside(style)['bad'],0);self.assertEqual(self.pixel(20,20)[3],0)
 def test_303_undo_redo_restore_pattern_membership(self):
  self.square();self.color('#ff4f87');self.pattern('dots');self.tap_art(100,100);a=self.digest();self.pattern('flowers');self.tap_art(100,100);b=self.digest()
  self.click('#undoBtn');self.page.wait_for_function('canvas.toDataURL()===history.at(-1)');self.assertEqual(self.digest(),a)
  self.click('#redoBtn');self.page.wait_for_function('canvas.toDataURL()===history.at(-1)');self.assertEqual(self.digest(),b)
  self.pattern('solid');self.tap_art(100,100);self.assertEqual(self.exact_inside('solid')['bad'],0)
 def test_304_black_and_white_patterns_are_visible_and_refillable(self):
  for color in ['#000000','#ffffff']:
   self.square();self.color(color);self.pattern('dots');self.tap_art(100,100);self.assertEqual(self.exact_inside('dots',color)['bad'],0)
   count=self.page.evaluate('''()=>{const t=FillPatterns.makeTile('dots',color,1),c=new Set();for(let i=0;i<t.data.length;i+=4)c.add(t.data.slice(i,i+4).join(','));return c.size}''');self.assertGreater(count,1)
   self.pattern('solid');self.tap_art(100,100);self.assertEqual(self.exact_inside('solid',color)['bad'],0)
 def test_305_zoomed_pattern_fill_uses_artwork_coordinates(self):
  self.square();self.color('#ff4f87');self.pattern('diamonds');self.page.evaluate('''()=>{canvasView.controlZoom(2.5);const g=canvasView.g;canvasStage.scrollLeft=g.left+130*g.scale-g.vw/2;canvasStage.scrollTop=g.top+130*g.scale-g.vh/2;}''');self.settle();self.tap_art(100,100);self.assertEqual(self.exact_inside('diamonds')['bad'],0)
 def test_306_brush_boundary_after_pattern_keeps_other_side(self):
  self.square();self.color('#ff4f87');self.pattern('checker');self.tap_art(100,100);right=self.pixel(170,100)
  self.color('#000000');self.click('#brushBtn');self.click('[data-size="8"]');self.stroke([(130,40),(130,230)])
  self.color('#00cc66');self.pattern('solid');self.tap_art(85,100);self.assertEqual(self.pixel(85,100),[0,204,102,255]);self.assertEqual(self.pixel(170,100),right);self.assertEqual(self.pixel(130,100)[:3],[0,0,0])
 def test_307_clear_and_import_reset_region_records(self):
  self.square();self.pattern('dots');self.tap_art(100,100);self.assertGreater(self.page.evaluate('HappyFill.debug().records'),0)
  self.click('[data-page="blank"]');self.assertEqual(self.page.evaluate('HappyFill.debug().records'),0)
  self.square();self.pattern('stars');self.tap_art(100,100);self.load('cat');self.assertEqual(self.page.evaluate('HappyFill.debug().records'),0)
 def test_308_pattern_survives_save_with_full_pixels_and_background(self):
  self.square();self.color('#ff4f87');self.pattern('stars');self.tap_art(100,100);self.zoom(2);before=self.digest();self.ready()
  with self.page.expect_download() as d:self.raw('#downloadPicture')
  path=self.evidence/f'{self.profile_name}-pattern-export.png';d.value.save_as(path)
  from PIL import Image
  im=Image.open(path).convert('RGBA');self.assertEqual(im.size,(before['width'],before['height']));self.assertEqual(list(im.getpixel((int(100*before['width']/self.page.evaluate('W()')),int(100*before['height']/self.page.evaluate('H()'))))),self.pixel(100,100));self.close_save()
 def test_309_pattern_picker_and_sizes_do_not_stack(self):
  self.open_tools();self.raw('#brushBtn');self.assertTrue(self.page.locator('#sizesSection').is_visible());self.raw('#bucketBtn');self.assertFalse(self.page.locator('#sizesSection').is_visible());self.assertTrue(self.page.locator('#fillStylesSection').is_visible());self.raw('#brushBtn');self.assertFalse(self.page.locator('#fillStylesSection').is_visible())
 def test_310_no_catalog_or_template_library_reads_at_startup(self):
  self.assertEqual(self.page.evaluate('HappyLibrary.debug().manifestLoads'),0)
  if self.inline:self.assertEqual(self.page.evaluate('__libRequests.length'),0)
 def test_311_catalog_three_tiers_each_ten_and_pagination(self):
  for level in ['easy','medium','hard']:
   self.open_gallery(level);self.assertEqual(self.page.locator('.library-card').count(),6);self.assertIn('10',self.page.locator('#libraryPageCount').inner_text());self.raw('#libraryNext');self.assertEqual(self.page.locator('.library-card').count(),4);self.assertTrue(self.page.locator('#libraryNext').is_disabled());self.close_gallery()
  self.assertEqual(self.page.evaluate('HappyLibrary.debug().manifestLoads'),1)
 def test_312_only_active_thumbnail_page_loaded_no_full_images(self):
  self.open_gallery('easy');self.page.wait_for_timeout(200);self.assertEqual(self.page.evaluate('HappyLibrary.debug().fullSelections'),[])
  paths=self.page.evaluate('HappyLibrary.debug().thumbsAssigned');self.assertTrue(paths);self.assertTrue(all('/thumbs/easy-' in x for x in paths));self.assertLessEqual(len(set(paths)),6)
  self.close_gallery()
 def test_313_selected_card_alone_reads_full_picture(self):
  item=next(x for x in CATALOG['items'] if x['id']=='hard-space-adventure');self.choose(item);self.assertEqual(self.page.evaluate('HappyLibrary.debug().fullSelections'),[item['src']]);self.assertGreater(self.nontransparent(),100)
 def nontransparent(self):return self.page.evaluate('''()=>{const d=ctx.getImageData(0,0,canvas.width,canvas.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i])n++;return n}''')
 def test_314_all_30_templates_load_and_pattern_fill_closed_region(self):
  for item in CATALOG['items']:
   with self.subTest(template=item['id']):
    self.choose(item);self.assertEqual(self.page.evaluate('HappyFill.debug().records'),0);before=self.digest();probe=PROBES[item['id']];x,y=self.page.evaluate('''p=>{const s=Math.min(W(),H());return [(W()-s)/2+p.x*s,(H()-s)/2+p.y*s]}''',probe)
    # Keep a small region's seed onscreen even in a fitted phone canvas.
    self.color('#ff4f87');self.pattern('waves');self.tap_art(x,y);self.assertNotEqual(self.digest(),before);self.assertGreater(self.page.evaluate('HappyFill.debug().records'),0)
 def test_315_library_failure_preserves_art_and_retry(self):
  if not self.inline:self.skipTest('Fault injection uses explicit inline fixture')
  self.stroke([(70,90),(170,90)]);before=self.digest();self.page.evaluate('__catalogFail=true');self.click('#openTemplateLibrary');self.page.wait_for_function('!document.getElementById("libraryRetry").hidden');self.assertEqual(self.digest(),before)
  self.page.evaluate('__catalogFail=false');self.raw('#libraryRetry');self.page.wait_for_function('HappyLibrary.getState().count===30');self.assertEqual(self.digest(),before);self.close_gallery()
 def test_316_image_failure_preserves_art_and_history(self):
  if not self.inline:self.skipTest('Fault injection uses explicit inline fixture')
  self.square();before=self.digest();h=self.page.evaluate('history.length');self.open_gallery('hard');self.page.evaluate('__libFail=true');self.page.once('dialog',lambda d:d.dismiss());self.raw('[data-template-id="hard-coral-reef"]');self.wait_picture();self.assertEqual(self.digest(),before);self.assertEqual(self.page.evaluate('history.length'),h);self.assertTrue(self.page.locator('#templateLibraryDialog').evaluate('e=>e.open'));self.close_gallery()
 def test_317_closing_while_loading_cancels_change(self):
  if not self.inline:self.skipTest('Controlled delay uses explicit inline fixture')
  self.square();before=self.digest();self.open_gallery('hard');self.page.evaluate('__libDelay=300');self.raw('[data-template-id="hard-coral-reef"]');self.close_gallery();self.page.wait_for_timeout(400);self.assertEqual(self.digest(),before)
 def test_318_newest_library_selection_wins(self):
  if not self.inline:self.skipTest('Controlled delay uses explicit inline fixture')
  self.open_gallery('hard');self.page.evaluate('__libDelay=300');self.raw('[data-template-id="hard-coral-reef"]');self.page.evaluate('__libDelay=0');self.raw('[data-template-id="hard-butterfly-mandala"]');self.page.wait_for_function('!document.getElementById("templateLibraryDialog").open');before=self.digest();self.page.wait_for_timeout(400);self.assertEqual(self.digest(),before)
 def test_319_seven_languages_fit_picker_and_library(self):
  for lang in ['en','fr','pt','es','zh-Hans','ja','ko']:
   self.select_language(lang);self.open_tools();self.raw('#bucketBtn');self.assertEqual(self.page.locator('[data-fill-style="hearts"] .fill-style-name').inner_text(),self.translated('pattern_hearts'));self.raw('[data-fill-style="hearts"]');self.open_gallery('easy');self.assertEqual(self.page.locator('[data-template-id="easy-kitten"] span').inner_text(),CATALOG['items'][0]['title'][lang]);vp=self.page.viewport_size
   for sel in ['#closeTemplateLibrary','#libraryNext','[data-level="hard"]']:
    r=self.page.locator(sel).bounding_box();self.assertGreaterEqual(r['height'],44);self.assertGreaterEqual(r['x'],0);self.assertLessEqual(r['x']+r['width'],vp['width']+1);self.assertLessEqual(r['y']+r['height'],vp['height']+1)
   self.close_gallery();self.assert_layout()
 def test_320_browsing_tabs_never_changes_drawing_or_history(self):
  self.square();before=self.digest();h=self.page.evaluate('history.length');self.open_gallery('easy');self.raw('[data-level="medium"]');self.raw('[data-level="hard"]');self.raw('#libraryNext');self.close_gallery();self.assertEqual(self.digest(),before);self.assertEqual(self.page.evaluate('history.length'),h)
 def test_321_keyboard_tabs_and_escape(self):
  self.open_gallery('easy');self.page.locator('[data-level="easy"]').focus();self.page.keyboard.press('ArrowRight');self.assertEqual(self.page.evaluate('HappyLibrary.getState().level'),'medium');self.page.keyboard.press('Escape');self.assertFalse(self.page.locator('#templateLibraryDialog').evaluate('e=>e.open'))
 def test_322_preview_screenshots(self):
  item=next(x for x in CATALOG['items'] if x['id']=='medium-rainbow-unicorn');self.choose(item);self.color('#9360e7');self.pattern('stars');x,y=self.picture_point('unicorn','body');self.tap_art(x,y);self.open_tools();self.raw('#bucketBtn');self.page.screenshot(path=str(self.evidence/f'{self.profile_name}-fill-menu.png'))
  self.close_tools();self.open_gallery('hard');self.page.wait_for_timeout(500);self.page.screenshot(path=str(self.evidence/f'{self.profile_name}-library.png'));self.close_gallery()

def main():
 p=argparse.ArgumentParser();p.add_argument('--inline',action='store_true');p.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=['desktop','tablet_landscape','phone_portrait','phone_landscape']);p.add_argument('--new-only',action='store_true');p.add_argument('--tests',nargs='+');p.add_argument('--evidence',type=Path,default=ROOT/'evidence/fill-library/browser');a=p.parse_args();a.evidence.mkdir(parents=True,exist_ok=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(old.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,executable_path=shutil.which('chromium'));suite=unittest.TestSuite()
   for profile in a.profiles:
    cls=type(f'chromium_{profile}',(FillLibraryCases,),dict(profile_name=profile,browser=browser,inline=a.inline,app_root=ROOT,base_url=f'http://127.0.0.1:{server.server_port}/',evidence=a.evidence))
    for name in unittest.defaultTestLoader.getTestCaseNames(FillLibraryCases):
     if a.new_only and int(name.split('_')[1])<300:continue
     if a.tests and name not in a.tests:continue
     suite.addTest(cls(name))
   old.JsonResult.records=[];result=unittest.TextTestRunner(verbosity=2,resultclass=old.JsonResult).run(suite)
   report=dict(browser='Chromium',browser_version=browser.version,transport='exact local source injection; catalog fetch and image source requests supplied with original local bytes' if a.inline else 'local HTTP',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),results=result.records)
   (a.evidence/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));browser.close();return 0 if result.wasSuccessful() else 1
 finally:server.shutdown();server.server_close()
if __name__=='__main__':sys.exit(main())
