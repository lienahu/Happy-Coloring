const canvas=document.getElementById("canvas"),ctx=canvas.getContext("2d",{willReadFrequently:true});

// Only mirror the visible viewport at normal scale. Pinch zoom must not
// become a new document size or trigger a destructive canvas resize.
function syncAppHeight(){
  const vv=window.visualViewport;
  if(vv && Math.abs(vv.scale-1)>0.02)return;
  const height=vv ? Math.min(window.innerHeight,vv.height) : window.innerHeight;
  if(height>0)document.documentElement.style.setProperty("--app-height",`${height}px`);
}

const palette=["#ff4f87","#ff3b30","#ff9500","#ffd60a","#34c759","#00c7be","#0a84ff","#5856d6","#af52de","#8e5a3c","#111111","#ffffff","#ff9fbb","#7ee787","#72d7ff"];
let color=palette[0],size=8,tool="brush",drawing=false,last=null,history=[],redo=[],background="#ffffff",selectedSticker=null;

// Artwork coordinates are established once per page load, not per resize.
// The bitmap and undo history survive rotation without resampling.
const canvasStage=document.querySelector(".canvas-stage");
let paperWidth=0,paperHeight=0;
let activePointerId=null;
let canvasView=null,canvasInput=null;
function W(){return paperWidth}
function H(){return paperHeight}
function fitCanvas(){
  const availableW=canvasStage.clientWidth,availableH=canvasStage.clientHeight;
  if(availableW<1 || availableH<1)return;
  if(!paperWidth){
    paperWidth=Math.max(320,Math.round(availableW));
    paperHeight=Math.max(320,Math.round(availableH));
    // Lock resolution for this drawing. Limit mobile bitmap memory at DPR > 2.
    const ratio=Math.min(2,Math.max(1,window.devicePixelRatio||1));
    canvas.width=Math.round(paperWidth*ratio);
    canvas.height=Math.round(paperHeight*ratio);
    ctx.setTransform(canvas.width/paperWidth,0,0,canvas.height/paperHeight,0,0);
  }
  canvasView.reflow();
}
function snap(){history.push(canvas.toDataURL());if(history.length>21)history.shift();redo=[];buttons()}
function buttons(){undoBtn.disabled=history.length<2;redoBtn.disabled=!redo.length}
// Do not let an eraser's destination-out mode erase an undo snapshot.
let restoreTicket=0;
function restore(src){
 const ticket=++restoreTicket,im=new Image();
 im.onload=()=>{
   if(ticket!==restoreTicket)return;
   ctx.save();ctx.globalCompositeOperation="source-over";
   ctx.clearRect(0,0,W(),H());ctx.drawImage(im,0,0,W(),H());ctx.restore();
 };
 im.src=src;
}
function p(e){
 const r=canvas.getBoundingClientRect();
 return {x:(e.clientX-r.left)*W()/r.width,y:(e.clientY-r.top)*H()/r.height};
}

function hex(h){h=h.replace("#","");let n=parseInt(h,16);return[(n>>16)&255,(n>>8)&255,n&255,255]}
function floodFill(xCss,yCss,fillHex){
 // p(e) now returns stable artwork coordinates, not display pixels.
 const sx=canvas.width/W(),sy=canvas.height/H();
 const x0=Math.floor(xCss*sx),y0=Math.floor(yCss*sy);
 if(x0<0||y0<0||x0>=canvas.width||y0>=canvas.height)return;
 const im=ctx.getImageData(0,0,canvas.width,canvas.height),d=im.data,w=im.width,h=im.height;
 const ii=(y0*w+x0)*4,target=[d[ii],d[ii+1],d[ii+2],d[ii+3]],fill=hex(fillHex),tol=45;
 if(Math.abs(target[0]-fill[0])+Math.abs(target[1]-fill[1])+Math.abs(target[2]-fill[2])+Math.abs(target[3]-fill[3])<10)return;
 const seen=new Uint8Array(w*h),q=[[x0,y0]];
 while(q.length){
  const [x,y]=q.pop();
  if(x<0||y<0||x>=w||y>=h)continue;
  const pos=y*w+x;if(seen[pos])continue;seen[pos]=1;const i=pos*4;
  const diff=Math.abs(d[i]-target[0])+Math.abs(d[i+1]-target[1])+Math.abs(d[i+2]-target[2])+Math.abs(d[i+3]-target[3]);
  if(diff>tol)continue;
  d[i]=fill[0];d[i+1]=fill[1];d[i+2]=fill[2];d[i+3]=255;
  q.push([x+1,y],[x-1,y],[x,y+1],[x,y-1]);
 }
 ctx.putImageData(im,0,0)
}
function sparkle(a,b){
 let dx=b.x-a.x,dy=b.y-a.y,n=Math.max(1,Math.floor(Math.hypot(dx,dy)/6));
 for(let i=0;i<n;i++){
  if(Math.random()>.6)continue;
  let t=Math.random(),x=a.x+dx*t+(Math.random()-.5)*size,y=a.y+dy*t+(Math.random()-.5)*size,r=Math.max(1,size*.08);
  ctx.save();ctx.fillStyle=Math.random()>.35?"#fff":"#fff0a8";ctx.globalAlpha=.9;
  ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();ctx.restore();
 }
}
function start(e,capture=true){
 if(!paperWidth || activePointerId!==null || e.isPrimary===false || e.button!==0)return;
 if(e.cancelable)e.preventDefault();
 const pt=p(e);
 if(pt.x<0||pt.y<0||pt.x>=W()||pt.y>=H())return;
 ++restoreTicket;
 // A previous eraser stroke must not erase a subsequent sticker.
 ctx.globalCompositeOperation="source-over";
 if(selectedSticker){
   ctx.save();ctx.font="48px serif";ctx.textAlign="center";ctx.textBaseline="middle";
   ctx.fillText(selectedSticker,pt.x,pt.y);ctx.restore();snap();return;
 }
 if(tool==="bucket"){floodFill(pt.x,pt.y,color);snap();return}
 activePointerId=e.pointerId;drawing=true;last=pt;ctx.beginPath();ctx.moveTo(pt.x,pt.y);
 if(capture && canvas.setPointerCapture){try{canvas.setPointerCapture(e.pointerId)}catch(_){}}
 e.preventDefault()
}
function move(e){
 if(!drawing || e.pointerId!==activePointerId)return;
 const pt=p(e);
 ctx.lineCap="round";ctx.lineJoin="round";
 ctx.globalCompositeOperation=tool==="eraser"?"destination-out":"source-over";
 ctx.strokeStyle=tool==="outline"?"#22252d":color;
 ctx.lineWidth=tool==="outline"?Math.max(2,Math.min(size,6)):size;
 ctx.lineTo(pt.x,pt.y);ctx.stroke();
 if(tool==="sparkle")sparkle(last,pt);
 ctx.beginPath();ctx.moveTo(pt.x,pt.y);last=pt;e.preventDefault()
}
function end(e){
 if(e && activePointerId!==null && e.pointerId!==activePointerId)return;
 const pointerId=activePointerId;
 activePointerId=null;
 if(drawing){drawing=false;ctx.beginPath();snap()}
 if(pointerId!==null && canvas.hasPointerCapture(pointerId)){
   canvas.releasePointerCapture(pointerId);
 }
}

// Canvas-only zoom does not resize the bitmap or add undo entries.
canvasView=new CanvasZoom.View({
 canvas,viewport:canvasStage,surface:document.getElementById("canvasSurface"),
 getSize:()=>({width:W(),height:H()}),
 controls:{out:document.getElementById("zoomOutBtn"),in:document.getElementById("zoomInBtn"),
   fit:document.getElementById("zoomFitBtn"),label:document.getElementById("zoomLabel"),
   x:document.getElementById("panX"),y:document.getElementById("panY")},
 beforeResize:()=>{if(canvasInput)canvasInput.cancel();end()},
 beforeControl:()=>{if(canvasInput)canvasInput.cancel();end()}
});

// Reusable rollback buffer, allocated only when a finger starts an actual stroke.
// A second finger cancels that unfinished preview, not the last committed drawing.
let touchBackup=null;
function backupTouchStroke(){
 if(!touchBackup)touchBackup=document.createElement("canvas");
 if(touchBackup.width!==canvas.width)touchBackup.width=canvas.width;
 if(touchBackup.height!==canvas.height)touchBackup.height=canvas.height;
 const b=touchBackup.getContext("2d");
 b.clearRect(0,0,touchBackup.width,touchBackup.height);b.drawImage(canvas,0,0);
}
function rollbackTouchStroke(){
 ++restoreTicket;
 activePointerId=null;drawing=false;last=null;ctx.beginPath();
 if(!touchBackup)return;
 ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.globalCompositeOperation="source-over";
 ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(touchBackup,0,0);ctx.restore();
}
canvasInput=new CanvasZoom.TouchInput({viewport:canvasStage,view:canvasView,callbacks:{
 externalDrawing:()=>activePointerId!==null && canvasInput.mode!=="drawing",
 onPaper:e=>{const q=p(e);return q.x>=0&&q.y>=0&&q.x<W()&&q.y<H()},
 isTapTool:()=>tool==="bucket"||Boolean(selectedSticker),
 begin:e=>{backupTouchStroke();start(e,false)},
 move:e=>move(e),finish:e=>end(e),rollback:rollbackTouchStroke,
 tap:e=>{
   const tap={pointerId:e.pointerId,button:0,isPrimary:true,clientX:e.clientX,clientY:e.clientY,
     cancelable:false,preventDefault(){}};
   start(tap,false);
   if(drawing){move({...tap,clientX:tap.clientX+0.01});end(tap)}
 }
}});
// Pencil and mouse retain their existing renderer and pointer capture.
canvas.addEventListener("pointerdown",e=>{
 if(e.pointerType==="touch")return;
 if(e.button!==0)return;
 canvasInput.cancel();start(e);
});
canvas.addEventListener("pointermove",e=>{if(e.pointerType!=="touch")move(e)});
["pointerup","pointercancel","lostpointercapture"].forEach(type=>{
 canvas.addEventListener(type,e=>{if(e.pointerType!=="touch")end(e)});
});
window.addEventListener("blur",()=>{canvasInput.reset();end()});
document.addEventListener("visibilitychange",()=>{if(document.hidden){canvasInput.reset();end()}});

// Safari fallback, scoped to the drawing surface. Pointer events still draw.
// Never cancel ordinary file-input/button touchend events on the whole document.
function cancelNativeGesture(e){if(e.cancelable)e.preventDefault()}
["touchstart","touchmove","touchend"].forEach(type=>{
 canvasStage.addEventListener(type,cancelNativeGesture,{passive:false});
});
document.querySelectorAll("header,.tools,.canvas-wrap").forEach(region=>{
 ["gesturestart","gesturechange","gestureend"].forEach(type=>{
   region.addEventListener(type,cancelNativeGesture,{passive:false});
 });
 // Single-finger toolbar scrolling and native Upload taps remain untouched.
 region.addEventListener("touchstart",e=>{
   if(e.touches.length>1)cancelNativeGesture(e);
 },{passive:false});
 region.addEventListener("dblclick",e=>{
   if(!e.target.closest("input,label"))cancelNativeGesture(e);
 });
});
canvasStage.addEventListener("contextmenu",cancelNativeGesture);

const pal=document.getElementById("palette");
palette.forEach((c,i)=>{
 const b=document.createElement("button");
 b.className="swatch"+(i?"":" active");b.style.background=c;
 b.onclick=()=>{
   color=c;selectedSticker=null;
   document.querySelectorAll(".swatch").forEach(x=>x.classList.remove("active"));b.classList.add("active")
 };
 pal.appendChild(b)
});
colorPicker.oninput=e=>{color=e.target.value;selectedSticker=null};

document.querySelectorAll(".brush").forEach(b=>b.onclick=()=>{
 size=+b.dataset.size;
 document.querySelectorAll(".brush").forEach(x=>x.classList.remove("active"));b.classList.add("active")
});

function setTool(t){
 canvasInput.cancel();end();
 tool=t;selectedSticker=null;
 document.querySelectorAll(".stickers button").forEach(x=>x.classList.remove("active"));
 ["brush","sparkle","bucket","outline","eraser"].forEach(n=>document.getElementById(n+"Btn").classList.toggle("active",t===n))
}
brushBtn.onclick=()=>setTool("brush");
sparkleBtn.onclick=()=>setTool("sparkle");
bucketBtn.onclick=()=>setTool("bucket");
outlineBtn.onclick=()=>setTool("outline");
eraserBtn.onclick=()=>setTool("eraser");

document.querySelectorAll(".stickers button").forEach(b=>b.onclick=()=>{
 selectedSticker=b.dataset.sticker;
 document.querySelectorAll(".stickers button").forEach(x=>x.classList.remove("active"));b.classList.add("active")
});

undoBtn.onclick=()=>{if(history.length>1){redo.push(history.pop());restore(history.at(-1));buttons()}};
redoBtn.onclick=()=>{if(redo.length){let s=redo.pop();history.push(s);restore(s);buttons()}};

function clearAll(){++restoreTicket;ctx.clearRect(0,0,W(),H());snap()}
clearBtn.onclick=()=>{if(confirm(window.HappyI18n ? window.HappyI18n.t("clearQuestion") : "Clear this picture?"))clearAll()};
newBtn.onclick=()=>confirmModal.classList.remove("hidden");
cancelNew.onclick=()=>confirmModal.classList.add("hidden");
confirmNew.onclick=()=>{confirmModal.classList.add("hidden");clearAll()};

// Keep export UI separate from the drawing and gesture engines.
saveBtn.onclick=()=>window.HappySave.open(canvas,background,saveBtn);

document.querySelectorAll(".bg").forEach(b=>b.onclick=()=>{
 background=b.dataset.bg;canvas.style.background=background;
 document.querySelectorAll(".bg").forEach(x=>x.classList.remove("active"));b.classList.add("active")
});

function line(x1,y1,x2,y2){ctx.moveTo(x1,y1);ctx.lineTo(x2,y2)}
function circle(x,y,r){ctx.moveTo(x+r,y);ctx.arc(x,y,r,0,Math.PI*2)}
function page(name){
 ++restoreTicket;ctx.clearRect(0,0,W(),H());ctx.save();ctx.globalCompositeOperation="source-over";ctx.strokeStyle="#252525";ctx.lineWidth=4;ctx.lineCap="round";ctx.lineJoin="round";ctx.beginPath();
 let w=W(),h=H(),cx=w/2,cy=h/2;
 if(name==="blank"){ctx.restore();snap();return}
 if(name==="unicorn"){circle(cx,cy,110);circle(cx-42,cy-20,9);circle(cx+42,cy-20,9);ctx.moveTo(cx-40,cy+45);ctx.quadraticCurveTo(cx,cy+70,cx+40,cy+45);ctx.moveTo(cx,cy-110);line(cx,cy-110,cx+18,cy-190);line(cx+18,cy-190,cx+42,cy-108);ctx.moveTo(cx-100,cy-55);line(cx-150,cy-100,cx-115,cy-20);ctx.moveTo(cx+100,cy-55);line(cx+150,cy-100,cx+115,cy-20)}
 if(name==="princess"){circle(cx,cy-45,80);ctx.moveTo(cx-80,cy-90);line(cx-50,cy-150,cx-10,cy-105);line(cx-10,cy-105,cx+25,cy-155);line(cx+25,cy-155,cx+75,cy-95);ctx.moveTo(cx-25,cy-20);circle(cx-28,cy-35,7);circle(cx+28,cy-35,7);ctx.moveTo(cx-35,cy+10);ctx.quadraticCurveTo(cx,cy+35,cx+35,cy+10);ctx.moveTo(cx-70,cy+40);line(cx-150,cy+210,cx+150,cy+210);line(cx+150,cy+210,cx+70,cy+40)}
 if(name==="cat"){circle(cx,cy,105);ctx.moveTo(cx-80,cy-75);line(cx-120,cy-150,cx-35,cy-110);ctx.moveTo(cx+80,cy-75);line(cx+120,cy-150,cx+35,cy-110);circle(cx-38,cy-18,9);circle(cx+38,cy-18,9);ctx.moveTo(cx,cy);line(cx-12,cy+18,cx+12,cy+18);ctx.moveTo(cx,cy+18);ctx.quadraticCurveTo(cx-20,cy+40,cx-40,cy+28);ctx.moveTo(cx,cy+18);ctx.quadraticCurveTo(cx+20,cy+40,cx+40,cy+28)}
 if(name==="butterfly"){ctx.moveTo(cx,cy-100);line(cx,cy+120,cx,cy-100);circle(cx,cy-120,18);ctx.moveTo(cx-5,cy-80);ctx.bezierCurveTo(cx-180,cy-210,cx-210,cy+10,cx-20,cy+20);ctx.moveTo(cx+5,cy-80);ctx.bezierCurveTo(cx+180,cy-210,cx+210,cy+10,cx+20,cy+20);ctx.moveTo(cx-15,cy+15);ctx.bezierCurveTo(cx-150,cy+10,cx-160,cy+180,cx-5,cy+105);ctx.moveTo(cx+15,cy+15);ctx.bezierCurveTo(cx+150,cy+10,cx+160,cy+180,cx+5,cy+105)}
 if(name==="dino"){ctx.moveTo(cx-160,cy+100);ctx.bezierCurveTo(cx-220,cy-40,cx-80,cy-170,cx+40,cy-100);ctx.bezierCurveTo(cx+140,cy-150,cx+180,cy-60,cx+120,cy);ctx.bezierCurveTo(cx+90,cy+30,cx+95,cy+100,cx+160,cy+130);ctx.moveTo(cx-160,cy+100);ctx.bezierCurveTo(cx-40,cy+130,cx+70,cy+120,cx+160,cy+130);circle(cx+65,cy-75,7)}
 ctx.stroke();ctx.restore();snap()
}
document.querySelectorAll(".pageBtn").forEach(b=>b.onclick=()=>page(b.dataset.page));

imageUpload.onchange=e=>{
 const f=e.target.files&&e.target.files[0];if(!f)return;
 const url=URL.createObjectURL(f),im=new Image();
 im.onload=()=>{
   ++restoreTicket;
   ctx.save();ctx.globalCompositeOperation="source-over";
   ctx.clearRect(0,0,W(),H());
   let s=Math.min(W()/im.width,H()/im.height),nw=im.width*s,nh=im.height*s;
   ctx.drawImage(im,(W()-nw)/2,(H()-nh)/2,nw,nh);
   ctx.restore();snap();
   URL.revokeObjectURL(url);
   e.target.value="";
 };
 im.src=url;
};

// Layout can change on every browser-toolbar animation. Only CSS changes;
// canvas.width/canvas.height are never reassigned after first initialization.
let layoutFrame=0;
function scheduleLayout(){
 if(layoutFrame)return;
 layoutFrame=requestAnimationFrame(()=>{
   layoutFrame=0;
   syncAppHeight();
   fitCanvas();
 });
}
window.addEventListener("resize",scheduleLayout,{passive:true});
window.addEventListener("orientationchange",scheduleLayout,{passive:true});
window.addEventListener("pageshow",scheduleLayout,{passive:true});
if(window.visualViewport)window.visualViewport.addEventListener("resize",scheduleLayout,{passive:true});
if("ResizeObserver" in window){
 const observer=new ResizeObserver(scheduleLayout);
 observer.observe(canvasStage);
}
syncAppHeight();fitCanvas();snap();buttons();
