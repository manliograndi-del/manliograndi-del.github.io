/* Voti di Manlio (idea 7 di 7, 24/11/2026): «importante / non importante» su ogni notizia.
   Visibile solo su un browser dove si è aperto una volta il sito con #voto-manlio (#voto-esci per spegnere).
   I voti restano nel browser; «Invia» apre GitHub con una segnalazione già scritta: conta solo se la crea l'account di Manlio.
   Nessuna chiave o segreto nella pagina. Il giro automatico legge le segnalazioni (voti.py). */
(function(){
  var K='aig-voto', KV='aig-voti', REPO='https://github.com/manliograndi-del/manliograndi-del.github.io/issues/new';
  function get(k){try{return localStorage.getItem(k);}catch(e){return null;}}
  function set(k,v){try{v===null?localStorage.removeItem(k):localStorage.setItem(k,v);}catch(e){}}
  var h=location.hash;
  if(h==='#voto-manlio'){set(K,'1');history.replaceState(null,'',location.pathname+location.search);}
  if(h==='#voto-esci'){set(K,null);history.replaceState(null,'',location.pathname+location.search);}
  if(get(K)!=='1') return;

  var V={}; try{V=JSON.parse(get(KV)||'{}')||{};}catch(e){V={};}
  function save(){set(KV,JSON.stringify(V));}
  function key(l){return (l.textContent||'').replace(/\s+/g,' ').trim();}

  var css=document.createElement('style');
  css.textContent='.vt{display:inline-flex;gap:4px;margin-left:8px;vertical-align:middle}'+
    '.vt button{font:500 10px/1 "DM Mono",monospace;letter-spacing:.04em;text-transform:uppercase;padding:3px 7px;border:1.5px solid #15120E;border-radius:99px;background:#FFFCF2!important;color:#15120E!important;cursor:pointer}'+
    '.vt button[aria-pressed="true"].si{background:#D4F23F!important}.vt button[aria-pressed="true"].no{background:#FF8A7A!important}'+
    '#vbar{position:fixed;right:12px;bottom:12px;z-index:99;display:flex;gap:8px;align-items:center;background:#15120E;color:#F4EEDC;border-radius:99px;padding:6px 6px 6px 14px;font:500 12px/1 "DM Mono",monospace;box-shadow:0 2px 8px rgba(0,0,0,.25)}'+
    '#vbar button{font:inherit;border:0;border-radius:99px;background:#D4F23F;color:#15120E;padding:7px 12px;cursor:pointer}#vbar button[disabled]{opacity:.45;cursor:default}';
  document.head.appendChild(css);

  var bar=document.createElement('div'); bar.id='vbar';
  bar.innerHTML='<span></span><button type="button">Invia</button>';
  function daInviare(){return Object.keys(V).filter(function(t){return !V[t].s;});}
  function aggBar(){var n=daInviare().length;bar.firstChild.textContent=n?(n===1?'1 voto da inviare':n+' voti da inviare'):'Voti inviati';bar.lastChild.disabled=!n;}
  bar.lastChild.onclick=function(){
    var ts=daInviare(), righe=[], inviati=[], len=0;
    ts.forEach(function(t){
      var r=(V[t].v>0?'+':V[t].v<0?'-':'0')+' | '+t+' | '+(V[t].u||'')+' | '+V[t].q;
      if(len+r.length>5500) return; righe.push(r); inviati.push(t); len+=r.length+1;
    });
    if(!righe.length) return;
    var q=new Date().toISOString().slice(0,16).replace('T',' ');
    var url=REPO+'?labels=voti&title='+encodeURIComponent('Voti AIgregatore '+q+' ('+righe.length+')')+
      '&body='+encodeURIComponent('Voti di Manlio: + importante, - non importante, 0 voto tolto. Premi «Create» per inviarli.\n\n```\n'+righe.join('\n')+'\n```\n');
    window.open(url,'_blank','noopener');
    inviati.forEach(function(t){V[t].s=1;}); save(); aggBar();
  };

  function stato(t){
    [].slice.call(document.querySelectorAll('.vt')).forEach(function(b){
      if(b.getAttribute('data-t')!==t) return; var v=V[t]&&V[t].v;
      b.children[0].setAttribute('aria-pressed',v>0?'true':'false'); b.children[1].setAttribute('aria-pressed',v<0?'true':'false');
    });
  }
  function vota(t,u,v){
    var q=new Date().toISOString().slice(0,16).replace('T',' ');
    if(V[t]&&V[t].v===v){ if(V[t].s) V[t]={v:0,u:u,q:q}; else delete V[t]; }  // secondo tocco: voto tolto (se già inviato, si invia «0»)
    else V[t]={v:v,u:u,q:q};
    save(); stato(t); aggBar();
  }
  function decora(root){
    [].slice.call(root.querySelectorAll('a[data-p]')).forEach(function(l){
      if(l.getAttribute('data-vt')) return; var t=key(l); if(!t) return; l.setAttribute('data-vt','1');
      var s=document.createElement('span'); s.className='vt'; s.setAttribute('data-t',t);
      s.innerHTML='<button type="button" class="si" title="Notizia importante">Importante</button><button type="button" class="no" title="Notizia non importante">No</button>';
      var u=l.getAttribute('href')||'';
      s.children[0].onclick=function(e){e.preventDefault();e.stopPropagation();vota(t,u,1);};
      s.children[1].onclick=function(e){e.preventDefault();e.stopPropagation();vota(t,u,-1);};
      var dopo=l.nextElementSibling&&l.nextElementSibling.classList.contains('gr')?l.nextElementSibling:l;
      dopo.insertAdjacentElement('afterend',s); stato(t);
    });
  }
  function avvia(){
    document.body.appendChild(bar); aggBar(); decora(document);
    new MutationObserver(function(m){m.forEach(function(x){[].forEach.call(x.addedNodes,function(n){if(n.nodeType===1)decora(n);});});})
      .observe(document.body,{childList:true,subtree:true});
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',avvia); else avvia();
})();
