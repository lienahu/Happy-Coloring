const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const m=require('../../selection-resize.js'),ui=require('../../mobile-ui.js'),i18n=require('../../i18n.js');
const root=path.resolve(__dirname,'../..'),read=f=>fs.readFileSync(path.join(root,f),'utf8').replace(/\r\n/g,'\n');
for(const [n,want] of [[NaN,1],[Infinity,1],[-Infinity,1],[0,.25],[-2,.25],[.25,.25],[.5,.5],[1,1],[1.75,1.75],[3,3],[10,3]])
 test(`selection scale ${n} has bounded value ${want}`,()=>assert.equal(m.limitScale(n),want));
for(const [a,b,want] of [
 [{x:10,y:20},{x:80,y:70},{x:10,y:20,width:70,height:50}],
 [{x:80,y:70},{x:10,y:20},{x:10,y:20,width:70,height:50}],
 [{x:-5,y:-6},{x:110,y:120},{x:0,y:0,width:100,height:100}],
 [{x:10.2,y:20.7},{x:31.2,y:40.7},{x:10,y:20,width:22,height:21}],
 [{x:0,y:0},{x:0,y:0},null],
 [{x:120,y:0},{x:130,y:10},null],
 [{x:NaN,y:0},{x:10,y:10},null]
])test(`rectangle normalizes/clamps ${JSON.stringify([a,b])}`,()=>assert.deepEqual(m.rectFromPoints(a,b,100,100),want));
for(const scale of [.25,.5,1,1.5,2,3])test(`scale ${scale} keeps center and aspect`,()=>{
 const d=m.scaledDestination(120,80,scale);assert.equal(d.x+d.width/2,60);assert.equal(d.y+d.height/2,40);assert.equal(d.width/d.height,1.5);
});
for(const [zoom,dpr] of [[1,1],[2,2],[4,3]])test(`pointer map at zoom ${zoom} DPR ${dpr}`,()=>{
 const box={left:-60,top:50,width:300*zoom,height:200*zoom};
 assert.deepEqual(m.bitmapPoint({clientX:box.left+150*zoom,clientY:box.top+100*zoom},box,300*dpr,200*dpr),{x:150*dpr,y:100*dpr});
});
test('pointer outside paper is clipped to its edges',()=>assert.deepEqual(m.bitmapPoint({clientX:-20,clientY:900},{left:0,top:0,width:100,height:100},200,200),{x:0,y:200}));
test('zero-width mapping returns null',()=>assert.equal(m.bitmapPoint({clientX:1,clientY:1},{left:0,top:0,width:0,height:100},200,200),null));
for(const [key,value] of Object.entries({toolsSection:['toolsSection'],colorsSection:['colorsSection','backgroundSection'],pagesSection:['pagesSection','uploadSection'],stickersSection:['stickersSection']}))
 test(`panel ${key} includes only its own related controls`,()=>assert.deepEqual(ui.panelSections(key),value));
for(const key of ['','unknown','__proto__','constructor',null])test(`unknown panel ${key} falls back safely`,()=>assert.deepEqual(ui.panelSections(key),['toolsSection']));
test('panel results cannot mutate shared configuration',()=>{ui.panelSections('pagesSection').push('toolsSection');assert.deepEqual(ui.panelSections('pagesSection'),['pagesSection','uploadSection'])});
const html=read('index.html');
test('exactly five brush widths and no duplicate size buttons',()=>{
 const sizes=[...html.matchAll(/data-size="(\d+)"/g)].map(m=>Number(m[1]));assert.deepEqual(sizes,[2,8,16,28,44]);
});
test('size picker starts hidden and has its own heading',()=>{assert.match(html,/<section id="sizesSection"[^>]* hidden/);assert.match(html,/aria-labelledby="brushSizesTitle"/)});
test('size picker is immediately after brush, before sparkle',()=>assert.ok(html.indexOf('id="brushBtn"')<html.indexOf('id="sizesSection"')&&html.indexOf('id="sizesSection"')<html.indexOf('id="sparkleBtn"')));
for(const id of ['brushBtn','sparkleBtn','outlineBtn','eraserBtn'])test(`${id} discloses a single shared size picker`,()=>assert.match(html,new RegExp('aria-controls="sizesSection" aria-expanded="false" id="'+id+'"')));
test('selection is a separate module loaded after engine',()=>assert.ok(html.indexOf('src="selection-resize.js')>html.indexOf('src="app.js')));
for(const locale of ['en','fr','pt','es','zh-Hans','ja','ko'])test(`${locale} translates all contextual and selection strings`,()=>{
 for(const key of ['extraSmall','extraSmallShort','selectArea','selectShort','selectionTitle','selectHint','resizeHint','selectionCancel','selectionApply','selectionAgain','selectionScale','selectionSmaller','selectionLarger','selectionMin','selectionStale','selectionError']) {
  assert.ok(i18n.dictionaries[locale][key]);assert.notEqual(i18n.translate(locale,key),key);
 }
});
const expected={'app.js':'78e6d602292864f19d58405bcbb07d5ec5de2c54','canvas-zoom.js':'a72eb0844b6bd879dc8d109dcbc92c936f2a6346'};
for(const [f,h] of Object.entries(expected))test(`${f} outside explicit pattern hooks matches accepted baseline`,()=>{
 const b=Buffer.from(f==='app.js'?require('./fill-source-bridge.cjs').withoutFillHooks(read(f)):read(f));assert.equal(crypto.createHash('sha1').update(Buffer.concat([Buffer.from(`blob ${b.length}\0`),b])).digest('hex'),h);
});
test('selection cannot rescale or resize the whole artwork canvas',()=>assert.doesNotMatch(read('selection-resize.js'),/paper\.(?:width|height)\s*=(?!=)/));
test('selection uses a read-only preview until Apply',()=>{const s=read('selection-resize.js');assert.ok(s.includes('ctx.putImageData(result,r.x,r.y)'));assert.ok(s.includes('paper.toDataURL()!==stamp'));assert.ok(s.includes('snap();finish()'))});
