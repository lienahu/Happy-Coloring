"""Save/export regression. Share API is explicitly MOCKED for native-sheet branches.
Use --inline only when navigation is blocked; this is not a Safari or HTTP test.
"""
from __future__ import annotations
import argparse,contextlib,functools,http.server,json,shutil,sys,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
import run_language_tests as lang
import run_browser_tests as old
ROOT=Path(__file__).resolve().parents[2]
PROFILES=lang.PROFILES
class SaveCases(lang.LanguageCases):
 def panel(self):
  self.click('#saveBtn')
  self.page.wait_for_function("document.querySelector('#saveDialog').open && document.querySelector('#saveDialog').getAttribute('aria-busy')!=='true'")
  self.settle()
 def ready(self):
  self.panel();self.page.wait_for_function("document.querySelector('#savePreview').naturalWidth>0")
 def close_save(self):
  self.click('#closeSave');self.page.wait_for_function("!document.querySelector('#saveDialog').open");self.settle()
 def mock_share(self,mode='ok',secure=True):
  self.page.evaluate('''({mode,secure})=>{
   Object.defineProperty(window,'isSecureContext',{configurable:true,value:secure});
   window.__shareCalls=[];window.__shareMode=mode;
   Object.defineProperty(navigator,'canShare',{configurable:true,value:({files})=>{
    if(window.__shareMode==='can-throw')throw new Error('blocked');
    return window.__shareMode!=='can-false'&&files.length===1&&files[0] instanceof File;
   }});
   Object.defineProperty(navigator,'share',{configurable:true,value:(payload)=>{
    window.__shareCalls.push({file:payload.files[0],keys:Object.keys(payload),active:navigator.userActivation.isActive});
    if(window.__shareMode==='pending')return new Promise(r=>window.__finishShare=r);
    if(window.__shareMode==='sync-throw')throw new DOMException('denied','NotAllowedError');
    if(window.__shareMode==='cancel')return Promise.reject(new DOMException('cancelled','AbortError'));
    if(window.__shareMode==='error')return Promise.reject(new DOMException('denied','NotAllowedError'));
    return Promise.resolve();
   }});
  }''',dict(mode=mode,secure=secure))
 def test_80_save_tap_opens_full_picture_preview(self):
  self.stroke([(80,80),(150,80)]);before=self.read_art_state();self.ready()
  self.assertEqual(self.page.locator('#savePreview').evaluate('e=>[e.naturalWidth,e.naturalHeight]'),[before['bitmap']['width'],before['bitmap']['height']])
  self.assertEqual(self.page.locator('#downloadPicture').get_attribute('aria-disabled'),'false')
  self.assertEqual(self.page.locator('#openPicture').get_attribute('target'),'_blank')
  self.assertEqual(self.read_art_state(),before);self.close_save();self.assertEqual(self.read_art_state(),before)
 def test_81_download_png_preserves_full_dimensions_pixels_background(self):
  self.color('#ff0000');self.stroke([(60,80),(150,80)]);self.click('[data-bg="#fff7df"]');self.zoom(3)
  before=self.read_art_state();self.ready()
  with self.page.expect_download() as event:self.click('#downloadPicture')
  target=self.evidence/f'{self.profile_name}-save-export.png';event.value.save_as(target)
  from PIL import Image
  im=Image.open(target).convert('RGBA');w,h=self.page.evaluate('[W(),H()]')
  self.assertEqual(im.size,(before['bitmap']['width'],before['bitmap']['height']))
  self.assertEqual(im.getpixel((0,0)),(255,247,223,255));self.assertEqual(im.getpixel((round(100*im.width/w),round(80*im.height/h))),(255,0,0,255))
  self.assertEqual(event.value.suggested_filename,'my-coloring.png');self.close_save();self.assertEqual(self.read_art_state(),before)
 def test_82_share_receives_prepared_png_file_on_fresh_user_tap(self):
  self.mock_share();self.ready();self.assertTrue(self.page.locator('#sharePicture').is_enabled())
  self.assertEqual(self.page.evaluate('__shareCalls.length'),0)
  self.click('#sharePicture');self.page.wait_for_function('__shareCalls.length===1')
  data=self.page.evaluate('''async()=>{const x=__shareCalls[0];return {name:x.file.name,type:x.file.type,size:x.file.size,keys:x.keys,active:x.active,signature:[...new Uint8Array(await x.file.arrayBuffer()).slice(0,8)]}}''')
  self.assertEqual(data['name'],'my-coloring.png');self.assertEqual(data['type'],'image/png');self.assertEqual(data['keys'],['files']);self.assertTrue(data['active']);self.assertGreater(data['size'],0);self.assertEqual(data['signature'],[137,80,78,71,13,10,26,10])
  self.assertEqual(self.page.locator('#saveStatus').inner_text(),self.translated('saveShared'))
 def test_83_cancel_share_preserves_preview_and_art_without_auto_download(self):
  self.mock_share('cancel');self.stroke([(80,80),(150,80)]);before=self.read_art_state();downloads=[];self.page.on('download',lambda d:downloads.append(d));self.ready();url=self.page.locator('#savePreview').get_attribute('src')
  self.click('#sharePicture');self.settle();self.assertEqual(self.page.locator('#saveStatus').inner_text(),self.translated('saveCancelled'))
  self.assertEqual(downloads,[]);self.assertEqual(self.page.locator('#savePreview').get_attribute('src'),url);self.assertEqual(self.read_art_state(),before);self.assertTrue(self.page.locator('#sharePicture').is_enabled())
 def test_84_share_rejection_and_synchronous_error_keep_download_usable(self):
  for mode in ['error','sync-throw']:
   self.mock_share(mode);self.ready();self.click('#sharePicture');self.settle()
   self.assertEqual(self.page.locator('#saveStatus').inner_text(),self.translated('saveShareError'))
   self.assertEqual(self.page.locator('#downloadPicture').get_attribute('aria-disabled'),'false')
   self.close_save()
 def test_85_insecure_preview_keeps_fallbacks_and_never_shares(self):
  self.mock_share(secure=False);self.ready();self.assertTrue(self.page.locator('#sharePicture').is_disabled())
  self.assertEqual(self.page.evaluate('__shareCalls.length'),0);self.assertEqual(self.page.locator('#saveStatus').inner_text(),self.translated('saveHttpHint'))
  self.assertEqual(self.page.locator('#downloadPicture').get_attribute('aria-disabled'),'false')
 def test_86_missing_or_rejected_file_share_support_falls_back(self):
  for mode in ['can-false','can-throw']:
   self.mock_share(mode);self.ready();self.assertTrue(self.page.locator('#sharePicture').is_disabled());self.assertEqual(self.page.locator('#saveStatus').inner_text(),self.translated('saveNoShare'));self.close_save()
  self.mock_share();self.page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:undefined})");self.ready();self.assertTrue(self.page.locator('#sharePicture').is_disabled())
 def test_87_delayed_export_can_close_and_cannot_replace_next_preview(self):
  self.page.evaluate('''()=>{window.__originalToBlob=HTMLCanvasElement.prototype.toBlob;window.__delay=true;HTMLCanvasElement.prototype.toBlob=function(cb,type){
    __originalToBlob.call(this,b=>{if(__delay){__delay=false;window.__releasePNG=()=>cb(b)}else cb(b)},type);
  }}''')
  self.click('#saveBtn');self.page.wait_for_function("typeof __releasePNG==='function'")
  self.assertEqual(self.page.locator('#saveDialog').get_attribute('aria-busy'),'true');self.assertTrue(self.page.locator('#closeSave').is_visible());self.close_save()
  self.color('#ff0000');self.stroke([(80,80),(150,80)]);self.ready();url=self.page.locator('#savePreview').get_attribute('src');self.page.evaluate('__releasePNG()');self.settle();self.assertEqual(self.page.locator('#savePreview').get_attribute('src'),url)
 def test_88_encode_failure_shows_retry_and_never_clears_drawing(self):
  self.stroke([(80,80),(150,80)]);before=self.read_art_state()
  self.page.evaluate('''()=>{window.__oldToBlob=HTMLCanvasElement.prototype.toBlob;HTMLCanvasElement.prototype.toBlob=cb=>cb(null)}''')
  self.panel();self.assertEqual(self.page.locator('#saveStatus').inner_text(),self.translated('saveExportError'));self.assertTrue(self.page.locator('#retrySave').is_visible());self.assertEqual(self.page.locator('#downloadPicture').get_attribute('href'),None);self.assertEqual(self.read_art_state(),before)
  self.page.evaluate('()=>{HTMLCanvasElement.prototype.toBlob=__oldToBlob;}');self.click('#retrySave');self.page.wait_for_function("document.querySelector('#savePreview').naturalWidth>0");self.assertEqual(self.read_art_state(),before)
 def test_89_repeated_save_uses_current_picture_and_keeps_live_url(self):
  self.mock_share();self.stroke([(80,80),(150,80)]);self.ready();url=self.page.locator('#savePreview').get_attribute('src');self.click('#sharePicture');self.close_save()
  self.assertEqual(self.page.evaluate('''()=>new Promise(resolve=>{const im=new Image();im.onload=()=>resolve(true);im.onerror=()=>resolve(false);im.src=document.querySelector('#savePreview').src})'''),True)
  self.color('#00cc66');self.stroke([(80,160),(150,160)]);self.ready();self.assertNotEqual(self.page.locator('#savePreview').get_attribute('src'),url);self.click('#sharePicture');self.settle()
  self.assertTrue(self.page.evaluate('''async()=>{const [a,b]=await Promise.all(__shareCalls.map(x=>x.file.arrayBuffer()));return a.byteLength!==b.byteLength||new Uint8Array(a).some((v,i)=>v!==new Uint8Array(b)[i])}'''))
 def test_90_pending_share_does_not_lock_preview_close_or_next_save(self):
  self.mock_share('pending');self.ready();self.click('#sharePicture');self.assertTrue(self.page.locator('#sharePicture').is_disabled());self.assertEqual(self.page.locator('#downloadPicture').get_attribute('aria-disabled'),'false');self.close_save()
  self.page.evaluate("__shareMode='ok'");self.ready();before=self.page.locator('#saveStatus').inner_text();self.page.evaluate('__finishShare()');self.settle();self.assertEqual(self.page.locator('#saveStatus').inner_text(),before);self.assertTrue(self.page.locator('#sharePicture').is_enabled())
 def test_91_all_languages_save_labels_fit_and_close_stays_reachable(self):
  self.mock_share()
  for locale in lang.LOCALES:
   self.select_language(locale);self.ready()
   for sel,key in [('#saveTitle','savePicture'),('#sharePicture','saveShare'),('#downloadPicture','saveDownload'),('#openPicture','saveOpen')]:self.assertEqual(self.page.locator(sel).inner_text(),self.translated(key))
   self.assertEqual(self.page.locator('#savePreview').get_attribute('alt'),self.translated('savePreview'))
   r=self.page.locator('#saveDialog').bounding_box();v=self.page.viewport_size
   self.assertGreaterEqual(r['x'],0);self.assertGreaterEqual(r['y'],0);self.assertLessEqual(r['x']+r['width'],v['width']+1);self.assertLessEqual(r['y']+r['height'],v['height']+1)
   self.assertLessEqual(self.page.locator('#saveDialog').evaluate('e=>e.scrollWidth-e.clientWidth'),1)
   for sel in ['#sharePicture','#downloadPicture','#openPicture']:
    e=self.page.locator(sel);e.scroll_into_view_if_needed();self.assertGreaterEqual(e.bounding_box()['height'],44)
   close=self.page.locator('#closeSave').bounding_box();self.assertGreaterEqual(close['y'],0);self.assertLessEqual(close['y']+close['height'],v['height']);self.close_save()
 def test_92_preview_is_outside_gesture_blocking_regions_and_allows_context_menu(self):
  self.ready();self.assertFalse(self.page.locator('#savePreview').evaluate("e=>!!e.closest('header,.tools,.canvas-wrap')"))
  self.assertEqual(self.page.locator('#savePreview').evaluate("e=>getComputedStyle(e).touchAction"),'auto')
  self.assertTrue(self.page.locator('#savePreview').evaluate("e=>e.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true}))"))
  self.assertTrue(self.page.locator('#savePreview').evaluate("e=>e.dispatchEvent(new Event('touchend',{bubbles:true,cancelable:true}))"))
 def test_93_modal_keyboard_focus_return_and_underlying_picture_unchanged(self):
  self.stroke([(80,80),(150,80)]);before=self.read_art_state();self.ready()
  for _ in range(8):
   self.page.keyboard.press('Tab');self.assertTrue(self.page.evaluate("document.activeElement===document.body||!!document.activeElement.closest('#saveDialog')"))
  self.page.keyboard.press('Escape');self.settle();self.assertFalse(self.page.locator('#saveDialog').evaluate('e=>e.open'));self.assertEqual(self.page.evaluate('document.activeElement.id'),'saveBtn');self.assertEqual(self.read_art_state(),before)
 def test_94_language_change_and_rotation_keep_prepared_export_identical(self):
  self.stroke([(80,80),(150,80)]);before=self.digest();self.ready();url=self.page.locator('#savePreview').get_attribute('src')
  self.page.evaluate("HappyI18n.setLanguage('zh-Hans')");self.assertEqual(self.page.locator('#saveTitle').inner_text(),'保存作品');self.assertEqual(self.page.locator('#savePreview').get_attribute('alt'),'完整作品预览')
  v=self.page.viewport_size;self.page.set_viewport_size(dict(width=v['height'],height=v['width']));self.settle();self.assertEqual(self.page.locator('#savePreview').get_attribute('src'),url);self.assertEqual(self.digest(),before)
 def test_95_error_after_success_cannot_download_stale_picture(self):
  self.ready();self.close_save();self.page.evaluate("()=>{HTMLCanvasElement.prototype.toBlob=function(){throw new DOMException('tainted','SecurityError')};}")
  self.panel();self.assertEqual(self.page.locator('#downloadPicture').get_attribute('href'),None);self.assertTrue(self.page.locator('#sharePicture').is_disabled());self.assertTrue(self.page.locator('#savePreview').is_hidden())
 def test_96_dialog_backdrop_dismisses_without_losing_drawing(self):
  self.stroke([(80,80),(150,80)]);before=self.digest();self.ready();self.page.mouse.click(1,1);self.settle();self.assertFalse(self.page.locator('#saveDialog').evaluate('e=>e.open'));self.assertEqual(self.digest(),before)

def main():
 p=argparse.ArgumentParser();p.add_argument('--inline',action='store_true');p.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=['phone_portrait','phone_landscape','tablet_landscape','desktop']);p.add_argument('--save-only',action='store_true');p.add_argument('--tests',nargs='+');p.add_argument('--evidence',type=Path,default=ROOT/'evidence/save/browser');args=p.parse_args();args.evidence.mkdir(parents=True,exist_ok=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(old.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,**({} if Path(pw.chromium.executable_path).exists() else {'executable_path':shutil.which('chromium')}))
   suite=unittest.TestSuite()
   for profile in args.profiles:
    cls=type(f'chromium_{profile}',(SaveCases,),dict(profile_name=profile,browser=browser,inline=args.inline,app_root=ROOT,base_url=f'http://127.0.0.1:{server.server_port}/',evidence=args.evidence))
    for name in unittest.defaultTestLoader.getTestCaseNames(SaveCases):
     if args.save_only and int(name.split('_')[1])<80:continue
     if args.tests and name not in args.tests:continue
     suite.addTest(cls(name))
   old.JsonResult.records=[];result=unittest.TextTestRunner(verbosity=2,resultclass=old.JsonResult).run(suite)
   report=dict(browser='Chromium',browser_version=browser.version,transport='exact local source injection' if args.inline else 'local HTTP',native_share='mocked API capability/outcomes; no native iOS sheet tested',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),results=result.records)
   (args.evidence/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));browser.close();return 0 if result.wasSuccessful() else 1
 finally:server.shutdown();server.server_close()
if __name__=='__main__':sys.exit(main())
