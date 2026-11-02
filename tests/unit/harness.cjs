const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
// Load the ACTUAL app.js, not a copied implementation of the functions.
function createApp(options = {}) {
  const calls = [];
  const frames = [];
  const images = [];
  const ids = {};
  const classes = () => ({ values: new Set(), add(n){this.values.add(n)}, remove(n){this.values.delete(n)}, toggle(n,v){ v ? this.add(n) : this.remove(n) } });
  const ctx = {
    globalCompositeOperation: 'source-over', stack: [],
    save(){this.stack.push(this.globalCompositeOperation)},
    restore(){this.globalCompositeOperation=this.stack.pop()},
    setTransform(...a){calls.push(['transform',...a])},
    clearRect(...a){calls.push(['clear',...a])},
    drawImage(...a){calls.push(['image',this.globalCompositeOperation,...a])},
    getImageData(x,y,w,h){return this.image || {width:w,height:h,data:new Uint8ClampedArray(w*h*4)}},
    putImageData(im){this.image=im;calls.push(['put',im])},
  };
  for(const n of ['beginPath','moveTo','lineTo','stroke','fill','arc','fillText','fillRect','quadraticCurveTo','bezierCurveTo'])ctx[n]=(...a)=>calls.push([n,ctx.globalCompositeOperation,...a]);
  function el(id='') {
    return {id,style:{},dataset:{},classList:classes(),listeners:{},
      addEventListener(t,f,o){(this.listeners[t]??=[]).push({f,o})},
      appendChild(){},closest(){return null},click(){if(this.onclick)this.onclick()},
      getContext(){return ctx},toDataURL(){return 'data:image/png;base64,'+calls.length},
    };
  }
  const names=['canvas','undoBtn','redoBtn','newBtn','saveBtn','clearBtn','palette','colorPicker','brushBtn','sparkleBtn','bucketBtn','outlineBtn','eraserBtn','imageUpload','cancelNew','confirmNew','confirmModal'];
  names.forEach(n=>ids[n]=el(n));
  const canvas=ids.canvas;
  let cw=300,ch=150,writes=0;
  Object.defineProperties(canvas, {
    width:{get:()=>cw,set:v=>{cw=v;writes++}},height:{get:()=>ch,set:v=>{ch=v;writes++}},
    clientWidth:{get:()=>parseFloat(canvas.style.width)||300},
    clientHeight:{get:()=>parseFloat(canvas.style.height)||150}
  });
  canvas.getBoundingClientRect=()=>({left:10,top:20,width:canvas.clientWidth,height:canvas.clientHeight});
  const captures = new Set();
  canvas.setPointerCapture=id=>captures.add(id);
  canvas.hasPointerCapture=id=>captures.has(id);
  canvas.releasePointerCapture=id=>captures.delete(id);
  const stage=el('stage');stage.clientWidth=options.width||600;stage.clientHeight=options.height||800;
  const regions=[el('header'),el('tools'),el('wrap')];
  const root=el('root');root.style.setProperty=(k,v)=>{root.style[k]=v};
  const document=el('document');Object.assign(document,{
    documentElement:root,hidden:false,getElementById:n=>ids[n],createElement:tag=>el(tag),
    querySelector:s=>s==='.canvas-stage'?stage:null,
    querySelectorAll:s=>s==='header,.tools,.canvas-wrap'?regions:[],
  });
  const window=el('window');Object.assign(window,{innerWidth:900,innerHeight:1000,devicePixelRatio:options.dpr||2,
    visualViewport:Object.assign(el('visualViewport'),{scale:1,height:950}),
  });
  const sandbox={...ids,console,document,window,devicePixelRatio:window.devicePixelRatio,
    requestAnimationFrame:f=>{frames.push(f);return frames.length},
    Image:class {constructor(){images.push(this)} set src(v){this._src=v} get src(){return this._src}},
    URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}},
    confirm:()=>true,Uint8Array,Uint8ClampedArray,Math,setTimeout,clearTimeout,
  };
  vm.createContext(sandbox);
  const file=path.resolve(__dirname,'../../app.js');
  vm.runInContext(fs.readFileSync(file,'utf8'),sandbox,{filename:file});
  return {calls,frames,images,ctx,ids,canvas,stage,regions,document,window,root,
    writes:()=>writes,run:s=>vm.runInContext(s,sandbox),
    event(extra={}){return {pointerId:1,button:0,isPrimary:true,cancelable:true,clientX:110,clientY:120,preventDefault(){this.defaultPrevented=true},...extra}},
    flush(){while(frames.length)frames.shift()()},
  };
}
module.exports={createApp};
