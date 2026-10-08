'use strict';
const $=id=>document.getElementById(id);
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const subjectNames={'algebra':'代数','number-theory':'数論','analysis':'解析','topology-metric-geometry':'位相・距離・幾何','combinatorics-set-theory':'組合せ・集合論','probability-measure':'測度・確率'};
const roleNames={definition:'定義',theorem:'定理・命題・補題・系',proof:'証明',claim:'主張',example:'例',remark:'注意',prose:'本文'};
const fields=['q','mode','evidence','function','tier','subject','role','document','kind','variants'];
let data,documents,functions,hits=[],page=0,currentTokens=[];
const size=20;
function normalize(s){return s.replace(/\s+/g,(space,offset,whole)=>offset>0&&offset+space.length<whole.length&&whole.charCodeAt(offset-1)<128&&whole.charCodeAt(offset+space.length)<128?' ':'').trim().toLowerCase();}
function option(value,label){const o=node('option',label);o.value=value;return o;}
function button(label,action){const b=node('button',label);b.type='button';b.onclick=action;return b;}
function link(label,url){const a=node('a',label);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}
function highlighted(text,tokens){const out=document.createDocumentFragment();const ts=[...new Set(tokens.filter(Boolean))].sort((a,b)=>b.length-a.length);if(!ts.length){out.append(document.createTextNode(text));return out;}const regex=new RegExp(ts.map(t=>t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|'),'gi');let prev=0;for(const match of text.matchAll(regex)){out.append(document.createTextNode(text.slice(prev,match.index)),node('mark',match[0]));prev=match.index+match[0].length;}out.append(document.createTextNode(text.slice(prev)));return out;}
function matchesFunction(text,entry){if(!entry)return true;if((entry.exclude_patterns||[]).some(p=>new RegExp(p).test(text)))return false;return entry.patterns?entry.patterns.some(p=>new RegExp(p).test(text)):entry.forms.some(f=>text.includes(normalize(f)));}
function guide(entry){$('guide').replaceChildren();$('guide').hidden=!entry;if(!entry)return;$('guide').append(node('h2',entry.role),node('p',entry.forms.join(' ／ ')),node('p',entry.use_when+'。'+entry.do_not_replace_when+'。'),node('p','作例（原文引用ではありません）','hint'),node('p',entry.composed_example,'composed'));if(entry.evidence_note)$('guide').append(node('p',entry.evidence_note,'hint'));}
function argumentGuide(){
 const panel=$('argument-guide');panel.replaceChildren();panel.hidden=$('evidence').value!=='passages';

 if(panel.hidden)return;
 const categories=data.argument_guide.categories,c=categories.find(x=>x.id===$('kind').value);
 panel.append(node('h2',c?c.title:'証明の目的から選ぶ'));
 if(c){panel.append(node('p',c.use_when),node('p','必要な前提：'+c.prerequisites),node('p','補う説明：'+c.explain),node('p','似た例との違い：'+c.distinction),node('p','入口の例：'+c.lead+'。絞り込み条件に合う例を、入口・比較例の順に表示します。','hint'));}
 else panel.append(node('p','目的を選ぶと、入口の例と比較例を表示します。原文の注意点も含めて読み、用例数を推奨の強さとは扱わないでください。'));
 const choices=node('div',undefined,'examples');
 for(const item of categories)choices.append(button(item.title,()=>{reset();$('evidence').value='passages';$('kind').value=item.id;run();}));
 panel.append(choices);
}
function stateToURL(){const p=new URLSearchParams();for(const id of fields)if($(id).value)p.set(id,$(id).value);history.replaceState(null,'','?'+p);}
function reset(){for(const id of fields){if(id==='q')$(id).value='';else $(id).selectedIndex=0;}}
function queryForms(q){
 if($('variants').value==='literal')return [q];
 const group=data.search_aliases.groups.find(g=>g.forms.some(f=>normalize(f)===normalize(q)));
 return group?group.forms:[q];
}
function run(save=true){
 page=0;const entry=functions.get($('function').value);guide(entry);argumentGuide();
 const q=normalize($('q').value),expanded=q?queryForms(q):[];
 const exactAlias=expanded.length>1;
 const groups=exactAlias?[expanded]:($('mode').value==='all'?q.split(/\s+/).filter(Boolean).map(queryForms):[expanded]);
 currentTokens=q?groups.flat():entry?.forms||[];
 const usedAliases=groups.filter(g=>g.length>1).flat();
 $('alias-notice').textContent=usedAliases.length?'別表記も検索：'+[...new Set(usedAliases)].join(' ／ ')+'。条件は原文で確認してください。':'';
 const acceptDoc=d=>($('tier').value==='all'||d.tier===$('tier').value)&&(!$('subject').value||d.subjects.includes($('subject').value))&&(!$('document').value||d.id===$('document').value);
 const accept=u=>(!$('role').value||u.role===$('role').value)&&(!q||groups.every(g=>g.some(t=>normalize(u.text).includes(normalize(t)))));
 const raw=[];
 if($('evidence').value==='passages'){
  for(const p of data.proof_passages||[]){const d=documents.get(p.document);const text=[p.title,p.summary,p.raw,p.use_when,p.prerequisites,p.explain,...p.phases.map(x=>x.commentary)].join(' ');const u={start:p.start,end:p.end,text,role:'proof',section:p.source_title};if(acceptDoc(d)&&accept(u)&&(!$('kind').value||p.argument_kinds.includes($('kind').value))&&(!entry||p.functions.includes(entry.id)))raw.push({d,u,passage:p,functions:p.functions.map(id=>functions.get(id)?.role||id)});}
 }else if($('evidence').value==='curated'){
  for(const e of entry?[entry]:data.lexicon)for(const h of e.curated_examples){const d=documents.get(h.document);if(acceptDoc(d)&&accept(h))raw.push({d,u:{...h,start:h.match_start,end:h.match_end},review:h,functions:[e.role]});}
 }else{
  for(const d of data.documents)if(acceptDoc(d))for(const u of d.units)if(accept(u)&&matchesFunction(normalize(u.text),entry))raw.push({d,u,functions:[]});
 }
 const category=data.argument_guide.categories.find(c=>c.id===$('kind').value);
 const order=category?[category.lead,...category.related]:[];
 raw.sort((a,b)=>category&&a.passage&&b.passage?order.indexOf(a.passage.id)-order.indexOf(b.passage.id):b.d.id.localeCompare(a.d.id)||a.u.start-b.u.start);
 const unique=new Map();
 for(const h of raw){const k=h.passage?h.passage.id:normalize(h.u.text);if(unique.has(k)){const existing=unique.get(k);if(!existing.copies.some(c=>c.d.id===h.d.id&&c.u.start===h.u.start))existing.copies.push(h);existing.functions=[...new Set([...existing.functions,...h.functions])];}else unique.set(k,{...h,copies:[h]});}
 hits=[...unique.values()];if(save)stateToURL();render();
}

const phaseNames={assumptions:'仮定・設定',goal:'目標',argument:'論証',conclusion:'結論'};
const explicitNames={explicit:'原文に明示','partly-implicit':'一部は文脈から補って整理','statement-only':'定理・補題の結論に記載'};
const scopeNames={'statement-and-proof':'主張と証明','construction-excerpt':'構成部分の抜粋','uniqueness-excerpt':'一意性部分の抜粋','closing-excerpt':'結び部分の抜粋','induction-excerpt':'帰納段階の抜粋','implication-excerpt':'一方向の含意の抜粋','equivalence-excerpt':'同値性の二方向の抜粋'};
function passagePanel(p){
 const box=node('section',undefined,'passage-panel');
 for(const [label,value] of [['使う場面',p.use_when],['必要な前提',p.prerequisites],['説明を補う点',p.explain]])box.append(node('h3',label),node('p',value));
 box.append(node('p','各段階の対応（編集注）','hint'));
 const flow=node('ol',undefined,'proof-flow');
 for(const phase of p.phases){const li=node('li');li.append(node('h3',phaseNames[phase.role]),node('p',phase.commentary),node('p',explicitNames[phase.explicitness],'hint'));const evidence=node('details');evidence.append(node('summary','対応する原文を見る'));for(const x of phase.excerpts)evidence.append(node('p',`${x.start}–${x.end}行`,'path'),node('pre',x.raw));li.append(evidence);flow.append(li);}box.append(flow);
 box.append(node('h3','参考にする運び'));const lessons=node('ul');for(const x of p.lessons)lessons.append(node('li',x));box.append(lessons);
 box.append(node('h3','そのまま移さない点'));const cautions=node('ul');for(const x of p.cautions)cautions.append(node('li',x));box.append(cautions);
 if(p.dependencies.length){const deps=node('details');deps.append(node('summary','前後の依存先を読む'));for(const dep of p.dependencies)deps.append(node('p',dep.commentary),node('p',`${dep.start}–${dep.end}行`,'path'),node('pre',dep.raw));box.append(deps);}
 box.append(node('p','原文を無改変で採録し、上の説明は編集注として付けています。証明全体の正しさを認定するものではありません。','hint'));return box;
}

async function copy(text,label){try{await navigator.clipboard.writeText(text);$('notice').textContent=label+'をコピーしました。';}catch{$('notice').textContent='コピーできませんでした。表示された本文を選択してコピーしてください。';}}
function sourcePanel(h,container){
 const {d,u}=h;container.replaceChildren();
 let radius=12;
 const location=node('h3',undefined,'source-heading'),pre=node('pre'),meta=node('p',undefined,'path');
 const paint=()=>{const lo=Math.max(1,u.start-radius),hi=Math.min(d.lines.length,u.end+radius);location.textContent=`原TeX ${lo}–${hi}行`;pre.textContent=d.lines.slice(lo-1,hi).map((line,i)=>`${String(lo+i).padStart(5)}  ${line}`).join('\n');meta.textContent=`${d.id} · SHA-256 ${d.sha256}`;};paint();
 container.append(location,pre,meta);
 const actions=node('div',undefined,'actions');actions.append(button('前後をさらに読む',()=>{radius+=30;paint();}),button('原文をコピー',()=>copy(d.lines.slice(u.start-1,u.end).join('\n'),'原文')),button('出典をコピー',()=>copy(`${d.title}\n${d.url}\n${u.start}–${u.end}行\nSHA-256 ${d.sha256}`,'出典')),link('公開TeXを開く',d.url));container.append(actions);
 if(h.copies.length>1){const details=node('details');details.append(node('summary',`同じ文章の掲載箇所（${h.copies.length}件）`));for(const other of h.copies){const p=node('p');p.append(link(`${other.d.title} · ${other.u.start}–${other.u.end}行`,other.d.url));details.append(p);}container.append(details);}
}
function qMatches(text){return $('q').value?[...new Set(currentTokens.filter(t=>normalize(text).includes(normalize(t))))]:[];}
function render(){
 $('results').replaceChildren();const docCount=new Set(hits.flatMap(h=>h.copies.map(c=>c.d.id))).size;
 $('notice').className='';$('notice').textContent=`${hits.length.toLocaleString()}件の文章 · ${docCount}文書${$('evidence').value==='passages'?'（証明のまとまり・原文と解説を検索）':$('evidence').value==='curated'?'（用法確認済み）':'（本文から検索）'}`;
 if(!hits.length){$('results').append(node('p','一致する用例がありません。語句を短くするか、「探す対象」を本文全体にして絞り込みを減らしてください。','empty'));}
 for(const h of hits.slice(page*size,(page+1)*size)){
  const {d,u}=h,card=node('article');card.append(node('h2',h.passage?`${h.passage.id} ${h.passage.title}`:d.title));const badges=node('div');
  for(const text of [d.id,d.tier==='primary'?'2020年以降':'2019年以前',roleNames[u.role]||u.role,`${u.start}–${u.end}行`])badges.append(node('span',text,'badge'));
  if(h.passage)badges.append(node('span',scopeNames[h.passage.scope_kind]||h.passage.scope_kind,'badge checked'));
  if(h.review)badges.append(node('span','用法確認済み','badge checked'));
  if(h.copies.length>1)badges.append(node('span',`${h.copies.length}箇所に掲載`,'badge'));
  if(qMatches(h.u.text).length)card.append(node('p','一致した検索表記：'+qMatches(h.u.text).join(' ／ '),'hint'));
  card.append(badges,node('p',[...d.subjects.map(s=>subjectNames[s]||s),u.section].filter(Boolean).join(' / '),'path'));
  const snippet=node('p',undefined,'snippet');const preview=h.passage?h.passage.summary:u.text;snippet.append(highlighted(preview.length>1100?preview.slice(0,1100)+'…':preview,currentTokens));card.append(snippet);
  if(h.passage)card.append(passagePanel(h.passage));
  if(h.review)card.append(node('p',h.functions.join('・')+' — '+h.review.review_note,'hint'));
  const actions=node('div',undefined,'actions'),detail=node('div');
  actions.append(button('本文と出典を見る',()=>{if(detail.childElementCount){detail.replaceChildren();}else sourcePanel(h,detail);}),link('文書の公開ページ',d.page_url));card.append(actions,detail);$('results').append(card);
 }
 $('pager').hidden=hits.length<=size;$('prev').disabled=page===0;$('next').disabled=(page+1)*size>=hits.length;$('position').textContent=`${hits.length?page*size+1:0}–${Math.min((page+1)*size,hits.length)} / ${hits.length}`;
}
$('evidence').onchange=()=>{if(data){if($('evidence').value!=='passages')$('kind').value='';run();}};
$('kind').onchange=()=>{if(data){$('evidence').value='passages';run();}};
$('form').onsubmit=e=>{e.preventDefault();if(data)run();};
$('prev').onclick=()=>{page--;render();$('notice').scrollIntoView({block:'start'});};$('next').onclick=()=>{page++;render();$('notice').scrollIntoView({block:'start'});};
$('reset').onclick=()=>{reset();$('evidence').value='curated';run();};
$('proofs').onclick=()=>{reset();$('evidence').value='passages';run();};
$('dictionary').onclick=()=>{reset();$('evidence').value='curated';$('function').value='reduction';run();};
document.querySelectorAll('[data-q],[data-function]').forEach(b=>b.onclick=()=>{reset();if(b.dataset.q)$('q').value=b.dataset.q;else{$('function').value=b.dataset.function;$('evidence').value='curated';}run();});
async function init(){try{
 const response=await fetch('corpus-data.json');if(!response.ok)throw Error('検索データを読み込めません。');data=await response.json();documents=new Map(data.documents.map(d=>[d.id,d]));functions=new Map(data.lexicon.map(e=>[e.id,e]));
 for(const e of data.lexicon)$('function').append(option(e.id,e.role));
 for(const c of data.argument_guide.categories)$('kind').append(option(c.id,c.title));
 for(const s of [...new Set(data.documents.flatMap(d=>d.subjects))].sort())$('subject').append(option(s,subjectNames[s]||s));
 for(const d of [...data.documents].reverse())$('document').append(option(d.id,`${d.id} ${d.title}`));
 const count=data.documents.reduce((n,d)=>n+d.units.length,0),checked=data.lexicon.reduce((n,e)=>n+e.curated_examples.length,0);
 $('stats').textContent=`${data.documents.length}文書 · ${count.toLocaleString()}検索区画 · ${data.lexicon.length}の文章の役割 · ${checked}件の用法確認済み例 · ${(data.proof_passages||[]).length}件の証明のまとまり`;
 const p=new URLSearchParams(location.search);if(p.size){for(const id of fields)if(p.has(id)){$(id).value=p.get(id);if($(id).tagName==='SELECT'&&$(id).selectedIndex<0)$(id).selectedIndex=0;}}else $('evidence').value='curated';
 $('submit').disabled=false;run(false);
}catch(error){$('stats').textContent='検索データを読み込めませんでした。';$('notice').className='error';$('notice').textContent=error.message;}}
init();
