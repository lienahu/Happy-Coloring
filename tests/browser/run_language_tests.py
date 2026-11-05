"""Seven-language UI tests against the actual files and the existing drawing regression.
Default: local HTTP. --inline: exact source injection (no HTTP/cache/storage claim).
Browser preference roundtrip uses explicitly labelled mock storage in --inline mode.
"""
from __future__ import annotations
import argparse,contextlib,functools,hashlib,http.server,json,shutil,sys,threading,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
import run_colorful_tests as base
import run_browser_tests as old
ROOT=Path(__file__).resolve().parents[2]
LOCALES=['en','fr','pt','es','zh-Hans','ja','ko']
NATIVE=['English','Français','Português','Español','简体中文','日本語','한국어']
PROFILES=base.PROFILES
PROFILES['phone_tiny_landscape']=dict(viewport=dict(width=568,height=320),device_scale_factor=2,has_touch=True,is_mobile=True)
old.PROFILES.update(PROFILES)
class LanguageCases(base.ColorfulCases):
 def language_button(self):
  return '#languageDockBtn' if self.compact() else '#languageBtn'
 def select_language(self,language):
  old.BrowserCases.click(self,self.language_button())
  self.page.locator(f'[data-language="{language}"]').click()
  self.settle()
 def translated(self,key):
  return self.page.evaluate('k=>HappyI18n.t(k)',key)
 def read_art_state(self):
  return dict(bitmap=self.digest(),state=self.page.evaluate('''()=>({history:[...history],redo:[...redo],color,size,tool,background,zoom:canvasView.zoom,x:canvasStage.scrollLeft,y:canvasStage.scrollTop})'''))
 def test_61_all_seven_languages_translate_visible_controls(self):
  for locale in LOCALES:
   with self.subTest(language=locale):
    self.select_language(locale)
    self.assertEqual(self.page.locator('html').get_attribute('lang'),locale)
    for sel,key in [('#brushBtn > span','brush'),('#saveBtn .action-text','save'),('#pagesSection h2','pages'),('#zoomFitBtn','fit'),('.upload-control > span','upload'),('#confirmModal h3','newQuestion')]:
     self.assertEqual(self.page.locator(sel).inner_text(),self.translated(key))
    self.assertEqual(self.page.locator('#saveBtn').get_attribute('aria-label'),self.translated('save'))
    self.assertEqual(self.page.locator('#canvasViewport').get_attribute('aria-label'),self.translated('canvasArea'))
 def test_62_switch_preserves_pixels_history_tool_color_zoom_and_scroll(self):
  self.color('#00cc66');self.click('#brushBtn');self.stroke([(80,80),(150,100)]);self.stroke([(80,120),(150,140)])
  self.click('#undoBtn');self.settle();self.zoom(2)
  self.page.evaluate('()=>{canvasStage.scrollLeft=30;canvasStage.scrollTop=25}');self.settle()
  before=self.read_art_state()
  for locale in LOCALES:
   self.select_language(locale);self.assertEqual(self.read_art_state(),before)
  self.click('#redoBtn');self.settle();self.assertNotEqual(self.digest(),before['bitmap'])
 def test_63_native_language_names_and_checked_state(self):
  self.select_language('zh-Hans');old.BrowserCases.click(self,self.language_button())
  self.assertEqual(self.page.locator('.language-option > span:first-child').all_text_contents(),NATIVE)
  self.assertEqual(self.page.locator('.language-option[aria-pressed="true"]').count(),1)
  self.assertEqual(self.page.locator('.language-option[aria-pressed="true"]').get_attribute('data-language'),'zh-Hans')
  self.assertEqual([self.page.locator(f'[data-language="{x}"]').get_attribute('lang') for x in LOCALES],LOCALES)
  self.page.locator('#closeLanguage').click()
 def test_64_new_and_clear_confirmations_translate_without_clearing_on_cancel(self):
  self.stroke([(80,80),(160,80)]);before=self.digest()
  for locale in LOCALES:
   self.select_language(locale);self.click('#newBtn')
   self.assertEqual(self.page.locator('#confirmModal h3').inner_text(),self.translated('newQuestion'))
   self.assertEqual(self.page.locator('#confirmModal p').inner_text(),self.translated('newWarning'))
   self.click('#cancelNew');self.assertEqual(self.digest(),before)
   message=[]
   def handle(d):message.append(d.message);d.dismiss()
   self.page.once('dialog',handle);self.click('#clearBtn')
   self.assertEqual(message,[self.translated('clearQuestion')]);self.assertEqual(self.digest(),before)
 def test_65_dynamic_color_names_and_large_view_remain_translated(self):
  self.select_language('zh-Hans');self.click('.swatch:nth-child(7)');self.click('#sparkleBtn')
  self.assertEqual(self.page.locator('.swatch:nth-child(7)').get_attribute('aria-label'),'蓝色')
  self.click('#zoomLargeBtn');self.assertEqual(self.page.locator('#viewNotice').inner_text(),self.translated('largeNotice'))
  self.select_language('fr');self.assertEqual(self.page.locator('#viewNotice').inner_text(),self.translated('largeNotice'))
  self.click('.swatch:nth-child(2)');self.assertEqual(self.page.locator('.swatch:nth-child(2)').get_attribute('aria-label'),'Rouge')
  self.click('#zoomFitBtn');self.select_language('ko');self.assertEqual(self.page.locator('#viewNotice').inner_text(),'')
 def test_66_modal_focus_escape_and_underlying_canvas_protection(self):
  self.stroke([(80,80),(160,80)]);before=self.digest();old.BrowserCases.click(self,self.language_button())
  self.assertTrue(self.page.locator('#languageDialog').evaluate('e=>e.open'))
  self.assertTrue(self.page.evaluate("!!document.activeElement.closest('#languageDialog')"))
  for _ in range(12):
   self.page.keyboard.press('Tab');self.assertTrue(self.page.evaluate("document.activeElement===document.body || !!document.activeElement.closest('#languageDialog')"))
  self.page.keyboard.press('Escape');self.assertFalse(self.page.locator('#languageDialog').evaluate('e=>e.open'))
  self.assertEqual(self.page.evaluate('document.activeElement.id'),self.language_button()[1:]);self.assertEqual(self.digest(),before)
 def test_67_all_languages_fit_controls_sidebar_and_picker(self):
  for locale in LOCALES:
   with self.subTest(language=locale):
    self.select_language(locale);self.assert_layout();self.open_tools();self.assert_layout()
    # Visible sidebar buttons must fit within their own text containers horizontally.
    overflow=self.page.locator('.tool-buttons button,.pages button,.backgrounds button').evaluate_all('(els)=>els.filter(e=>e.getClientRects().length && e.scrollWidth>e.clientWidth+2).map(e=>e.id||e.textContent)')
    self.assertEqual(overflow,[]);self.close_tools()
    old.BrowserCases.click(self,self.language_button());r=self.page.locator('#languageDialog').bounding_box();vp=self.page.viewport_size
    self.assertGreaterEqual(r['x'],0);self.assertGreaterEqual(r['y'],0)
    self.assertLessEqual(r['x']+r['width'],vp['width']+1);self.assertLessEqual(r['y']+r['height'],vp['height']+1)
    for l in LOCALES:
     option=self.page.locator(f'[data-language="{l}"]');option.scroll_into_view_if_needed();b=option.bounding_box();self.assertGreaterEqual(b['height'],44)
    self.page.locator('#closeLanguage').click()
  self.page.screenshot(path=str(self.evidence/f'{self.profile_name}-korean.png'))
 def test_68_storage_preference_roundtrip_simulated_when_inline(self):
  self.context.close()
  storage_script="""(()=>{const data={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>data[k]??null,setItem:(k,v)=>{data[k]=String(v)}}});})()"""
  self.context=self.browser.new_context(**PROFILES[self.profile_name]);self.page=self.context.new_page();self.page.set_default_timeout(10000);self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  if self.inline:self.page.evaluate(storage_script)
  self.load_app();self.settle();self.select_language('ja')
  stored=self.page.evaluate("localStorage.getItem('happy-colors.language')");self.assertEqual(stored,'ja')
  if self.inline:
   self.page.close();self.page=self.context.new_page();self.page.set_default_timeout(10000);self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.evaluate(storage_script);self.page.evaluate("v=>localStorage.setItem('happy-colors.language',v)",stored);self.load_app()
  else:self.page.reload()
  self.settle();self.assertEqual(self.page.locator('html').get_attribute('lang'),'ja');self.assertEqual(self.page.locator('#saveBtn').get_attribute('aria-label'),'保存')
 def test_69_blocked_storage_does_not_break_language_switch(self):
  self.context.close();self.context=self.browser.new_context(**PROFILES[self.profile_name]);self.page=self.context.new_page();self.page.set_default_timeout(10000);self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  script="Object.defineProperty(window,'localStorage',{configurable:true,get(){throw new DOMException('Blocked','SecurityError')}})"
  if self.inline:self.page.evaluate(script)
  else:self.context.add_init_script(script)
  self.load_app();self.settle();self.assertEqual(self.page.locator('html').get_attribute('lang'),'en')
  self.select_language('es');self.assertEqual(self.page.locator('#saveBtn').get_attribute('aria-label'),'Guardar')
  self.click('#zoomFitBtn');self.stroke([(80,80),(160,80)]);self.assertGreater(self.pixel(120,80)[3],0)
 def test_70_picker_does_not_reintroduce_style_switcher(self):
  self.select_language('pt');self.assertEqual(self.page.locator('#themeBtn,#themeDialog,[data-theme-choice]').count(),0)
  self.assertEqual(self.page.locator('html').get_attribute('data-ui'),'colorful-1')
  if self.compact():
   self.assertFalse(self.page.locator('#languageBtn').is_visible());self.assertTrue(self.page.locator('#languageDockBtn').is_visible())
  else:self.assertTrue(self.page.locator('#languageBtn').is_visible())
 def test_71_translated_tools_still_draw_fill_undo_zoom_and_export(self):
  self.select_language('fr');self.enclosed_shape();self.color('#00cc66');self.click('#bucketBtn');self.tap_art(100,100)
  self.assertEqual(self.pixel(100,100),[0,204,102,255]);filled=self.digest()
  self.select_language('ko');self.click('#undoBtn');self.settle();self.assertEqual(self.pixel(100,100)[3],0)
  self.click('#redoBtn');self.settle();self.assertEqual(self.digest(),filled);self.zoom(2);self.select_language('es');self.assertEqual(self.digest(),filled)
  self.click('#saveBtn');self.page.wait_for_function("document.getElementById('downloadPicture').getAttribute('aria-disabled')==='false'")
  with self.page.expect_download() as info:self.click('#downloadPicture')
  path=self.evidence/f'{self.profile_name}-translated-export.png';info.value.save_as(path)
  from PIL import Image
  im=Image.open(path);self.assertEqual(im.size,(filled['width'],filled['height']))

def main():
 p=argparse.ArgumentParser();p.add_argument('--inline',action='store_true');p.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=['desktop','tablet_landscape','phone_landscape','phone_portrait']);p.add_argument('--only-languages',action='store_true');p.add_argument('--tests',nargs='+');p.add_argument('--evidence',type=Path,default=ROOT/'evidence/languages/browser');args=p.parse_args();args.evidence.mkdir(parents=True,exist_ok=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(old.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,**({} if Path(pw.chromium.executable_path).exists() else {'executable_path':shutil.which('chromium')}))
   suite=unittest.TestSuite()
   for profile in args.profiles:
    cls=type(f'chromium_{profile}',(LanguageCases,),dict(profile_name=profile,browser=browser,inline=args.inline,app_root=ROOT,base_url=f'http://127.0.0.1:{server.server_port}/',evidence=args.evidence))
    for name in unittest.defaultTestLoader.getTestCaseNames(LanguageCases):
     if args.only_languages and int(name.split('_')[1])<61:continue
     if args.tests and name not in args.tests:continue
     suite.addTest(cls(name))
   old.JsonResult.records=[];result=unittest.TextTestRunner(verbosity=2,resultclass=old.JsonResult).run(suite)
   report=dict(browser='Chromium',browser_version=browser.version,transport='exact local source injection' if args.inline else 'local HTTP',storage='simulated preference roundtrip; real API blocked on this origin' if args.inline else 'real browser localStorage',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),results=result.records)
   (args.evidence/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));browser.close();return 0 if result.wasSuccessful() else 1
 finally:server.shutdown();server.server_close()
if __name__=='__main__':sys.exit(main())
