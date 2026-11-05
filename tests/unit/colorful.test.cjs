const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const ui=require('../../mobile-ui.js');
for(const [w,h,compact,landscape] of [[393,852,true,false],[852,393,true,true],[667,375,true,true],[568,320,true,true],[320,568,true,false],[1024,500,true,true],[1180,820,false,false],[820,1180,false,false],[507,1024,true,false],[1280,800,false,false]]) {
 test(`responsive classification ${w}x${h}`,()=>{assert.equal(ui.isCompact(w,h),compact);assert.equal(ui.isPhoneLandscape(w,h),landscape)});
}


test('large view preserves scale aspect using one scalar',()=>{assert.equal(ui.coverZoom(400,800,800,400),4)});
test('matched aspect needs no additional zoom',()=>assert.equal(ui.coverZoom(800,400,800,400),1));
test('large view clamps to the existing 400 percent zoom maximum',()=>assert.equal(ui.coverZoom(200,1200,900,250),4));
test('invalid/zero geometry is harmless',()=>{for(const dims of [[0,2,3,4],[1,NaN,3,4],[1,2,3,-1]])assert.equal(ui.coverZoom(...dims),1)});
test('narrower wide paper uses width cover correctly',()=>assert.ok(Math.abs(ui.coverZoom(756,320,756,306)-320/306)<1e-8));
test('all six runtime dependencies exist and are referenced',()=>{const root=path.resolve(__dirname,'../..'),html=fs.readFileSync(path.join(root,'index.html'),'utf8');for(const f of ['style.css','apple-colorful.css','canvas-zoom.js','app.js','mobile-ui.js']){assert.ok(html.includes(f));assert.ok(fs.existsSync(path.join(root,f)))} });

const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const css=fs.readFileSync(path.join(root,'apple-colorful.css'),'utf8');
const js=fs.readFileSync(path.join(root,'mobile-ui.js'),'utf8');
test('only fixed Colorful marker is shipped',()=>{assert.match(html,/data-ui="colorful-1"/);assert.doesNotMatch(html,/data-theme=/)});
test('style button and picker are removed, not just hidden',()=>assert.doesNotMatch(html,/id="(?:themeBtn|themeDialog|closeTheme)"|data-theme-choice/));
test('old theme APIs cannot be invoked',()=>{assert.equal(ui.THEMES,undefined);assert.equal(ui.themeOrDefault,undefined);assert.doesNotMatch(js,/setTheme|currentTheme/)});
test('saved preferences and URL theme parameter are not consumed',()=>assert.doesNotMatch(js,/localStorage|sessionStorage|URLSearchParams|location.search/));
test('stylesheet has no selectable palette branches',()=>assert.doesNotMatch(css,/\[data-theme|sample-candy|sample-ocean|sample-forest|sample-space/));
test('built-in canvas and UI color layers are kept separate',()=>{assert.doesNotMatch(js,/ctx\.|getContext|toDataURL|canvas.width\s*=/);assert.match(css,/--accent:#6b36d8/)});
test('accessible labels and pressed states are provided',()=>{assert.match(js,/aria-label/);assert.match(js,/aria-pressed/)});
test('opaque fallback and reduced transparency fallback included',()=>{assert.match(css,/@supports not/);assert.match(css,/prefers-reduced-transparency/)});
test('reduced motion and forced colors remain supported',()=>{assert.match(css,/prefers-reduced-motion/);assert.match(css,/forced-colors/)});
test('native file picker remains in the markup',()=>{assert.match(html,/id="imageUpload"/);assert.match(html,/type="file"/)});
test('all DOM IDs are unique',()=>{const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);assert.equal(ids.length,new Set(ids).size)});
test('no external runtime font/script/style dependencies',()=>{assert.doesNotMatch(html,/(?:href|src)="https?:/);assert.doesNotMatch(css,/@import|@font-face/)});
