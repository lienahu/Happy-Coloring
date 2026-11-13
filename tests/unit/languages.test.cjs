const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const i18n=require('../../i18n.js');
const root=path.resolve(__dirname,'../..');
const source=f=>fs.readFileSync(path.join(root,f),'utf8').replace(/\r\n/g,'\n');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const locales=['en','fr','pt','es','zh-Hans','ja','ko'];
const keys=Object.keys(i18n.dictionaries.en).sort();
test('exactly seven requested languages in the selector',()=>assert.deepEqual(i18n.languages.map(l=>l.code),locales));
for(const locale of locales){
 test(`${locale}: complete nonempty message catalogue`,()=>{
  const d=i18n.dictionaries[locale];assert.deepEqual(Object.keys(d).sort(),keys);
  for(const key of keys){assert.equal(typeof d[key],'string');assert.ok(d[key].trim());assert.ok(!/[<>]/.test(d[key]));}
 });
 test(`${locale}: translation returns every exact message`,()=>{
  for(const key of keys)assert.equal(i18n.translate(locale,key),i18n.dictionaries[locale][key]);
 });
 test(`${locale}: native option exists and keeps its own language tag`,()=>{
  assert.ok(html.includes(`data-language="${locale}"`));
  const entry=i18n.languages.find(l=>l.code===locale);assert.ok(html.includes(entry.name));
 });
}
for(const [input,expected] of [['fr-CA','fr'],['fr-FR','fr'],['pt-BR','pt'],['pt-PT','pt'],['es-MX','es'],['zh-CN','zh-Hans'],['zh','zh-Hans'],['zh-Hans','zh-Hans'],['ja-JP','ja'],['ko-KR','ko'],['EN_us','en'],['  fr  ','fr'],['de-DE','en'],['__proto__','en'],['constructor','en'],['','en'],[null,'en'],[42,'en']]){
 test(`resolve locale ${JSON.stringify(input)}`,()=>assert.equal(i18n.resolveLanguage(input),expected));
}
test('every HTML translation key is present in every catalogue',()=>{
 for(const m of html.matchAll(/data-i18n(?:-aria|-title)?="([^"]+)"/g)){
  for(const locale of locales)assert.ok(Object.hasOwn(i18n.dictionaries[locale],m[1]),`${locale}:${m[1]}`);
 }
});
test('missing message safely returns a readable key',()=>assert.equal(i18n.translate('fr','notAMessage'),'notAMessage'));
test('unsupported locale safely falls back to English',()=>assert.equal(i18n.translate('invalid','save'),'Save'));
test('missing preference defaults to English',()=>assert.equal(i18n.readPreference({getItem:()=>null}),'en'));
test('stored preference restores French Canadian as French',()=>assert.equal(i18n.readPreference({getItem:()=> 'fr-CA'}),'fr'));
test('blocked storage reads do not break initialization',()=>assert.equal(i18n.readPreference({getItem(){throw new Error('blocked')}}),'en'));
test('absent storage does not break the picker',()=>{assert.equal(i18n.readPreference(null),'en');assert.equal(i18n.savePreference(null,'ko'),false)});
test('blocked storage writes are handled',()=>assert.equal(i18n.savePreference({setItem(){throw new Error('quota')}},'ko'),false));
test('saved language uses a dedicated key and canonical code',()=>{
 let actual;assert.equal(i18n.savePreference({setItem(...a){actual=a}},'zh-CN'),true);
 assert.deepEqual(actual,[i18n.STORAGE_KEY,'zh-Hans']);
});
test('valid storage roundtrip restores all seven choices',()=>{
 const data=new Map(),s={getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v)};
 for(const l of locales){assert.ok(i18n.savePreference(s,l));assert.equal(i18n.readPreference(s),l)}
});
test('app changes remain confined to Clear, Save, and the shared picture import block',()=>{
 const js=require('./fill-source-bridge.cjs').withoutFillHooks(source('app.js')).replace(/\/\/ PICTURE-SOURCE-BEGIN:[\s\S]*?\/\/ PICTURE-SOURCE-END\n\n/,source('tests/fixtures/picture-base-handlers.txt')).replace('// Keep export UI separate from the drawing and gesture engines.\nsaveBtn.onclick=()=>window.HappySave.open(canvas,background,saveBtn);',source('tests/fixtures/save-base-handler.txt')).replace('confirm(window.HappyI18n ? window.HappyI18n.t("clearQuestion") : "Clear this picture?")','confirm("Clear this picture?")');
 assert.equal(crypto.createHash('sha256').update(js).digest('hex'),'dea51ef0e04a1786ce224562649882db42bf5fb4311030b1e9826f3ab1ce21f5');
});
test('canvas zoom source is unchanged, allowing LF/CRLF checkout conversion',()=>{
 assert.equal(crypto.createHash('sha256').update(source('canvas-zoom.js')).digest('hex'),'d5889b50df3b8e24c627dde0c7b98156996512da93285b4b1fb574dba5ded5ff');
});
test('Clear uses the selected language and still cancels safely',()=>{
 const h=require('./harness.cjs').createApp();h.window.HappyI18n={t:k=>i18n.translate('ja',k)};
 h.run('confirm=(m)=>{globalThis.capturedMessage=m;return false;}');
 const before=h.calls.length;h.ids.clearBtn.onclick();
 assert.equal(h.run('capturedMessage'),i18n.translate('ja','clearQuestion'));assert.equal(h.calls.length,before);
});
test('picker cannot change canvas pixels or tool IDs',()=>{
 const js=fs.readFileSync(path.join(root,'i18n.js'),'utf8');
 assert.doesNotMatch(js,/getContext\(|toDataURL\(|\.innerHTML\s*=|\.width\s*=|fetch\(/);
 assert.doesNotMatch(html,/data-theme-choice|id="themeBtn"/);
});
test('localization loads before UI dynamic messages',()=>assert.ok(html.indexOf('src="i18n.js')<html.indexOf('src="mobile-ui.js')));
test('both language controls reach one native dialog',()=>{
 assert.equal((html.match(/data-open-language/g)||[]).length,2);
 assert.match(html,/<dialog[^>]+id="languageDialog"/);assert.match(html,/aria-labelledby="languageTitle"/);
});
