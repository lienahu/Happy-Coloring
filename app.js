const canvas=document.getElementById("canvas"),ctx=canvas.getContext("2d",{willReadFrequently:true});
const palette=["#ff4f87","#ff3b30","#ff9500","#ffd60a","#34c759","#00c7be","#0a84ff","#5856d6","#af52de","#8e5a3c","#111111","#ffffff","#ff9fbb","#7ee787","#72d7ff"];
let color=palette[0],size=8,tool="brush",drawing=false,last=null,history=[],redo=[],background="#ffffff",selectedSticker=null;

function W(){return canvas.width/devicePixelRatio} function H(){return canvas.height/devicePixelRatio}
function fitCanvas(){
 const r=canvas.getBoundingClientRect(),old=document.createElement("canvas");old.width=canvas.width;old.height=canvas.height;
 if(old.width&&old.height)old.getContext("2d").drawImage(canvas,0,0);
 canvas.width=Math.max(300,Math.floor(r.width*devicePixelRatio));canvas.height=Math.max(300,Math.floor(r.height*devicePixelRatio));
 ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
 if(old.width&&old.height)ctx.drawImage(old,0,0,old.width,old.height,0,0,r.width,r.height);
}
function snap(){history.push(canvas.toDataURL());if(history.length>20)history.shift();redo=[];buttons()}
function buttons(){undoBtn.disabled=history.length<2;redoBtn.disabled=!redo.length}
function restore(src){const im=new Image();im.onload=()=>{ctx.clearRect(0,0,W(),H());ctx.drawImage(im,0,0,W(),H())};im.src=src}
function p(e){const r=canvas.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top}}

function hex(h){h=h.replace("#","");let n=parseInt(h,16);return[(n>>16)&255,(n>>8)&255,n&255,255]}
function floodFill(xCss,yCss,fillHex){
 const sx=canvas.width/canvas.clientWidth,sy=canvas.height/canvas.clientHeight;
 const x0=Math.floor(xCss*sx),y0=Math.floor(yCss*sy),im=ctx.getImageData(0,0,canvas.width,canvas.height),d=im.data,w=im.width,h=im.height;
 const ii=(y0*w+x0)*4,target=[d[ii],d[ii+1],d[ii+2],d[ii+3]],fill=hex(fillHex),tol=45;
 if(Math.abs(target[0]-fill[0])+Math.abs(target[1]-fill[1])+Math.abs(target[2]-fill[2])<10)return;
 const seen=new Uint8Array(w*h),q=[[x0,y0]];
 while(q.length){
  const [x,y]=q.pop();if(x<0||y<0||x>=w||y>=h)continue;const pos=y*w+x;if(seen[pos])continue;seen[pos]=1;const i=pos*4;
  const diff=Math.abs(d[i]-target[0])+Math.abs(d[i+1]-target[1])+Math.abs(d[i+2]-target[2])+Math.abs(d[i+3]-target[3]);
  if(diff>tol)continue;d[i]=fill[0];d[i+1]=fill[1];d[i+2]=fill[2];d[i+3]=255;
  q.push([x+1,y],[x-1,y],[x,y+1],[x,y-1]);
 }
 ctx.putImageData(im,0,0)
}
function sparkle(a,b){
 let dx=b.x-a.x,dy=b.y-a.y,n=Math.max(1,Math.floor(Math.hypot(dx,dy)/6));
 for(let i=0;i<n;i++){if(Math.random()>.6)continue;let t=Math.random(),x=a.x+dx*t+(Math.random()-.5)*size,y=a.y+dy*t+(Math.random()-.5)*size,r=Math.max(1,size*.08);
  ctx.save();ctx.fillStyle=Math.random()>.35?"#fff":"#fff0a8";ctx.globalAlpha=.9;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();ctx.restore();}
}
function start(e){
 const pt=p(e);
 if(selectedSticker){ctx.save();ctx.font="48px serif";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText(selectedSticker,pt.x,pt.y);ctx.restore();snap();return}
 if(tool==="bucket"){floodFill(pt.x,pt.y,color);snap();return}
 drawing=true;last=pt;ctx.beginPath();ctx.moveTo(pt.x,pt.y);e.preventDefault()
}
function move(e){if(!drawing)return;const pt=p(e);ctx.lineCap="round";ctx.lineJoin="round";ctx.globalCompositeOperation=tool==="eraser"?"destination-out":"source-over";
 ctx.strokeStyle=tool==="outline"?"#22252d":color;ctx.lineWidth=tool==="outline"?Math.max(2,Math.min(size,6)):size;ctx.lineTo(pt.x,pt.y);ctx.stroke();if(tool==="sparkle")sparkle(last,pt);ctx.beginPath();ctx.moveTo(pt.x,pt.y);last=pt;e.preventDefault()}
function end(){if(drawing){drawing=false;ctx.beginPath();snap()}}
canvas.addEventListener("pointerdown",start);canvas.addEventListener("pointermove",move);window.addEventListener("pointerup",end);canvas.addEventListener("pointercancel",end);

const pal=document.getElementById("palette");palette.forEach((c,i)=>{const b=document.createElement("button");b.className="swatch"+(i?"":" active");b.style.background=c;b.onclick=()=>{color=c;selectedSticker=null;document.querySelectorAll(".swatch").forEach(x=>x.classList.remove("active"));b.classList.add("active")};pal.appendChild(b)});
colorPicker.oninput=e=>{color=e.target.value;selectedSticker=null};
document.querySelectorAll(".brush").forEach(b=>b.onclick=()=>{size=+b.dataset.size;document.querySelectorAll(".brush").forEach(x=>x.classList.remove("active"));b.classList.add("active")});
function setTool(t){tool=t;selectedSticker=null;document.querySelectorAll(".stickers button").forEach(x=>x.classList.remove("active"));["brush","sparkle","bucket","outline","eraser"].forEach(n=>document.getElementById(n+"Btn").classList.toggle("active",t===n))}
brushBtn.onclick=()=>setTool("brush");sparkleBtn.onclick=()=>setTool("sparkle");bucketBtn.onclick=()=>setTool("bucket");outlineBtn.onclick=()=>setTool("outline");eraserBtn.onclick=()=>setTool("eraser");
document.querySelectorAll(".stickers button").forEach(b=>b.onclick=()=>{selectedSticker=b.dataset.sticker;document.querySelectorAll(".stickers button").forEach(x=>x.classList.remove("active"));b.classList.add("active")});

undoBtn.onclick=()=>{if(history.length>1){redo.push(history.pop());restore(history.at(-1));buttons()}};
redoBtn.onclick=()=>{if(redo.length){let s=redo.pop();history.push(s);restore(s);buttons()}};
function clearAll(){ctx.clearRect(0,0,W(),H());canvas.style.backgroundImage="none";snap()}
clearBtn.onclick=()=>{if(confirm("Clear this picture?"))clearAll()};
newBtn.onclick=()=>confirmModal.classList.remove("hidden");cancelNew.onclick=()=>confirmModal.classList.add("hidden");confirmNew.onclick=()=>{confirmModal.classList.add("hidden");clearAll()};
saveBtn.onclick=()=>{const out=document.createElement("canvas");out.width=canvas.width;out.height=canvas.height;let o=out.getContext("2d");o.fillStyle=background;o.fillRect(0,0,out.width,out.height);o.drawImage(canvas,0,0);let a=document.createElement("a");a.download="my-coloring.png";a.href=out.toDataURL();a.click()};

document.querySelectorAll(".bg").forEach(b=>b.onclick=()=>{background=b.dataset.bg;canvas.style.background=background;document.querySelectorAll(".bg").forEach(x=>x.classList.remove("active"));b.classList.add("active")});

function line(x1,y1,x2,y2){ctx.moveTo(x1,y1);ctx.lineTo(x2,y2)}
function circle(x,y,r){ctx.moveTo(x+r,y);ctx.arc(x,y,r,0,Math.PI*2)}
function page(name){
 ctx.clearRect(0,0,W(),H());ctx.save();ctx.strokeStyle="#252525";ctx.lineWidth=4;ctx.lineCap="round";ctx.lineJoin="round";ctx.beginPath();
 let w=W(),h=H(),cx=w/2,cy=h/2;
 if(name==="blank"){ctx.restore();snap();return}
 if(name==="unicorn"){circle(cx,cy,110);circle(cx-42,cy-20,9);circle(cx+42,cy-20,9);ctx.moveTo(cx-40,cy+45);ctx.quadraticCurveTo(cx,cy+70,cx+40,cy+45);ctx.moveTo(cx,cy-110);line(cx,cy-110,cx+18,cy-190);line(cx+18,cy-190,cx+42,cy-108);ctx.moveTo(cx-100,cy-55);line(cx-150,cy-100,cx-115,cy-20);ctx.moveTo(cx+100,cy-55);line(cx+150,cy-100,cx+115,cy-20)}
 if(name==="princess"){circle(cx,cy-45,80);ctx.moveTo(cx-80,cy-90);line(cx-50,cy-150,cx-10,cy-105);line(cx-10,cy-105,cx+25,cy-155);line(cx+25,cy-155,cx+75,cy-95);ctx.moveTo(cx-25,cy-20);circle(cx-28,cy-35,7);circle(cx+28,cy-35,7);ctx.moveTo(cx-35,cy+10);ctx.quadraticCurveTo(cx,cy+35,cx+35,cy+10);ctx.moveTo(cx-70,cy+40);line(cx-150,cy+210,cx+150,cy+210);line(cx+150,cy+210,cx+70,cy+40)}
 if(name==="cat"){circle(cx,cy,105);ctx.moveTo(cx-80,cy-75);line(cx-120,cy-150,cx-35,cy-110);ctx.moveTo(cx+80,cy-75);line(cx+120,cy-150,cx+35,cy-110);circle(cx-38,cy-18,9);circle(cx+38,cy-18,9);ctx.moveTo(cx,cy);line(cx-12,cy+18,cx+12,cy+18);ctx.moveTo(cx,cy+18);ctx.quadraticCurveTo(cx-20,cy+40,cx-40,cy+28);ctx.moveTo(cx,cy+18);ctx.quadraticCurveTo(cx+20,cy+40,cx+40,cy+28);[-1,1].forEach(s=>{ctx.moveTo(cx+s*35,cy+10);line(cx+s*125,cy-5,cx+s*155,cy-10);ctx.moveTo(cx+s*35,cy+25);line(cx+s*125,cy+35,cx+s*155,cy+38)})}
 if(name==="butterfly"){ctx.moveTo(cx,cy-100);line(cx,cy+120,cx,cy-100);circle(cx,cy-120,18);ctx.moveTo(cx-5,cy-80);ctx.bezierCurveTo(cx-180,cy-210,cx-210,cy+10,cx-20,cy+20);ctx.moveTo(cx+5,cy-80);ctx.bezierCurveTo(cx+180,cy-210,cx+210,cy+10,cx+20,cy+20);ctx.moveTo(cx-15,cy+15);ctx.bezierCurveTo(cx-150,cy+10,cx-160,cy+180,cx-5,cy+105);ctx.moveTo(cx+15,cy+15);ctx.bezierCurveTo(cx+150,cy+10,cx+160,cy+180,cx+5,cy+105)}
 if(name==="dino"){ctx.moveTo(cx-160,cy+100);ctx.bezierCurveTo(cx-220,cy-40,cx-80,cy-170,cx+40,cy-100);ctx.bezierCurveTo(cx+140,cy-150,cx+180,cy-60,cx+120,cy);ctx.bezierCurveTo(cx+90,cy+30,cx+95,cy+100,cx+160,cy+130);ctx.moveTo(cx-160,cy+100);ctx.bezierCurveTo(cx-40,cy+130,cx+70,cy+120,cx+160,cy+130);circle(cx+65,cy-75,7);ctx.moveTo(cx+100,cy-50);ctx.quadraticCurveTo(cx+125,cy-35,cx+145,cy-48)}
 ctx.stroke();ctx.restore();snap()
}
document.querySelectorAll(".pageBtn").forEach(b=>b.onclick=()=>page(b.dataset.page));

imageUpload.onchange=e=>{const f=e.target.files[0];if(!f)return;const im=new Image();im.onload=()=>{ctx.clearRect(0,0,W(),H());let s=Math.min(W()/im.width,H()/im.height),nw=im.width*s,nh=im.height*s;ctx.drawImage(im,(W()-nw)/2,(H()-nh)/2,nw,nh);snap()};im.src=URL.createObjectURL(f)};

window.addEventListener("resize",fitCanvas);fitCanvas();snap();buttons();
