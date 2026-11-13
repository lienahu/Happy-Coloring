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
function snap(){history.push(canvas.toDataURL());if(history.length>21)history.shift();redo=[];if(window.HappyFill)window.HappyFill.remember(history.at(-1),[...history,...redo]);buttons()}
function buttons(){undoBtn.disabled=history.length<2;redoBtn.disabled=!redo.length}
// Do not let an eraser's destination-out mode erase an undo snapshot.
let restoreTicket=0;
function restore(src){
 const ticket=++restoreTicket,im=new Image();
 im.onload=()=>{
   if(ticket!==restoreTicket)return;
   if(window.HappyFill)window.HappyFill.restore(src);
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
 // PATTERN-DISPATCH: normal solid fills retain the accepted implementation.
 if(window.HappyFill && window.HappyFill.needsPatternPath())return window.HappyFill.paint(ctx,canvas,x0,y0,fillHex,W());
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

function clearAll(){if(window.HappyFill)window.HappyFill.reset();++restoreTicket;ctx.clearRect(0,0,W(),H());snap()}
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

// PICTURE-SOURCE-BEGIN: templates and Upload share this one import path.
// The five files are the supplied originals, not CSS backgrounds or extra layers.
const coloringPages=Object.freeze({
 unicorn:"assets/coloring-pages/unicorn.png",
 princess:"assets/coloring-pages/princess.png",
 cat:"assets/coloring-pages/cat.png",
 butterfly:"assets/coloring-pages/butterfly.png",
 dino:"assets/coloring-pages/dinosaur.png"
});
let pictureRequest=0,cancelPictureRequest=null,pictureLoadPending=false;

function pictureLoadError(){
 const fallback="This picture could not be opened. Your drawing is unchanged. Please try again.";
 window.alert(window.HappyI18n ? window.HappyI18n.t("pictureLoadError") : fallback);
}

function loadPictureSource(src,release=()=>{}){
 // A later selection wins. Stop waiting for the earlier image and release its URL.
 if(cancelPictureRequest)cancelPictureRequest();
 const request=++pictureRequest,revision=restoreTicket;
 pictureLoadPending=true;
 return new Promise(resolve=>{
   const im=new Image();let finished=false,timer=null;
   const current=()=>request===pictureRequest && revision===restoreTicket;
   function finish(ok){
     if(finished)return;
     finished=true;clearTimeout(timer);im.onload=null;im.onerror=null;
     if(request===pictureRequest){cancelPictureRequest=null;pictureLoadPending=false;}
     release();resolve(ok);
   }
   function fail(){
     const report=current();finish(false);
     if(report)pictureLoadError();
   }
   cancelPictureRequest=()=>{finish(false);im.src="";};
   im.onload=()=>{
     if(!current()){finish(false);return;}
     // Decode/readability is validated BEFORE clearing the child's existing art.
     // This temporary import buffer is copied 1:1; it is NOT an overlay layer.
     let prepared;
     try{
       const iw=im.naturalWidth||im.width,ih=im.naturalHeight||im.height;
       if(!(iw>0&&ih>0&&W()>0&&H()>0))throw new Error("Invalid image size");
       prepared=document.createElement("canvas");
       prepared.width=canvas.width;prepared.height=canvas.height;
       const pc=prepared.getContext("2d",{willReadFrequently:true});
       pc.setTransform(canvas.width/W(),0,0,canvas.height/H(),0,0);
       const s=Math.min(W()/iw,H()/ih),nw=iw*s,nh=ih*s;
       pc.drawImage(im,(W()-nw)/2,(H()-nh)/2,nw,nh);
       // Refuse unreadable/tainted sources without tainting the real canvas.
       pc.getImageData(0,0,1,1);
     }catch(_){fail();return;}
     if(!current()){finish(false);return;}
     canvasInput.cancel();end();++restoreTicket;
     ctx.save();ctx.globalCompositeOperation="source-over";
     ctx.setTransform(1,0,0,1,0,0);
     ctx.clearRect(0,0,canvas.width,canvas.height);
     ctx.drawImage(prepared,0,0);ctx.restore();if(window.HappyFill)window.HappyFill.reset();snap();
     finish(true);
   };
   im.onerror=fail;
   timer=setTimeout(fail,30000);
   try{im.src=src;}catch(_){fail();}
 });
}

function page(name){
 if(name==="blank"){
   if(cancelPictureRequest)cancelPictureRequest();
   canvasInput.cancel();end();clearAll();return;
 }
 if(Object.prototype.hasOwnProperty.call(coloringPages,name)){
   return loadPictureSource(coloringPages[name]);
 }
}
document.querySelectorAll(".pageBtn").forEach(b=>b.onclick=()=>page(b.dataset.page));

let uploadRequest=0;
imageUpload.onchange=e=>{
 const input=e.target,f=input.files&&input.files[0];if(!f)return;
 const request=++uploadRequest,url=URL.createObjectURL(f);
 return loadPictureSource(url,()=>{
   URL.revokeObjectURL(url);
   // An older request must not clear the selection of a newer upload.
   if(request===uploadRequest)input.value="";
 });
};
// PICTURE-SOURCE-END

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
