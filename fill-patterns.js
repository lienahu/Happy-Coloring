/* Fill patterns: region membership is separate from decorative pixels.
 * Pure helpers are exported for tests. Uses the SAME 4-neighbour RGBA tolerance
 * as the accepted solid Fill. A span mask limits writes to the selected region.
 * Record snapshots make pattern->pattern and pattern->solid re-fill undoable.
 */
(function(root){
 'use strict';
 const STYLES=Object.freeze(['solid','sparkle','horizontal','vertical','diagonalLeft','diagonalRight','waves','dots','stars','triangles','hearts','flowers','checker','grid','diamonds']);
 const validStyle=id=>STYLES.includes(id)?id:'solid';
 function rgb(hex){
   if(typeof hex!=='string'||!/^#[0-9a-f]{6}$/i.test(hex))throw new TypeError('Expected #RRGGBB');
   const n=parseInt(hex.slice(1),16);return [n>>>16,(n>>>8)&255,n&255,255];
 }
 function region(data,w,h,x,y,labels=null,tolerance=45){
   if(!Number.isInteger(w)||!Number.isInteger(h)||w<1||h<1||data.length!==w*h*4)throw new RangeError('Invalid bitmap');
   x=Math.floor(x);y=Math.floor(y);
   const mask=new Uint8Array(w*h),spans=[];
   if(!Number.isFinite(x)||!Number.isFinite(y)||x<0||y<0||x>=w||y>=h)return {mask,spans:new Uint32Array(),count:0};
   const seed=y*w+x,i=seed*4,target=[data[i],data[i+1],data[i+2],data[i+3]],label=labels?labels[seed]:0;
   const matches=p=>{
     if(mask[p])return false;
     if(label)return labels[p]===label;
     if(labels&&labels[p])return false;
     const j=p*4;return Math.abs(data[j]-target[0])+Math.abs(data[j+1]-target[1])+Math.abs(data[j+2]-target[2])+Math.abs(data[j+3]-target[3])<=tolerance;
   };
   const stack=[seed];let count=0;
   while(stack.length){
     const p=stack.pop();if(!matches(p))continue;
     const row=Math.floor(p/w),min=row*w,max=min+w;let left=p;
     while(left>min&&matches(left-1))left--;
     let q=left,above=false,below=false;
     while(q<max&&matches(q)){
       mask[q]=1;count++;
       if(row>0){const ok=matches(q-w);if(ok&&!above)stack.push(q-w);above=ok;}
       if(row<h-1){const ok=matches(q+w);if(ok&&!below)stack.push(q+w);below=ok;}
       q++;
     }
     spans.push(left,q-left);
   }
   return {mask,spans:Uint32Array.from(spans),count};
 }
 function subtract(spans,mask){
   const out=[];
   for(let k=0;k<spans.length;k+=2){let start=-1,end=spans[k]+spans[k+1];
     for(let p=spans[k];p<end;p++){
       if(!mask[p]){if(start<0)start=p;}
       else if(start>=0){out.push(start,p-start);start=-1;}
     }
     if(start>=0)out.push(start,end-start);
   }
   return Uint32Array.from(out);
 }
 function tileIndex(rec,p,w){return (((Math.floor(p/w)%rec.tile.height)*rec.tile.width)+(p%w)%rec.tile.width)*4;}
 function labelsFor(records,data,w,h){
   const labels=new Uint32Array(w*h);
   records.forEach((rec,index)=>{
     for(let k=0;k<rec.spans.length;k+=2){const end=rec.spans[k]+rec.spans[k+1];for(let p=rec.spans[k];p<end;p++){
       const i=p*4,j=tileIndex(rec,p,w),t=rec.tile.data;
       // New brush marks/erasing are NOT flattened; they become new boundaries.
       if(data[i]===t[j]&&data[i+1]===t[j+1]&&data[i+2]===t[j+2]&&data[i+3]===t[j+3])labels[p]=index+1;
     }}
   });return labels;
 }
 function paintPixels(data,w,spans,tile){
   let changed=false;
   for(let k=0;k<spans.length;k+=2){const end=spans[k]+spans[k+1];for(let p=spans[k];p<end;p++){
     const i=p*4,j=((Math.floor(p/w)%tile.height)*tile.width+(p%w)%tile.width)*4;
     for(let c=0;c<4;c++){if(data[i+c]!==tile.data[j+c])changed=true;data[i+c]=tile.data[j+c];}
   }}return changed;
 }
 function makeTile(style,hex,ratio=1){
   style=validStyle(style);const rgba=rgb(hex),factor=Math.max(1,Math.min(3,ratio));
   const side=style==='solid'?1:Math.round(40*factor),tile=document.createElement('canvas');tile.width=tile.height=side;
   const c=tile.getContext('2d',{willReadFrequently:true});c.fillStyle=hex;c.fillRect(0,0,side,side);
   if(style==='solid')return c.getImageData(0,0,side,side);
   c.scale(side/40,side/40);
   const lum=.2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2],mix=lum>210?0:255;
   const ink=rgba.slice(0,3).map(v=>Math.round(v+(mix-v)*(mix? .74:.46)));
   c.fillStyle=c.strokeStyle=`rgb(${ink.join(',')})`;c.lineWidth=4;c.lineCap='round';c.lineJoin='round';
   const circle=(x,y,r)=>{c.beginPath();c.arc(x,y,r,0,Math.PI*2);c.fill();};
   const star=(x,y,r,inner=0.45,points=5)=>{c.beginPath();for(let k=0;k<points*2;k++){const a=-Math.PI/2+k*Math.PI/points,rr=k%2?r*inner:r;const xx=x+Math.cos(a)*rr,yy=y+Math.sin(a)*rr;k?c.lineTo(xx,yy):c.moveTo(xx,yy);}c.closePath();c.fill();};
   if(style==='horizontal'){c.fillRect(0,6,40,6);c.fillRect(0,26,40,6);}
   if(style==='vertical'){c.fillRect(6,0,6,40);c.fillRect(26,0,6,40);}
   if(style==='diagonalLeft'||style==='diagonalRight'){
     for(let d=-40;d<=60;d+=20){c.beginPath();if(style==='diagonalLeft'){c.moveTo(d,0);c.lineTo(d+40,40);}else{c.moveTo(d,40);c.lineTo(d+40,0);}c.stroke();}
   }
   if(style==='waves'){for(let y of [10,30]){c.beginPath();c.moveTo(0,y);c.bezierCurveTo(6,y-8,14,y-8,20,y);c.bezierCurveTo(26,y+8,34,y+8,40,y);c.stroke();}}
   if(style==='dots'){circle(10,10,4);circle(30,30,4);}
   if(style==='stars'){star(20,20,11);}
   if(style==='triangles'){c.beginPath();c.moveTo(20,9);c.lineTo(31,30);c.lineTo(9,30);c.closePath();c.fill();}
   if(style==='hearts'){c.beginPath();c.moveTo(20,32);c.bezierCurveTo(0,20,7,6,20,15);c.bezierCurveTo(33,6,40,20,20,32);c.fill();}
   if(style==='flowers'){for(let a=0;a<6;a++)circle(20+Math.cos(a*Math.PI/3)*8,20+Math.sin(a*Math.PI/3)*8,5);circle(20,20,4);}
   if(style==='checker'){c.fillRect(0,0,20,20);c.fillRect(20,20,20,20);}
   if(style==='grid'){c.fillRect(0,0,40,3);c.fillRect(0,0,3,40);c.fillRect(20,0,3,40);c.fillRect(0,20,40,3);}
   if(style==='diamonds'){c.beginPath();c.moveTo(20,6);c.lineTo(30,20);c.lineTo(20,34);c.lineTo(10,20);c.closePath();c.fill();}
   if(style==='sparkle'){star(13,13,8,.2,4);star(31,29,5,.2,4);circle(29,7,1.5);circle(6,33,1.3);circle(21,28,1.8);}
   return c.getImageData(0,0,side,side);
 }
 class HistoryRegions {
   constructor(){this.current=[];this.states=new Map();}
   reset(){this.current=[];}
   remember(src,keep){this.states.set(src,this.current);const live=new Set(keep);for(const key of this.states.keys())if(!live.has(key))this.states.delete(key);}
   restore(src){this.current=this.states.get(src)||[];}
   applyMask(mask,spans,tile,isPattern){
     const next=[];
     for(const rec of this.current){const remaining=subtract(rec.spans,mask);if(remaining.length)next.push({...rec,spans:remaining});}
     if(isPattern&&spans.length)next.push({spans,tile});this.current=next;
   }
 }
 const api={STYLES,validStyle,rgb,region,subtract,labelsFor,paintPixels,HistoryRegions,makeTile};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 root.FillPatterns=api;
 if(typeof document==='undefined')return;
 const history=new HistoryRegions();let selected='solid';
 root.HappyFill={
   getStyle:()=>selected,
   setStyle:id=>{selected=validStyle(id);return selected;},
   needsPatternPath:()=>selected!=='solid'||history.current.length>0,
   reset:()=>history.reset(),
   invalidateRect:(r,w,h)=>{
     const mask=new Uint8Array(w*h);
     for(let y=Math.max(0,r.y);y<Math.min(h,r.y+r.height);y++)mask.fill(1,y*w+Math.max(0,r.x),y*w+Math.min(w,r.x+r.width));
     history.applyMask(mask,new Uint32Array(),null,false);
   },
   remember:(src,keep)=>history.remember(src,keep),
   restore:src=>history.restore(src),
   paint(context,canvas,x,y,hex,paperWidth){
     const w=canvas.width,h=canvas.height,img=context.getImageData(0,0,w,h);
     const labels=history.current.length?labelsFor(history.current,img.data,w,h):null;
     const result=region(img.data,w,h,x,y,labels);
     if(!result.count)return false;
     const tile=makeTile(selected,hex,w/paperWidth);
     const changed=paintPixels(img.data,w,result.spans,tile);
     if(changed){context.putImageData(img,0,0);history.applyMask(result.mask,result.spans,tile,selected!=='solid');}
     return changed;
   },
   debug:()=>({records:history.current.length,snapshots:history.states.size})
 };
})(typeof globalThis==='undefined'?window:globalThis);
