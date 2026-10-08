// Logic-only checks with a minimal document stand-in. Not browser or visual QA.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const dist=path.resolve(__dirname,'../dist');
class Element {
 constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.textContent='';this._value=undefined;this.hidden=false;}
 append(...xs){this.children.push(...xs);}
 replaceChildren(...xs){this.children=xs;}
 get childElementCount(){return this.children.length;}
 get value(){return this._value??(this.tagName==='SELECT'?this.children[0]?.value??'':'');}
 set value(v){this._value=v;}
 get selectedIndex(){return this.children.findIndex(x=>x.value===this.value);}
 set selectedIndex(i){this._value=this.children[i]?.value??'';}
 scrollIntoView(){}
}
const html=fs.readFileSync(path.join(dist,'index.html'),'utf8'),els={};
for(const m of html.matchAll(/<([a-z]+)[^>]*\bid="([^"]+)"[^>]*>/g))els[m[2]]=new Element(m[1]);
for(const m of html.matchAll(/<select id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g))for(const o of m[2].matchAll(/<option value="([^"]*)">([^<]*)<\/option>/g)){const e=new Element('option');e.value=o[1];e.textContent=o[2];els[m[1]].append(e);}
const payload=JSON.parse(fs.readFileSync(path.join(dist,'corpus-data.json')));
const context=vm.createContext({document:{getElementById:id=>els[id],createElement:t=>new Element(t),createTextNode:t=>({textContent:t}),createDocumentFragment:()=>new Element(),querySelectorAll:()=>[]},URLSearchParams,location:{search:'?evidence=passages&kind=compactness&tier=all'},history:{replaceState(){}},fetch:async()=>({ok:true,json:async()=>payload}),navigator:{}});
vm.runInContext(fs.readFileSync(path.join(dist,'app.js'),'utf8'),context);
setImmediate(()=>{
 assert.equal(els.submit.disabled,false,els.notice.textContent);
 const evaluate=expr=>JSON.parse(vm.runInContext(`JSON.stringify(${expr})`,context));
 assert.deepEqual(evaluate('hits.map(h=>h.passage.id)'),['JP-P20','JP-P10']);
 assert.equal(els['argument-guide'].hidden,false);
 for(const c of payload.argument_guide.categories){els.kind.value=c.id;els.kind.onchange();assert.deepEqual(evaluate('hits.map(h=>h.passage.id)'),[c.lead,...c.related]);}
 els.kind.value='well-defined';els.q.value='代表元';els.kind.onchange();assert.deepEqual(evaluate('hits.map(h=>h.passage.id)'),['JP-P21']);
 els.proofs.onclick();assert.equal(evaluate('hits.length'),21);assert.equal(els.kind.value,'');
 els.reset.onclick();assert.equal(els.evidence.value,'curated');assert.equal(els['argument-guide'].hidden,true);
 els.evidence.value='body';els.kind.value='';els.tier.value='primary';els.q.value='1の分割';els.variants.value='expand';vm.runInContext('run()',context);
 assert.ok(evaluate('hits.length')>0);assert.ok(evaluate('hits.some(h=>h.u.text.includes("単位の分割"))'));
 els.variants.value='literal';vm.runInContext('run()',context);assert.equal(evaluate('hits.length'),0);
 els.q.value='partition of unity';els.mode.value='all';els.variants.value='expand';vm.runInContext('run()',context);assert.ok(evaluate('hits.length')>0);
 assert.deepEqual(evaluate('queryForms("点有限")'),['点有限']);
 console.log('Aliases, exact fallback, multiword lookup: OK');
 console.log('Purpose links, lead order, guidance search, and reset: OK (14 categories)');
});
