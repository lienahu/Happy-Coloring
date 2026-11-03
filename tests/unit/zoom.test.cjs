const {test}=require('node:test');
const assert=require('node:assert/strict');
const Z=require('../../canvas-zoom.js');
const {createApp}=require('./harness.cjs');
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} != ${b}`);

test('zoom clamps to fit through 400 percent',()=>{assert.equal(Z.limitZoom(-2),1);assert.equal(Z.limitZoom(9),4);assert.equal(Z.limitZoom(2.5),2.5)});
test('non-finite zoom safely falls back to fit',()=>{for(const n of [NaN,Infinity,-Infinity,undefined])assert.equal(Z.limitZoom(n),1)});
test('invalid geometry is ignored',()=>{for(const n of [0,-5,NaN,Infinity])assert.equal(Z.geometry(n,400,300,400,1),null)});
test('fit centers a portrait paper in a landscape viewport',()=>{const g=Z.geometry(400,800,900,400,1);close(g.scale,.5);close(g.left,350);close(g.top,0);close(g.sw,900);close(g.sh,400)});
test('zoom geometry preserves paper aspect ratio',()=>{const g=Z.geometry(400,800,900,400,4);close(g.width/g.height,.5);close(g.sh,1600)});
test('anchor is held exactly when scrolling is not clamped',()=>{const g=Z.geometry(600,800,600,800,2);const s=Z.scrollForAnchor(g,{x:320,y:410},{x:300,y:400});close(s.x,340);close(s.y,420)});
test('anchor scrolling is bounded at paper edges',()=>{const g=Z.geometry(600,800,600,800,2);assert.deepEqual(Z.scrollForAnchor(g,{x:-100,y:5000},{x:0,y:0}),{x:0,y:800})});
test('fit never has scrolling overflow',()=>{const g=Z.geometry(400,800,900,400,1);assert.deepEqual(Z.scrollForAnchor(g,{x:2000,y:1000},{x:1,y:0}),{x:0,y:0})});
test('midpoint and distance use client coordinates',()=>{const a={clientX:10,clientY:20},b={clientX:40,clientY:60};assert.deepEqual(Z.midpoint(a,b),{x:25,y:40});close(Z.distance(a,b),50)});
test('zoom buttons never write artwork bitmap or history',()=>{const a=createApp();a.ids.zoomInBtn.click();a.ids.zoomInBtn.click();assert.equal(a.writes(),2);assert.equal(a.run('history.length'),1);close(a.run('canvasView.zoom'),1.5625)});
test('Fit resets the view only',()=>{const a=createApp();a.run('canvasView.setZoom(3)');a.ids.zoomFitBtn.click();close(a.run('canvasView.zoom'),1);assert.equal(a.writes(),2);assert.equal(a.stage.scrollLeft,0);assert.equal(a.stage.scrollTop,0)});
test('zoom scroll controls appear only when the paper overflows',()=>{const a=createApp();assert.equal(a.ids.panX.disabled,true);a.ids.zoomInBtn.click();assert.equal(a.ids.panX.disabled,false);assert.equal(a.ids.panY.disabled,false);a.ids.zoomFitBtn.click();assert.equal(a.ids.panX.disabled,true)});
test('scroll slider controls only the canvas viewport',()=>{const a=createApp();a.run('canvasView.setZoom(3)');a.ids.panX.value='100';a.ids.panX.listeners.input[0].f();assert.equal(a.stage.scrollLeft,100);assert.equal(a.writes(),2)});
test('rotation keeps zoom and one artwork bitmap',()=>{const a=createApp();a.run('canvasView.setZoom(2)');a.stage.clientWidth=900;a.stage.clientHeight=400;a.run('fitCanvas()');assert.equal(a.writes(),2);close(a.run('canvasView.zoom'),2);close(a.canvas.clientWidth/a.canvas.clientHeight,.75)});
test('coordinate mapping accounts for canvas zoom',()=>{const a=createApp();a.run('canvasView.setZoom(2)');const p=a.run('p({clientX:210,clientY:220})');close(p.x,100);close(p.y,100)});
test('zoom is absent from the 20-step drawing history',()=>{const a=createApp();a.run('for(let i=0;i<30;i++)canvasView.setZoom(1+(i%4))');assert.equal(a.run('history.length'),1)});

function rig({tapTool=false,external=false,onPaper=true}={}){
 const calls=[],handlers={},v={zoom:1,paperAt:c=>c,setZoom(z,c,p){this.zoom=Z.limitZoom(z);calls.push(['view',this.zoom,c,p])}};
 const vp={addEventListener(t,f){handlers[t]=f},setPointerCapture(){},hasPointerCapture(){return false},releasePointerCapture(){}};
 const cb={externalDrawing:()=>external,onPaper:()=>onPaper,isTapTool:()=>tapTool,
   begin:e=>calls.push(['begin',e.pointerId]),move:e=>calls.push(['move',e.pointerId]),finish:e=>calls.push(['finish',e.pointerId]),
   rollback:()=>calls.push(['rollback']),tap:e=>calls.push(['tap',e.pointerId])};
 const input=new Z.TouchInput({viewport:vp,view:v,callbacks:cb});
 const e=(id,x=0,y=0)=>({pointerId:id,clientX:x,clientY:y,button:0,pointerType:'touch',cancelable:true,preventDefault(){}});
 return {input,calls,v,handlers,e};
}
test('one touch begins pending without painting or filling',()=>{const r=rig();r.input.down(r.e(1));assert.equal(r.input.mode,'pending');assert.equal(r.calls.length,0)});
test('tap tool commits exactly once on release',()=>{const r=rig({tapTool:true});r.input.down(r.e(1));r.input.up(r.e(1));assert.deepEqual(r.calls,[['tap',1]])});
test('two fingers never commit bucket or sticker taps',()=>{const r=rig({tapTool:true});r.input.down(r.e(1));r.input.down(r.e(2,50));r.input.up(r.e(2,50));r.input.up(r.e(1));assert.equal(r.calls.length,0)});
test('finger motion beyond tap tolerance cancels a bucket tap',()=>{const r=rig({tapTool:true});r.input.down(r.e(1));r.input.move(r.e(1,20));r.input.up(r.e(1,20));assert.equal(r.calls.length,0)});
test('movement starts one normal stroke then finishes once',()=>{const r=rig();r.input.down(r.e(1));r.input.move(r.e(1,20));r.input.up(r.e(1,20));assert.deepEqual(r.calls,[['begin',1],['move',1],['finish',1]])});
test('second finger rolls back only the unfinished touch stroke',()=>{const r=rig();r.input.down(r.e(1));r.input.move(r.e(1,20));r.input.down(r.e(2,80));assert.equal(r.calls.filter(c=>c[0]==='rollback').length,1);assert.equal(r.input.mode,'gesture')});
test('pinch distance doubles the view zoom',()=>{const r=rig();r.input.down(r.e(1,0));r.input.down(r.e(2,100));r.input.move(r.e(2,200));close(r.v.zoom,2)});
test('two-finger translation pans without changing zoom',()=>{const r=rig();r.input.down(r.e(1,0));r.input.down(r.e(2,100));r.input.move(r.e(1,20));r.input.move(r.e(2,120));close(r.v.zoom,1);assert.deepEqual(r.calls.at(-1)[2],{x:70,y:0})});
test('one remaining finger after pinch cannot accidentally paint',()=>{const r=rig();r.input.down(r.e(1));r.input.down(r.e(2,100));r.input.up(r.e(2,100));r.input.move(r.e(1,30));r.input.up(r.e(1,30));assert.equal(r.calls.filter(c=>['begin','move','tap'].includes(c[0])).length,0);assert.equal(r.input.mode,'idle')});
test('third finger does not replace the two active pinch anchors',()=>{const r=rig();r.input.down(r.e(1));r.input.down(r.e(2,100));r.input.down(r.e(3,200));assert.deepEqual(r.input.gesture.ids,[1,2]);r.input.up(r.e(1));assert.deepEqual(r.input.gesture.ids,[2,3])});
test('cancelled stroke rolls back and recovers for next touch',()=>{const r=rig();r.input.down(r.e(1));r.input.move(r.e(1,20));r.input.cancelPointer(r.e(1,20));assert.equal(r.input.mode,'idle');assert.deepEqual(r.calls.at(-1),['rollback']);r.input.down(r.e(2));r.input.up(r.e(2));assert.deepEqual(r.calls.at(-1),['tap',2])});
test('blur reset releases all contacts and restores idle',()=>{const r=rig();r.input.down(r.e(1));r.input.down(r.e(2,80));r.input.reset();assert.equal(r.input.points.size,0);assert.equal(r.input.mode,'idle')});
test('rotation cancels gestures until all old contacts lift',()=>{const r=rig();r.input.down(r.e(1));r.input.down(r.e(2,80));r.input.cancel();assert.equal(r.input.mode,'blocked');r.input.move(r.e(2,160));assert.equal(r.calls.length,0);r.input.up(r.e(1));r.input.up(r.e(2));assert.equal(r.input.mode,'idle')});
test('Pencil or mouse active stroke blocks palm touches',()=>{const r=rig({external:true});r.input.down(r.e(1));r.input.down(r.e(2,80));r.input.move(r.e(2,160));assert.equal(r.calls.length,0)});
test('single touch on the gutter never draws',()=>{const r=rig({onPaper:false});r.input.down(r.e(1));r.input.move(r.e(1,20));r.input.up(r.e(1,20));assert.equal(r.calls.length,0)});
test('near-coincident fingertips produce finite zoom',()=>{const r=rig();r.input.down(r.e(1));r.input.down(r.e(2));r.input.move(r.e(2,1));assert.ok(Number.isFinite(r.v.zoom))});
test('foreign pointer cancellation does not end a tracked touch',()=>{const r=rig();r.input.down(r.e(1));r.input.cancelPointer(r.e(9));assert.equal(r.input.mode,'pending');assert.equal(r.input.points.size,1)});
