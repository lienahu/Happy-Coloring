/* Inline Fill choices + demand-loaded picture library. No remote services.
 * No full template URLs are assigned to any Image until a card is selected.
 */
(function(root){
 'use strict';
 const LEVELS=['easy','medium','hard'],PAGE_SIZE=6;
 function pageItems(items,level,page=0,size=PAGE_SIZE){
   const list=items.filter(x=>x.level===level),total=Math.max(1,Math.ceil(list.length/size));
   page=Math.max(0,Math.min(total-1,Number.isFinite(page)?Math.trunc(page):0));
   return {items:list.slice(page*size,(page+1)*size),page,total,count:list.length};
 }
 function safeAsset(path){return typeof path==='string'&&/^assets\/[a-zA-Z0-9_./-]+\.(png|webp|svg)$/.test(path)&&!path.split('/').includes('..');}
 function validateCatalog(data){
   if(!data||!Array.isArray(data.items))throw Error('Invalid catalog');const ids=new Set();
   for(const e of data.items){
     if(!e||!/^[-a-z0-9]+$/.test(e.id)||ids.has(e.id)||!LEVELS.includes(e.level)||!safeAsset(e.src)||!safeAsset(e.thumb)||e.src===e.thumb||!e.title||!e.title.en)throw Error('Invalid template');
     ids.add(e.id);
   }
   return data.items;
 }
 const api={LEVELS,PAGE_SIZE,pageItems,validateCatalog,safeAsset};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 root.TemplateCatalog=api;if(typeof document==='undefined')return;
 const $=id=>document.getElementById(id),tr=k=>root.HappyI18n?root.HappyI18n.t(k):k;
 const picker=$('fillStylesSection'),fillButton=$('bucketBtn'),grid=$('fillStyleGrid');
 function closeFill(){picker.hidden=true;fillButton.setAttribute('aria-expanded','false');}
 function syncFill(){
   grid.querySelectorAll('[data-fill-style]').forEach(button=>{
     const selected=button.dataset.fillStyle===root.HappyFill.getStyle();
     button.classList.toggle('selected',selected);button.setAttribute('aria-pressed',String(selected));
     button.querySelector('.fill-style-name').textContent=tr('pattern_'+button.dataset.fillStyle);
     const sample=button.querySelector('canvas'),c=sample.getContext('2d'),tile=root.FillPatterns.makeTile(button.dataset.fillStyle,color,1);
     const t=document.createElement('canvas');t.width=tile.width;t.height=tile.height;t.getContext('2d').putImageData(tile,0,0);
     c.fillStyle=c.createPattern(t,'repeat');c.fillRect(0,0,sample.width,sample.height);
   });
 }
 root.FillPatterns.STYLES.forEach(id=>{
   const b=document.createElement('button');b.type='button';b.className='fill-style-option';b.dataset.fillStyle=id;b.setAttribute('aria-pressed',String(id==='solid'));
   const sample=document.createElement('canvas');sample.width=72;sample.height=44;sample.setAttribute('aria-hidden','true');
   const name=document.createElement('span');name.className='fill-style-name';b.append(sample,name);grid.append(b);
   b.addEventListener('click',()=>{
     root.HappyFill.setStyle(id);syncFill();closeFill();
     if(root.StudioLayout.isCompact(innerWidth,innerHeight))root.HappyStudio.closeDrawer(false);else fillButton.focus({preventScroll:true});
   });
 });
 fillButton.addEventListener('click',()=>{
   const open=picker.hidden;root.HappyStudio.collapseSizes();closeFill();if(!open)return;
   syncFill();picker.hidden=false;fillButton.setAttribute('aria-expanded','true');
   requestAnimationFrame(()=>picker.scrollIntoView({block:'nearest',behavior:'instant'}));
 });
 document.addEventListener('click',e=>{if(!picker.hidden&&!e.target.closest('#fillStylesSection,#bucketBtn'))closeFill();},true);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!picker.hidden){closeFill();}});
 root.HappyFillUI={close:closeFill};syncFill();
 const dialog=$('templateLibraryDialog'),cards=$('libraryGrid'),scroll=$('libraryScroll'),status=$('libraryStatus');
 let catalog=null,catalogPromise=null,level='easy',page=0,selection=0,pending=false,opener=null,observer=null;
 const counters={manifestLoads:0,thumbsAssigned:[],fullSelections:[]};
 const language=()=>root.HappyI18n?root.HappyI18n.getLanguage():'en';
 function title(item){return item.title[language()]||item.title.en;}
 function stopObserver(){if(observer){observer.disconnect();observer=null;}}
 function thumbs(){
   stopObserver();
   const assign=image=>{if(image.dataset.src){const src=image.dataset.src;image.src=src;delete image.dataset.src;counters.thumbsAssigned.push(src);}};
   if('IntersectionObserver' in window){observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){assign(e.target);observer.unobserve(e.target);}}),{root:scroll,rootMargin:'80px'});cards.querySelectorAll('img').forEach(im=>observer.observe(im));}
   else cards.querySelectorAll('img').forEach(assign);
 }
 function render(){
   if(!catalog)return;stopObserver();cards.replaceChildren();
   const result=pageItems(catalog,level,page);page=result.page;
   document.querySelectorAll('[data-level]').forEach(b=>{const yes=b.dataset.level===level;b.setAttribute('aria-selected',String(yes));b.tabIndex=yes?0:-1;});
   cards.setAttribute('aria-labelledby','level-'+level);scroll.scrollTop=0;
   for(const item of result.items){
     const b=document.createElement('button');b.type='button';b.className='library-card';b.dataset.templateId=item.id;b.setAttribute('aria-label',title(item));
     const im=new Image();im.width=192;im.height=192;im.loading='lazy';im.decoding='async';im.alt='';im.dataset.src=item.thumb;
     im.onerror=()=>{im.hidden=true;b.classList.add('thumbnail-failed');};
     const text=document.createElement('span');text.textContent=title(item);b.append(im,text);b.addEventListener('click',()=>choose(item));cards.append(b);
   }
   $('libraryPrev').disabled=page===0;$('libraryNext').disabled=page===result.total-1;
   $('libraryPageCount').textContent=`${page+1} / ${result.total} · ${result.count}`;
   if(!pending)status.textContent='';thumbs();
 }
 async function getCatalog(){
   if(catalog)return catalog;
   if(!catalogPromise){counters.manifestLoads++;catalogPromise=fetch('assets/template-library/catalog.json?v=1',{cache:'no-cache'})
     .then(r=>{if(!r.ok)throw Error('Catalog HTTP '+r.status);return r.json();})
     .then(data=>{catalog=validateCatalog(data);return catalog;})
     .catch(err=>{catalogPromise=null;throw err;});}
   return catalogPromise;
 }
 async function startLibrary(){
   status.textContent=tr('libraryLoading');$('libraryRetry').hidden=true;
   try{await getCatalog();if(dialog.open)render();}
   catch(_){if(dialog.open){status.textContent=tr('libraryError');$('libraryRetry').hidden=false;}}
 }
 async function choose(item){
   const ticket=++selection;pending=true;status.textContent=tr('pictureLoading');cards.setAttribute('aria-busy','true');
   counters.fullSelections.push(item.src);
   // Existing loader handles decoding, same-origin safety, race cancellation and undo.
   const ok=await loadPictureSource(item.src);
   if(ticket!==selection)return;
   pending=false;cards.removeAttribute('aria-busy');
   if(ok){dialog.close();}else if(dialog.open){status.textContent=tr('libraryImageError');}
 }
 $('openTemplateLibrary').addEventListener('click',()=>{
   closeFill();root.HappyStudio.closeDrawer(false);opener=$('openTemplateLibrary');
   canvasInput.cancel();end();if(root.HappySelection?.isActive())root.HappySelection.cancel?.();
   if(!dialog.open)dialog.showModal();$('closeTemplateLibrary').focus({preventScroll:true});startLibrary();
 });
 $('closeTemplateLibrary').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('close',()=>{
   stopObserver();++selection;
   if(pending&&cancelPictureRequest)cancelPictureRequest();pending=false;cards.removeAttribute('aria-busy');
   // On a phone the library launch button is hidden with the closed drawer.
   const target=opener?.getClientRects().length?opener:document.querySelector('[data-open-section="pagesSection"]');target?.focus({preventScroll:true});
 });
 function levelChange(next){if(!LEVELS.includes(next))return;level=next;page=0;render();}
 document.querySelectorAll('[data-level]').forEach(b=>{
   b.addEventListener('click',()=>levelChange(b.dataset.level));
   b.addEventListener('keydown',e=>{let i=LEVELS.indexOf(level);if(e.key==='ArrowRight')i=(i+1)%3;else if(e.key==='ArrowLeft')i=(i+2)%3;else return;e.preventDefault();levelChange(LEVELS[i]);$('level-'+level).focus();});
 });
 $('libraryPrev').addEventListener('click',()=>{page--;render();});$('libraryNext').addEventListener('click',()=>{page++;render();});$('libraryRetry').addEventListener('click',startLibrary);
 document.addEventListener('happy-language-change',()=>{syncFill();if(dialog.open)render();});
 root.HappyLibrary={getState:()=>({level,page,pending,count:catalog?.length||0}),debug:()=>JSON.parse(JSON.stringify(counters))};
})(typeof globalThis==='undefined'?window:globalThis);
