"""Original-image template import regression, plus the full accepted Save suite.
Default uses a local HTTP server. --inline substitutes ONLY template image URLs with
byte-identical data URLs because this execution environment blocks HTTP navigation.
That fallback is not a network, hosting, caching or physical iOS test.
"""
from __future__ import annotations
import argparse,base64,contextlib,functools,http.server,json,shutil,sys,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
import run_save_tests as save
import run_browser_tests as old
ROOT=Path(__file__).resolve().parents[2]
PROFILES=save.PROFILES
PAGES={'unicorn':'unicorn.png','princess':'princess.png','cat':'cat.png','butterfly':'butterfly.png','dino':'dinosaur.png'}
POINTS=json.loads((ROOT/'tests/fixtures/template-points.json').read_text())
ASSET_DATA={f'assets/coloring-pages/{f}':'data:image/png;base64,'+base64.b64encode((ROOT/'assets/coloring-pages'/f).read_bytes()).decode() for f in PAGES.values()}

class TemplateCases(save.SaveCases):
 def load_app(self):
  if self.inline:
   n=int(self._testMethodName.split('_')[1])
   images=ASSET_DATA if n>=100 or n in (9,20,25,31,38) else {}
   self.page.evaluate('''assets=>{
    window.__templateData=assets;window.__templateRequests=[];window.__pictureDelays={};
    const p=HTMLImageElement.prototype;
    if(!p.__originalPictureSrc)p.__originalPictureSrc=Object.getOwnPropertyDescriptor(p,'src');
    const original=p.__originalPictureSrc;
    Object.defineProperty(p,'src',{configurable:true,enumerable:original.enumerable,get:original.get,set(v){
      const source=String(v);
      if(Object.hasOwn(window.__templateData,source)){
        window.__templateRequests.push(source);
        const data=window.__templateData[source],delay=window.__pictureDelays[source]||0;
        if(delay){const im=this;setTimeout(()=>original.set.call(im,data),delay);}
        else original.set.call(this,data);
      }else original.set.call(this,v);
    }});
   }''',images)
  super().load_app()
 def click(self,selector):
  super().click(selector)
  if 'data-page=' in selector:self.wait_picture()
 def wait_picture(self):
  self.page.wait_for_function('pictureLoadPending===false');self.settle()
 def load(self,name):
  self.click(f'[data-page="{name}"]');self.assertFalse(self.page.evaluate('pictureLoadPending'))
 def picture_point(self,name,key):
  u,v=POINTS[name][key]
  return self.page.evaluate('''([u,v])=>{const side=Math.min(W(),H());return [(W()-side)/2+u*side,(H()-side)/2+v*side]}''',[u,v])
 def at(self,name,key):return self.pixel(*self.picture_point(name,key))
 def center_on(self,name,key,zoom=2.5):
  xy=self.picture_point(name,key)
  self.page.evaluate('''({xy,zoom})=>{canvasView.controlZoom(zoom);const g=canvasView.g;
    canvasStage.scrollLeft=g.left+xy[0]*g.scale-g.vw/2;
    canvasStage.scrollTop=g.top+xy[1]*g.scale-g.vh/2;canvasView.updateControls();}''',dict(xy=xy,zoom=zoom))
  self.settle()
 def fill_at(self,name,key,color):
  self.color(color);self.click('#bucketBtn');self.tap_art(*self.picture_point(name,key));self.settle()
 def dark_digest(self):
  return self.page.evaluate('''()=>{const a=ctx.getImageData(0,0,canvas.width,canvas.height).data;let hash=2166136261,n=0;
  for(let i=0;i<a.length;i+=4)if(a[i]+a[i+1]+a[i+2]<150&&a[i+3]>100){n++;hash=Math.imul(hash^i,16777619);for(let k=0;k<4;k++)hash=Math.imul(hash^a[i+k],16777619)}
  return {n,hash:hash>>>0};}''')
 def import_file(self,name):
  self.page.locator('#imageUpload').set_input_files(str(ROOT/'assets/coloring-pages'/PAGES[name]));self.wait_picture();self.page.wait_for_function('imageUpload.value===""')

 # The original vector-template assertions use obsolete eye coordinates. They are
 # replaced with original-image body/detail locations, retaining no-leak assertions.
 def test_09_bucket_builtin_and_other_page_buttons(self):
  for name in PAGES:
   self.load(name);self.assertGreater(self.dark_digest()['n'],500)
  self.load('unicorn');detail=self.at('unicorn','detail');outside=self.at('unicorn','outside')
  self.fill_at('unicorn','body','#ff0000')
  self.assertEqual(self.at('unicorn','body'),[255,0,0,255]);self.assertEqual(self.at('unicorn','detail'),detail);self.assertEqual(self.at('unicorn','outside'),outside)
 def test_31_template_fill_after_zoom_does_not_leak_through_eye(self):
  self.load('unicorn');detail=self.at('unicorn','detail');outside=self.at('unicorn','outside');self.center_on('unicorn','body')
  self.fill_at('unicorn','body','#ff0000')
  self.assertEqual(self.at('unicorn','body'),[255,0,0,255]);self.assertEqual(self.at('unicorn','detail'),detail);self.assertEqual(self.at('unicorn','outside'),outside)

 def assert_template_equals_upload(self,name):
  opened=[];self.page.on('filechooser',lambda e:opened.append(True))
  self.load(name);pristine=self.digest();self.assertEqual(opened,[],'Template must not open the photo picker')
  detail=self.at(name,'detail');outside=self.at(name,'outside');lines=self.dark_digest()
  self.fill_at(name,'body','#ff4f87');painted=self.digest()
  self.assertEqual(self.at(name,'body'),[255,79,135,255]);self.assertEqual(self.at(name,'detail'),detail);self.assertEqual(self.at(name,'outside'),outside);self.assertEqual(self.dark_digest(),lines)
  self.import_file(name);self.assertEqual(self.digest(),pristine,'Template path must produce the exact same pixels as Upload')
  self.fill_at(name,'body','#ff4f87');self.assertEqual(self.digest(),painted,'Fill must be byte-pixel identical on both import paths')

 def assert_fill_history_export(self,name):
  self.load(name);before=self.digest();detail=self.at(name,'detail');self.center_on(name,'body',2.5)
  self.fill_at(name,'body','#00cc66');filled=self.digest();self.assertEqual(self.at(name,'body'),[0,204,102,255]);self.assertEqual(self.at(name,'detail'),detail)
  self.click('#undoBtn');self.page.wait_for_function('history.at(-1)===canvas.toDataURL()');self.settle();self.assertEqual(self.digest(),before)
  self.click('#redoBtn');self.page.wait_for_function('history.at(-1)===canvas.toDataURL()');self.settle();self.assertEqual(self.digest(),filled)
  self.ready()
  with self.page.expect_download() as event:self.click('#downloadPicture')
  target=self.evidence/f'{self.profile_name}-{name}-filled.png';event.value.save_as(target)
  from PIL import Image
  im=Image.open(target).convert('RGBA');self.assertEqual(im.size,(filled['width'],filled['height']))
  x,y=self.picture_point(name,'body');w,h=self.page.evaluate('[W(),H()]');self.assertEqual(im.getpixel((int(x*im.width/w),int(y*im.height/h))),(0,204,102,255))
  self.close_save();self.assertEqual(self.digest(),filled)

 def test_120_template_switch_undo_restores_previous_template(self):
  self.load('cat');a=self.digest();self.load('butterfly');b=self.digest();self.assertNotEqual(a,b)
  self.click('#undoBtn');self.settle();self.page.wait_for_function('history.at(-1)===canvas.toDataURL()');self.assertEqual(self.digest(),a)
  self.click('#redoBtn');self.settle();self.page.wait_for_function('history.at(-1)===canvas.toDataURL()');self.assertEqual(self.digest(),b)
 def test_121_seven_language_template_buttons_still_map_to_correct_files(self):
  # All seven locales, all five buttons. A loop is counted as one case.
  expected={}
  for name in PAGES:self.load(name);expected[name]=self.digest()
  for locale in save.lang.LOCALES:
   self.select_language(locale)
   for name in PAGES:
    self.load(name);self.assertEqual(self.digest(),expected[name],f'{locale}:{name}')
 def test_122_template_load_after_eraser_and_uploaded_picture(self):
  self.import_file('princess');self.click('#eraserBtn');self.stroke([(80,80),(120,80)])
  self.load('cat');self.assertGreater(self.dark_digest()['n'],500)
  self.fill_at('cat','body','#ff0000');self.assertEqual(self.at('cat','body'),[255,0,0,255])
 def test_123_import_preserves_zoom_scroll_background_color_size_and_tool(self):
  self.load('cat');self.center_on('cat','body');self.click('[data-bg="#ffe5ef"]');self.color('#ab12ef');self.click('[data-size="28"]');self.click('#sparkleBtn')
  state=lambda:self.page.evaluate('({z:canvasView.zoom,x:canvasStage.scrollLeft,y:canvasStage.scrollTop,background,color,size,tool,bw:canvas.width,bh:canvas.height})')
  before=state();self.load('butterfly');self.assertEqual(state(),before)
 def test_124_template_rotation_preserves_image_and_fill_coordinate(self):
  self.load('butterfly');d=self.digest();v=self.page.viewport_size;self.page.set_viewport_size({'width':v['height'],'height':v['width']});self.settle();self.click('#zoomFitBtn');self.assertEqual(self.digest(),d)
  self.center_on('butterfly','body');self.fill_at('butterfly','body','#3366ff');self.assertEqual(self.at('butterfly','body'),[51,102,255,255])
 def test_125_failed_image_keeps_drawing_and_reports_localized_error(self):
  self.load('cat');before=self.digest();h=self.page.evaluate('history.length');messages=[]
  def handle(d):messages.append(d.message);d.accept()
  self.page.on('dialog',handle)
  for locale in save.lang.LOCALES:
   self.select_language(locale)
   # A corrupted image source exercises the real image decoder failure path.
   self.page.evaluate('()=>{loadPictureSource("data:image/png;base64,INVALID");}')
   self.wait_picture();self.assertEqual(messages[-1],self.translated('pictureLoadError'));self.assertEqual(self.digest(),before);self.assertEqual(self.page.evaluate('history.length'),h)
 def test_126_latest_image_selection_wins_not_late_first_decode(self):
  self.load('cat');expected=self.digest()
  if self.inline:
   self.page.evaluate('()=>{__pictureDelays["assets/coloring-pages/unicorn.png"]=350;page("unicorn");page("cat");}')
  else:
   self.page.evaluate('()=>{page("unicorn");page("cat");}')
  self.wait_picture();self.page.wait_for_timeout(450);self.assertEqual(self.digest(),expected)
 def test_127_blank_cancels_pending_image(self):
  self.load('cat')
  if self.inline:self.page.evaluate('()=>{__pictureDelays["assets/coloring-pages/unicorn.png"]=350;}')
  self.page.evaluate('()=>{page("unicorn");page("blank");}')
  self.wait_picture();empty=self.digest();self.page.wait_for_timeout(450);self.assertEqual(self.digest(),empty)
  self.assertFalse(self.page.evaluate('ctx.getImageData(0,0,canvas.width,canvas.height).data.some((v,i)=>i%4===3&&v)'))
 def test_128_drawing_action_cancels_late_image_completion(self):
  if not self.inline:self.skipTest('Controlled delayed decode uses explicit inline fixture substitution')
  self.load('cat');self.page.evaluate('()=>{__pictureDelays["assets/coloring-pages/unicorn.png"]=800;page("unicorn");}')
  self.click('#brushBtn');cx,cy=self.view_center();self.stroke([(cx-10,cy),(cx+10,cy)]);d=self.digest()
  self.wait_picture();self.assertEqual(self.digest(),d)
 def test_129_repeated_template_selection_does_not_duplicate_handlers(self):
  n=self.page.evaluate('history.length');self.load('cat');self.load('cat');self.assertEqual(self.page.evaluate('history.length'),n+2)
  self.fill_at('cat','body','#ff0000');self.assertEqual(self.page.evaluate('history.length'),n+3)
 def test_130_template_assets_keep_original_resolution_and_readable_canvas(self):
  for name in PAGES:
   self.load(name)
   self.assertTrue(self.page.evaluate('canvas.toDataURL("image/png").startsWith("data:image/png;base64,")'))
   self.assertGreater(self.dark_digest()['n'],500)
  self.page.screenshot(path=self.evidence/f'{self.profile_name}-templates.png')

for n,name in enumerate(PAGES):
 def equality(self,name=name):return self.assert_template_equals_upload(name)
 def export(self,name=name):return self.assert_fill_history_export(name)
 setattr(TemplateCases,f'test_{100+n}_{name}_matches_upload_and_fill',equality)
 setattr(TemplateCases,f'test_{110+n}_{name}_zoom_fill_undo_redo_export',export)

def main():
 p=argparse.ArgumentParser();p.add_argument('--inline',action='store_true');p.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=['desktop','tablet_landscape','phone_portrait','phone_landscape']);p.add_argument('--templates-only',action='store_true');p.add_argument('--tests',nargs='+');p.add_argument('--evidence',type=Path,default=ROOT/'evidence/templates/browser');args=p.parse_args();args.evidence.mkdir(parents=True,exist_ok=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(old.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,**({} if Path(pw.chromium.executable_path).exists() else {'executable_path':shutil.which('chromium')}))
   suite=unittest.TestSuite()
   for profile in args.profiles:
    cls=type(f'chromium_{profile}',(TemplateCases,),dict(profile_name=profile,browser=browser,inline=args.inline,app_root=ROOT,base_url=f'http://127.0.0.1:{server.server_port}/',evidence=args.evidence))
    for name in unittest.defaultTestLoader.getTestCaseNames(TemplateCases):
     if args.templates_only and int(name.split('_')[1])<100:continue
     if args.tests and name not in args.tests:continue
     suite.addTest(cls(name))
   old.JsonResult.records=[];result=unittest.TextTestRunner(verbosity=2,resultclass=old.JsonResult).run(suite)
   report=dict(browser='Chromium',browser_version=browser.version,transport='exact source injection; original PNG bytes substituted for relative image URLs' if args.inline else 'local HTTP',native_share='mocked API only',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),results=result.records)
   (args.evidence/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));browser.close();return 0 if result.wasSuccessful() else 1
 finally:server.shutdown();server.server_close()
if __name__=='__main__':sys.exit(main())
