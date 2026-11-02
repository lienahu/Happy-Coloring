"""Regression tests against the actual app in a real browser engine.

Usage:
  python tests/browser/run_browser_tests.py
  python tests/browser/run_browser_tests.py --browser webkit
  python tests/browser/run_browser_tests.py --root PATH --baseline-only

Device profiles emulate viewport/DPR/touch, not physical iOS/Android hardware.
"""
from __future__ import annotations
import argparse
import contextlib
import functools
import hashlib
import http.server
import importlib.metadata
import io
import json
import os
import re
from pathlib import Path
import shutil
import sys
import threading
import time
import unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PROFILES = {
    'desktop': dict(viewport=dict(width=1280, height=800), device_scale_factor=1, has_touch=False, is_mobile=False),
    'tablet_portrait': dict(viewport=dict(width=820, height=1180), device_scale_factor=2, has_touch=True, is_mobile=True),
    'tablet_landscape': dict(viewport=dict(width=1180, height=820), device_scale_factor=2, has_touch=True, is_mobile=True),
    'tablet_split_view': dict(viewport=dict(width=507, height=1024), device_scale_factor=2, has_touch=True, is_mobile=True),
    'phone_portrait': dict(viewport=dict(width=393, height=851), device_scale_factor=3, has_touch=True, is_mobile=True),
    'phone_landscape': dict(viewport=dict(width=851, height=393), device_scale_factor=3, has_touch=True, is_mobile=True),
}

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

class BrowserCases(unittest.TestCase):
    profile_name = 'desktop'
    baseline_only = False
    inline = False
    app_root = ROOT
    browser = None
    base_url = ''
    evidence = ROOT / 'test-results'

    def setUp(self):
        self.context = self.browser.new_context(**PROFILES[self.profile_name], accept_downloads=True)
        self.page = self.context.new_page()
        self.page.set_default_timeout(5000)
        self.errors = []
        self.page.on('pageerror', lambda err: self.errors.append(str(err)))
        if self.inline:
            # Exact local source, no HTTP/cache/deployment claim in this mode.
            html = (self.app_root/'index.html').read_text(encoding='utf-8')
            html = re.sub(r'<link[^>]+href="style\.css[^"]*"[^>]*>', '', html)
            html = re.sub(r'<script[^>]+src="app\.js[^"]*"[^>]*></script>', '', html)
            self.page.set_content(html)
            self.page.add_style_tag(content=(self.app_root/'style.css').read_text(encoding='utf-8'))
            self.page.add_script_tag(content=(self.app_root/'app.js').read_text(encoding='utf-8'))
        else:
            self.page.goto(self.base_url, wait_until='load')
        self.settle()

    def tearDown(self):
        # Capture an image before closing when a test failed.
        if any(test is self for test, _ in self._outcome.result.failures + self._outcome.result.errors):
            with contextlib.suppress(Exception):
                self.page.screenshot(path=str(self.evidence / f'{self.profile_name}-{self._testMethodName}-failed.png'))
        errors = self.errors[:]
        self.context.close()
        self.assertEqual(errors, [], 'Unexpected JavaScript exception')

    def settle(self):
        self.page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')

    def click(self, selector):
        loc = self.page.locator(selector)
        if PROFILES[self.profile_name]['has_touch']:
            loc.tap()
        else:
            loc.click()

    def digest(self):
        # Hash raw pixels, not a screenshot or compressed PNG.
        return self.page.evaluate('''() => {
          const c=document.getElementById('canvas'), x=c.getContext('2d');
          const d=x.getImageData(0,0,c.width,c.height).data;
          let h=2166136261; for(let i=0;i<d.length;i++)h=Math.imul(h^d[i],16777619);
          return {width:c.width,height:c.height,hash:h>>>0};
        }''')

    def pixel(self, x, y):
        return self.page.evaluate('''([x,y]) => {
          const c=document.getElementById('canvas');
          return Array.from(c.getContext('2d').getImageData(Math.floor(x*c.width/W()),Math.floor(y*c.height/H()),1,1).data);
        }''', [x, y])

    def client(self, x, y):
        return self.page.evaluate('''([x,y]) => {
          const r=document.getElementById('canvas').getBoundingClientRect();
          return {x:r.left+x*r.width/W(),y:r.top+y*r.height/H()};
        }''', [x, y])

    def tap_art(self, x, y):
        p = self.client(x, y)
        if PROFILES[self.profile_name]['has_touch']:
            self.page.touchscreen.tap(p['x'], p['y'])
        else:
            self.page.mouse.click(p['x'], p['y'])

    def stroke(self, points):
        # Actual mouse pointer pipeline, plus dedicated CDP touch test below.
        p = self.client(*points[0])
        self.page.mouse.move(p['x'], p['y'])
        self.page.mouse.down()
        for xy in points[1:]:
            p = self.client(*xy)
            self.page.mouse.move(p['x'], p['y'], steps=4)
        self.page.mouse.up()

    def enclosed_shape(self):
        self.click('#outlineBtn')
        self.stroke([(60,60),(140,60),(140,140),(60,140),(60,60)])

    def color(self, value):
        self.page.locator('#colorPicker').fill(value)

    def assert_layout(self):
        data=self.page.evaluate('''() => {
          const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
          return {vw:innerWidth,vh:innerHeight,scrollX,scrollY,
            header:box('header'),tools:box('.tools'),canvas:box('#canvas'),main:box('main'),
            actions:[...document.querySelectorAll('.top-actions button')].map(e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}}),
            toolsOverflow:document.querySelector('.tools').scrollWidth-document.querySelector('.tools').clientWidth};
        }''')
        for name in ['header','tools','canvas','main']:
            b=data[name]
            self.assertGreater(b['width'],0,name)
            self.assertGreaterEqual(b['left'],-1,name)
            self.assertGreaterEqual(b['top'],-1,name)
            self.assertLessEqual(b['right'],data['vw']+1,name)
            self.assertLessEqual(b['bottom'],data['vh']+1,name)
        for b in data['actions']:
            self.assertLessEqual(b['right'],data['vw']+1)
            self.assertLessEqual(b['bottom'],data['vh']+1)
        self.assertEqual(data['scrollX'],0)
        self.assertEqual(data['scrollY'],0)
        self.assertLessEqual(data['toolsOverflow'],1)

    def test_01_layout_and_touch_targets(self):
        self.assert_layout()
        for selector in ['#undoBtn','#redoBtn','#newBtn','#saveBtn']:
            b=self.page.locator(selector).bounding_box()
            self.assertGreaterEqual(b['width'],44)
            self.assertGreaterEqual(b['height'],44)
        self.page.screenshot(path=str(self.evidence / f'{self.profile_name}-layout.png'))

    def test_02_rotation_preserves_exact_pixels_and_aspect(self):
        self.stroke([(70,80),(150,80),(150,160)])
        before=self.digest()
        ratio=self.page.evaluate('W()/H()')
        v=PROFILES[self.profile_name]['viewport']
        for w,h in [(v['height'],v['width']),(v['width'],v['height'])]*2:
            self.page.set_viewport_size(dict(width=w,height=h));self.settle()
            self.assertEqual(self.digest(),before)
            b=self.page.locator('#canvas').bounding_box()
            self.assertAlmostEqual(b['width']/b['height'],ratio,delta=.003)
            self.assert_layout()

    def test_03_browser_bar_height_changes_do_not_rebuild_bitmap(self):
        self.stroke([(90,100),(180,200)])
        before=self.digest();v=PROFILES[self.profile_name]['viewport']
        for delta in [50,-60,35,-85,0]:
            self.page.set_viewport_size(dict(width=v['width'],height=v['height']+delta));self.settle()
            self.assertEqual(self.digest(),before)
            self.assert_layout()

    def test_04_brush_and_exact_undo_redo(self):
        before=self.digest();self.stroke([(60,80),(180,80)])
        painted=self.digest();self.assertNotEqual(before,painted)
        self.assertGreater(self.pixel(110,80)[3],0)
        self.click('#undoBtn');self.page.wait_for_function('!redoBtn.disabled');self.settle()
        self.assertEqual(self.digest(),before)
        self.click('#redoBtn');self.settle();self.assertEqual(self.digest(),painted)

    def test_05_sparkle_leaves_paint_and_highlights(self):
        self.click('#sparkleBtn');self.click('[data-size="44"]');self.color('#ff0000')
        self.page.evaluate('window._oldRandom=Math.random;Math.random=()=>0.5')
        self.stroke([(70,100),(180,100),(180,160)])
        self.page.evaluate('Math.random=window._oldRandom')
        result=self.page.evaluate('''() => {
          const d=ctx.getImageData(0,0,canvas.width,canvas.height).data;
          let red=0,white=0;for(let i=0;i<d.length;i+=4){if(d[i+3]>180&&d[i]>200){if(d[i+1]<80)red++;if(d[i+1]>200)white++}}
          return {red,white};
        }''')
        self.assertGreater(result['red'],0);self.assertGreater(result['white'],0)

    def test_06_eraser_then_undo_restores_exact_pixels(self):
        self.click('[data-size="44"]');self.stroke([(60,100),(180,100)])
        before=self.digest();self.click('#eraserBtn');self.stroke([(110,80),(110,120)])
        self.assertEqual(self.pixel(110,100)[3],0)
        self.click('#undoBtn');self.settle();self.assertEqual(self.digest(),before)

    def test_07_bucket_self_drawn_closed_region(self):
        self.enclosed_shape();self.color('#ff0000');self.click('#bucketBtn');self.tap_art(100,100)
        self.assertEqual(self.pixel(100,100),[255,0,0,255]);self.assertEqual(self.pixel(30,30)[3],0)

    def test_08_bucket_after_resize_hits_same_region(self):
        self.enclosed_shape();v=PROFILES[self.profile_name]['viewport']
        self.page.set_viewport_size(dict(width=v['height'],height=v['width']));self.settle()
        self.color('#00cc66');self.click('#bucketBtn');self.tap_art(100,100)
        self.assertEqual(self.pixel(100,100),[0,204,102,255]);self.assertEqual(self.pixel(30,30)[3],0)

    def test_09_bucket_builtin_and_other_page_buttons(self):
        for name in ['unicorn','princess','cat','butterfly','dino']:
            self.click(f'[data-page="{name}"]')
            nonempty=self.page.evaluate('ctx.getImageData(0,0,canvas.width,canvas.height).data.some((v,i)=>i%4===3&&v>0)')
            self.assertTrue(nonempty,name)
        self.click('[data-page="unicorn"]')
        cx,cy=self.page.evaluate('[W()/2,H()/2]')
        self.color('#ff0000');self.click('#bucketBtn');self.tap_art(cx,cy)
        self.assertEqual(self.pixel(cx,cy),[255,0,0,255])
        self.assertEqual(self.pixel(cx-42,cy-20)[3],0) # The closed eye is not filled.

    def test_10_upload_after_scrolling_opens_native_filechooser(self):
        self.page.locator('#imageUpload').scroll_into_view_if_needed();self.settle()
        self.assertGreater(self.page.locator('.tools').evaluate('(e)=>e.scrollTop'),0)
        # Opening a native chooser is checked, not merely set_input_files().
        with self.page.expect_file_chooser() as choice:
            self.click('#imageUpload')
        choice.value.set_files(str(ROOT / 'tests/fixtures/closed-square.png'))
        self.page.wait_for_function('imageUpload.value===""')
        self.settle();self.assert_layout()
        cx,cy=self.page.evaluate('[W()/2,H()/2]')
        self.color('#ff0000');self.click('#bucketBtn');self.tap_art(cx,cy)
        self.assertEqual(self.pixel(cx,cy),[255,0,0,255])
        offset=self.page.evaluate('Math.min(W(),H())*0.3')
        self.assertEqual(self.pixel(cx-offset,cy-offset),[255,255,255,255])
        # Selecting the same file again works because the input was cleared.
        self.page.locator('#imageUpload').set_input_files(str(ROOT / 'tests/fixtures/closed-square.png'))
        self.page.wait_for_function('imageUpload.value===""');self.settle()
        self.assertEqual(self.pixel(cx,cy),[255,255,255,255])

    def test_11_draw_after_rotation_maps_to_pointer(self):
        v=PROFILES[self.profile_name]['viewport']
        self.page.set_viewport_size(dict(width=v['height'],height=v['width']));self.settle()
        self.stroke([(70,90),(170,90)])
        self.assertGreater(self.pixel(120,90)[3],0)
        self.assertEqual(self.pixel(120,180)[3],0)

    def test_12_rapid_taps_and_dblclick_keep_scale_and_toolbar(self):
        before=self.digest()
        for _ in range(6):self.tap_art(100,100)
        p=self.client(100,100);self.page.mouse.dblclick(p['x'],p['y'])
        self.settle();self.assert_layout()
        self.assertEqual(self.digest()['width'],before['width'])
        self.assertAlmostEqual(self.page.evaluate('visualViewport.scale'),1,delta=.01)
        # Also assert the scoped fallback cancels a cancellable dblclick.
        self.assertTrue(self.page.evaluate('''() => {
          const e=new MouseEvent('dblclick',{bubbles:true,cancelable:true});canvas.dispatchEvent(e);return e.defaultPrevented;
        }'''))

    def test_13_multi_pointer_and_cancel_recovery(self):
        self.page.evaluate('''() => {
          const r=canvas.getBoundingClientRect();
          const e=(type,id,primary,x,y)=>canvas.dispatchEvent(new PointerEvent(type,{pointerId:id,pointerType:'touch',isPrimary:primary,button:0,buttons:type==='pointerup'?0:1,clientX:r.left+x,clientY:r.top+y,bubbles:true,cancelable:true}));
          e('pointerdown',101,true,40,40);e('pointermove',101,true,60,40);
          e('pointerdown',102,false,80,80);e('pointermove',102,false,100,100);e('pointerup',102,false,100,100);
          if(!drawing || activePointerId!==101)throw new Error('Second finger corrupted active stroke');
          e('pointercancel',101,true,60,40);
          if(drawing)throw new Error('Cancelled stroke is stuck');
        }''')
        self.stroke([(80,120),(180,120)]);self.assertGreater(self.pixel(130,120)[3],0)

    def test_14_twenty_step_undo_limit(self):
        before=self.digest()
        for i in range(20):self.stroke([(50,50+i*9),(95,50+i*9)])
        last=self.digest()
        self.assertEqual(self.page.evaluate('history.length'),21)
        for _ in range(20):self.click('#undoBtn');self.settle()
        self.assertEqual(self.digest(),before);self.assertTrue(self.page.locator('#undoBtn').is_disabled())
        for _ in range(20):self.click('#redoBtn');self.settle()
        self.assertEqual(self.digest(),last)

    def test_15_sticker_background_and_png_export(self):
        self.click('[data-bg="#ffe5ef"]');self.click('[data-sticker="⭐"]');self.tap_art(120,120)
        self.assertGreater(self.pixel(120,120)[3],0)
        with self.page.expect_download() as event:self.click('#saveBtn')
        download=event.value;target=self.evidence/f'{self.profile_name}-saved.png';download.save_as(str(target))
        content=target.read_bytes();self.assertTrue(content.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertEqual(int.from_bytes(content[16:20],'big'),self.digest()['width'])
        self.assertEqual(int.from_bytes(content[20:24],'big'),self.digest()['height'])
        # Decode exported PNG through a browser canvas to inspect background.
        import base64
        pixel=self.page.evaluate('''src => new Promise((resolve,reject)=>{
          const im=new Image();im.onload=()=>{const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const x=c.getContext('2d');x.drawImage(im,0,0);resolve(Array.from(x.getImageData(0,0,1,1).data))};im.onerror=reject;im.src=src;
        })''','data:image/png;base64,'+base64.b64encode(content).decode())
        self.assertEqual(pixel,[255,229,239,255])

    def test_16_new_confirmation_does_not_clear_on_cancel(self):
        self.stroke([(70,100),(170,100)]);before=self.digest()
        self.click('#newBtn');self.click('#cancelNew');self.assertEqual(self.digest(),before)
        self.click('#newBtn');self.click('#confirmNew')
        self.assertEqual(self.pixel(120,100)[3],0)

    def test_17_touch_gesture_handlers_scoped_away_from_upload(self):
        result=self.page.evaluate('''() => {
          const surface=document.querySelector('.canvas-stage');
          const a=new Event('touchend',{bubbles:true,cancelable:true});surface.dispatchEvent(a);
          const b=new Event('touchend',{bubbles:true,cancelable:true});imageUpload.dispatchEvent(b);
          const g=new Event('gesturestart',{bubbles:true,cancelable:true});surface.dispatchEvent(g);
          return {surface:a.defaultPrevented,upload:b.defaultPrevented,gesture:g.defaultPrevented,action:getComputedStyle(canvas).touchAction};
        }''')
        self.assertEqual(result,dict(surface=True,upload=False,gesture=True,action='none'))

    def test_18_actual_touch_swipe_draws_without_scrolling(self):
        if not PROFILES[self.profile_name]['has_touch']:self.skipTest('Touch-only case')
        if self.browser.browser_type.name!='chromium':self.skipTest('CDP touch swipe is Chromium-only; verify on real iPad')
        cdp=self.context.new_cdp_session(self.page)
        points=[self.client(70,100),self.client(100,100),self.client(150,100)]
        for i,p in enumerate(points):
            cdp.send('Input.dispatchTouchEvent',dict(type='touchStart' if i==0 else 'touchMove',touchPoints=[dict(x=p['x'],y=p['y'])]))
        cdp.send('Input.dispatchTouchEvent',dict(type='touchEnd',touchPoints=[]))
        self.assertGreater(self.pixel(110,100)[3],0);self.assert_layout()

    def test_19_actual_toolbar_touch_scroll_keeps_header(self):
        if not PROFILES[self.profile_name]['has_touch']:self.skipTest('Touch-only case')
        if self.browser.browser_type.name!='chromium':self.skipTest('CDP touch swipe is Chromium-only')
        r=self.page.locator('.tools').bounding_box();cdp=self.context.new_cdp_session(self.page)
        x=r['x']+r['width']-5;y=r['y']+min(350,r['height']-40)
        for i in range(9):
            cdp.send('Input.dispatchTouchEvent',dict(type='touchStart' if i==0 else 'touchMove',touchPoints=[dict(x=x,y=y-i*20)]))
            self.page.wait_for_timeout(15)
        cdp.send('Input.dispatchTouchEvent',dict(type='touchEnd',touchPoints=[]))
        self.page.wait_for_timeout(150)
        self.assertGreater(self.page.locator('.tools').evaluate('(e)=>e.scrollTop'),0);self.assert_layout()

    def test_20_after_eraser_templates_and_uploads_are_visible(self):
        self.click('#eraserBtn');self.stroke([(80,80),(120,80)])
        self.click('[data-page="cat"]')
        self.assertTrue(self.page.evaluate('ctx.getImageData(0,0,canvas.width,canvas.height).data.some((v,i)=>i%4===3&&v>0)'))
        self.page.locator('#imageUpload').set_input_files(str(ROOT/'tests/fixtures/closed-square.png'))
        self.page.wait_for_function('imageUpload.value===""');self.settle()
        cx,cy=self.page.evaluate('[W()/2,H()/2]');self.assertEqual(self.pixel(cx,cy),[255,255,255,255])

class JsonResult(unittest.TextTestResult):
    records=[]
    def startTest(self,test):super().startTest(test);test._started=time.monotonic()
    def record(self,test,status,detail=''):
        self.records.append(dict(test=test.id(),status=status,seconds=round(time.monotonic()-test._started,3),detail=detail))
    def addSuccess(self,test):super().addSuccess(test);self.record(test,'passed')
    def addFailure(self,test,err):super().addFailure(test,err);self.record(test,'failed',self._exc_info_to_string(err,test))
    def addError(self,test,err):super().addError(test,err);self.record(test,'error',self._exc_info_to_string(err,test))
    def addSkip(self,test,reason):super().addSkip(test,reason);self.record(test,'skipped',reason)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',default='chromium',choices=['chromium','webkit','firefox'])
    parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--evidence',type=Path,default=ROOT/'test-results')
    parser.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=list(PROFILES))
    parser.add_argument('--baseline-only',action='store_true');parser.add_argument('--inline',action='store_true',help='Inject exact local HTML/CSS/JS; excludes HTTP/navigation testing');args=parser.parse_args()
    args.evidence.mkdir(parents=True,exist_ok=True)
    handler=functools.partial(QuietHandler,directory=str(args.root.resolve()))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            engine=getattr(pw,args.browser);launch={}
            custom=os.environ.get('PLAYWRIGHT_EXECUTABLE')
            if custom:launch['executable_path']=custom
            elif args.browser=='chromium' and not Path(engine.executable_path).exists() and shutil.which('chromium'):
                launch['executable_path']=shutil.which('chromium')
            try:browser=engine.launch(headless=True,**launch)
            except Exception as exc:
                (args.evidence/'unavailable.json').write_text(json.dumps(dict(browser=args.browser,error=str(exc)),indent=2))
                print(f'{args.browser} could not be launched: {exc}',file=sys.stderr);return 2
            suite=unittest.TestSuite()
            for profile in args.profiles:
                methods=unittest.defaultTestLoader.getTestCaseNames(BrowserCases)
                if args.baseline_only:methods=[n for n in methods if n.startswith(('test_02','test_03'))]
                cls=type(f'{args.browser}_{profile}',(BrowserCases,),dict(profile_name=profile,browser=browser,inline=args.inline,app_root=args.root,base_url=f'http://127.0.0.1:{server.server_port}/',evidence=args.evidence))
                for name in methods:suite.addTest(cls(name))
            version=browser.version
            result=unittest.TextTestRunner(verbosity=2,resultclass=JsonResult).run(suite)
            report=dict(transport='inline local HTML/CSS/JS' if args.inline else 'local HTTP server',browser=args.browser,browser_version=version,playwright=importlib.metadata.version('playwright'),
                        device_test_type='viewport/DPR/touch emulation; NOT physical hardware',
                        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
                        results=result.records,app_sha256={p:hashlib.sha256((args.root/p).read_bytes()).hexdigest() for p in ['index.html','style.css','app.js']})
            (args.evidence/'browser-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            browser.close();return 0 if result.wasSuccessful() else 1
    finally:server.shutdown();server.server_close()

if __name__=='__main__':sys.exit(main())
