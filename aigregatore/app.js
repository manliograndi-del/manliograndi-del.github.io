(function(){
  function start(D){
    var N=D.news, CATS=D.cats, WD=D.wd, DN=D.dn||{}, TODAY=D.today;
    var vista=document.getElementById('vista'), home=document.getElementById('home');
    var BYP={}; N.forEach(function(x){BYP[x.p]=x;});
    function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
    function word(n){return n+(n===1?' notizia':' notizie');}
    function leaf(d,sm){return '<span class="leaf'+(sm?' sm':'')+'"><b>'+WD[d]+'</b><i>'+(DN[d]||d)+'</i></span>';}
    function ago(d){var k=TODAY-d;return k===0?'oggi':k===1?'ieri':k+' giorni fa';}
    function week(d){var s='<span class="week" aria-hidden="true">';for(var k=TODAY-6;k<=TODAY;k++)s+='<i'+(k===d?' class="on"':'')+'></i>';return s+'</span>';}
    function srcs(f,n){return f.length<=n+1?f.join(' · '):f.slice(0,n).join(' · ')+' e altre '+(f.length-n);}
    function a(x){return '<a href="'+esc(x.u)+'" data-p="'+x.p+'" target="_blank" rel="noopener">'+esc(x.t)+'</a>'+(x.g?'<span class="gr">gratis</span>':'');}

    /* a story with several articles opens in place and lists them all */
    function nart(x){return x.ar.length+' articoli di '+x.n+' testate';}
    function listHtml(x){
      return '<ol class="arts">'+x.ar.map(function(r){
        return '<li><a href="'+esc(r[2])+'" target="_blank" rel="noopener"><span class="af">'+esc(r[0])+(r[4]==='L'?' <span class="gr">gratis</span>':'')+'</span><span class="at">'+esc(r[1])+'</span><span class="ad">'+WD[r[3]]+' '+(DN[r[3]]||r[3])+'</span></a></li>';
      }).join('')+'</ol>';
    }
    function decorate(root){
      [].slice.call(root.querySelectorAll('a[data-p]')).forEach(function(l){
        var x=BYP[l.getAttribute('data-p')]; if(!x||!x.ar.length||l.classList.contains('multi')) return;
        l.classList.add('multi'); l.setAttribute('role','button'); l.setAttribute('aria-expanded','false');
        var box=l.closest('.card,.mcard');
        if(box&&!box.querySelector('.more')){
          var b=document.createElement('button'); b.type='button'; b.className='more'; b.setAttribute('data-p',x.p);
          b.textContent='Apri i '+nart(x); (box.querySelector('.src')||l.parentNode).insertAdjacentElement('afterend',b);
        }
      });
    }
    function toggle(p,from){
      var x=BYP[p]; if(!x||!x.ar.length) return false;
      var box=from.closest('.card,.mcard'), host=box||from.closest('li')||from.parentNode;
      var open=host.classList.toggle('open');
      var old=host.querySelector('.arts'); if(old) old.parentNode.removeChild(old);
      if(open){
        var target=box?(box.querySelector('.more')||box.lastElementChild):(host.querySelector('.gt')||host.querySelector('div')||host);
        target.insertAdjacentHTML(box?'afterend':'beforeend',listHtml(x));
      }
      var m=host.querySelector('.more'); if(m) m.textContent=open?'× chiudi':'Apri i '+nart(x);
      [].slice.call(host.querySelectorAll('a.multi')).forEach(function(l){l.setAttribute('aria-expanded',String(open));});
      if(open) setTimeout(function(){
        var r=host.getBoundingClientRect(); if(r.top<0||r.top>window.innerHeight*0.6) window.scrollTo(0,r.top+window.pageYOffset-90);
      },60);
      return true;
    }
    document.addEventListener('click',function(e){
      var t=e.target.closest?e.target.closest('a.multi,button.more'):null; if(!t) return;
      if(toggle(t.getAttribute('data-p'),t)) e.preventDefault();
    });
    decorate(document);

    /* an outlet's bubble grows: its numbers, the stories it shared with others, a link to its site */
    var fbox=document.querySelector('.mg.dark'), fpills=[].slice.call(document.querySelectorAll('[data-fk="f"]'));
    function closeSrc(){
      if(!fbox) return; var o=fbox.querySelector('.fpanel'); if(o) o.parentNode.removeChild(o);
      fbox.classList.remove('grown'); fpills.forEach(function(p){p.setAttribute('aria-pressed','false');});
    }
    function openSrc(key,label){
      closeSrc();
      var L=N.filter(function(x){return x.s.indexOf(key)>-1;});
      var sh=L.filter(function(x){return x.n>=2;}).sort(function(p,q){return q.n-p.n||q.d-p.d||p.p-q.p;});
      var solo=L.filter(function(x){return x.n<2;}).sort(function(p,q){return q.d-p.d||p.p-q.p;});
      var show=sh.slice(0,8); if(show.length<3) show=show.concat(solo.slice(0,3-show.length));
      var site='';
      L.some(function(x){
        var u=''; if(x.ar.length){x.ar.some(function(r){if(r[0]===label){u=r[2];return true;}return false;});} else if(x.f[0]===label) u=x.u;
        if(u){try{site=new URL(u).origin;}catch(e){} } return !!site;
      });
      var h='<div class="fpanel"><div class="fhead"><h3>'+esc(label)+'</h3><button type="button" class="fclose">× chiudi</button></div>'+
        '<div class="fnums"><span><b>'+L.length+'</b>'+(L.length===1?'notizia':'notizie')+' nella settimana</span><span><b>'+sh.length+'</b>date anche da altre testate</span><span><b>'+solo.length+'</b>date solo da lei</span></div>'+
        '<ol class="rows">'+show.map(function(x){
          return '<li>'+leaf(x.d,true)+'<div>'+a(x)+'<span class="src">'+(x.n>1?'<b>'+x.n+' testate</b> · ':'')+CATS[x.c]+'</span></div></li>';
        }).join('')+'</ol>'+
        (site?'<a class="all fgo" href="'+esc(site)+'" target="_blank" rel="noopener">Vai al sito di '+esc(label)+' <i>→</i></a>':'')+'</div>';
      fbox.insertAdjacentHTML('beforeend',h); fbox.classList.add('grown'); decorate(fbox);
      fpills.forEach(function(p){p.setAttribute('aria-pressed',String(p.getAttribute('data-fv')===key));});
      fbox.querySelector('.fclose').addEventListener('click',closeSrc);
      var pn=fbox.querySelector('.fpanel'); setTimeout(function(){var r=pn.getBoundingClientRect(); if(r.top>window.innerHeight*0.5||r.top<0) window.scrollTo(0,r.top+window.pageYOffset-110);},60);
    }
    fpills.forEach(function(p){
      p.addEventListener('click',function(e){
        e.preventDefault();
        if(p.getAttribute('aria-pressed')==='true') closeSrc(); else openSrc(p.getAttribute('data-fv'),p.getAttribute('data-fl'));
      });
    });

    /* choosing an assistant or a theme: its top stories first, big, then the rest */
    if(!vista||!home) return;
    var pills=[].slice.call(document.querySelectorAll('[data-fk="a"],[data-fk="c"]'));
    var LAY={1:['s8'],2:['s7','s5'],3:['s5','s3','s4'],4:['s7','s5','s5','s7'],5:['s5','s3','s4','s6','s6']};
    var SHP=['','blob','ticket','tail','blob2'], ROT=[-1.4,2,1.1,-1.2,1.5], OFF=[0,36,8,0,28];
    function big(x,i,k){
      var sp=LAY[k][i], size=(sp==='s8'||sp==='s7')?'xl':(sp==='s3'?'m':'l'), d=58+x.n*6;
      return '<article class="card c-'+x.c+' '+sp+' '+SHP[i%5]+' '+size+'" style="--r:'+ROT[i%5]+'deg;--y:'+OFF[i%5]+'px">'+
        '<span class="n" style="--d:'+d+'px"><b>'+x.n+'</b><i>'+(x.n===1?'testata':'testate')+'</i></span>'+
        '<div class="when">'+leaf(x.d)+'<span class="whentxt">uscita<br><strong>'+ago(x.d)+'</strong></span>'+week(x.d)+'</div>'+
        '<p class="cat">'+CATS[x.c]+'</p>'+(x.j?'<span class="jb">cercata ×'+x.j+'</span>':'')+
        '<h3>'+a(x)+'</h3><p class="src">'+esc(srcs(x.f,3))+'</p>'+
        '<svg class="ill" viewBox="0 0 96 96" aria-hidden="true"><use href="#i-'+x.c+'"/></svg></article>';
    }
    function mid(x,i){
      return '<article class="mcard c-'+x.c+'" style="--r:'+[-.7,.6,-.4,.8][i%4]+'deg"><div class="mh">'+leaf(x.d,true)+'<span class="cat">'+CATS[x.c]+'</span><b class="mn">'+x.n+' testate</b></div>'+
        '<h3>'+a(x)+'</h3><p class="src">'+esc(srcs(x.f,3))+'</p></article>';
    }
    function row(x){return '<li class="ar vr">'+leaf(x.d,true)+'<div>'+a(x)+'<span class="src"><i class="dot c-'+x.c+'"></i>'+CATS[x.c]+' · '+esc(x.f[0])+'</span></div></li>';}
    function pick(kind,key){
      var L=N.filter(function(x){return kind==='c'?x.c===key:x.a.indexOf(key)>-1;});
      L.sort(function(p,q){return q.n-p.n||q.j-p.j||q.d-p.d||p.p-q.p;});
      var B=L.filter(function(x){return x.n>=3;}).slice(0,5);
      if(!B.length) B=L.slice(0,L.length>=8?2:1);
      var R=L.filter(function(x){return B.indexOf(x)<0;});
      return {all:L,big:B,mid:R.filter(function(x){return x.n>=2;}),rest:R.filter(function(x){return x.n<2;}).sort(function(p,q){return q.d-p.d||p.p-q.p;})};
    }
    function title(l){var i=l.lastIndexOf(' ');return i<0?'<em>'+esc(l)+'</em>':esc(l.slice(0,i))+' <em>'+esc(l.slice(i+1))+'</em>';}
    function show(kind,key,label){
      var S=pick(kind,key), k=S.big.length, h='';
      h+='<header class="sec"><p class="lab"><span class="pill">★</span> '+word(S.all.length)+' nella settimana</p><h2>'+title(label)+'</h2>'+
         '<button id="vreset" type="button">× torna a tutta la settimana</button></header>';
      h+='<div class="g12 mosaic vtop">'+S.big.map(function(x,i){return big(x,i,k);}).join('')+
         (k===1?'<div class="vstat" style="--r:5deg"><b>'+S.all.length+'</b><span>'+(S.all.length===1?'notizia':'notizie')+'<br>nella settimana</span></div>':'')+'</div>';
      if(S.mid.length) h+='<div class="vmid">'+S.mid.map(mid).join('')+'</div>';
      if(S.rest.length) h+='<ol class="vrest">'+S.rest.map(row).join('')+'</ol>';
      vista.innerHTML=h; vista.hidden=false; home.hidden=true; decorate(vista);
      document.getElementById('vreset').addEventListener('click',function(){clear(true);});
      pills.forEach(function(p){p.setAttribute('aria-pressed',String(p.getAttribute('data-fk')===kind&&p.getAttribute('data-fv')===key));});
      try{history.replaceState(null,'','#'+kind+'='+key);}catch(e){}
      window.scrollTo(0,Math.max(0,vista.getBoundingClientRect().top+window.pageYOffset-150));
    }
    function clear(scroll){
      vista.hidden=true; vista.innerHTML=''; home.hidden=false;
      pills.forEach(function(p){p.setAttribute('aria-pressed','false');});
      try{history.replaceState(null,'',location.pathname+location.search);}catch(e){}
      if(scroll) window.scrollTo(0,0);
    }
    pills.forEach(function(p){
      p.addEventListener('click',function(e){
        e.preventDefault();
        if(p.getAttribute('aria-pressed')==='true') clear(true);
        else show(p.getAttribute('data-fk'),p.getAttribute('data-fv'),p.getAttribute('data-fl'));
      });
    });
    [].slice.call(document.querySelectorAll('.links a[href^="#"]')).forEach(function(l){
      l.addEventListener('click',function(){ if(home.hidden) clear(false); });
    });
    var m=/^#([ac])=([a-z0-9-]+)$/.exec(location.hash||'');
    if(m){ var p0=document.querySelector('[data-fk="'+m[1]+'"][data-fv="'+m[2]+'"]'); if(p0) show(m[1],m[2],p0.getAttribute('data-fl')); }
  }
  var el=document.getElementById('dati');
  if(el) start(JSON.parse(el.textContent));
  else if(window.fetch) fetch('dati.json').then(function(r){return r.json();}).then(start).catch(function(){});
  /* ultim'ora: controllata ogni 10 minuti da un programma a parte (ultimora.json) */
  function uo(U){
    var hm=function(t){try{return new Date(t.replace(' ','T')+':00Z').toLocaleTimeString('it-IT',{timeZone:'Europe/Rome',hour:'2-digit',minute:'2-digit'});}catch(e){return '';}};
    var o=document.getElementById('agg-ora'); if(o&&U.ora&&U.ora>(o.getAttribute('data-t')||'')){ o.textContent=hm(U.ora);
      var gg=document.getElementById('agg-giorno'); try{ if(gg) gg.textContent=new Date(U.ora.replace(' ','T')+':00Z').toLocaleDateString('it-IT',{timeZone:'Europe/Rome',weekday:'long'}); }catch(e){} }
    var home=document.getElementById('home'), top=document.querySelector('nav.top'); if(!home||!top||!U.notizie||!U.notizie.length) return;
    var E=function(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});};
    var h='<section class="uo" aria-label="Ultim’ora"><p class="uo-lab"><i></i>Ultim’ora</p><ol>'+U.notizie.map(function(n){
      var f=[];n.ar.forEach(function(a){if(f.indexOf(a[0])<0)f.push(a[0]);});
      return '<li><a href="'+E(n.u)+'" target="_blank" rel="noopener">'+E(n.t)+'</a>'+(n.gratis?'<span class="gr">gratis</span>':'')+
        '<span class="uo-f">'+f.length+' testate dalle '+hm(n.primo)+' · '+E(f.join(' · '))+'</span></li>';
    }).join('')+'</ol><p class="uo-nota">Appena uscite, col titolo originale: entro poche ore le trovi qui sotto in italiano.</p></section>';
    top.insertAdjacentHTML('afterend',h);
  }
  if(window.fetch) fetch('ultimora.json?t='+Date.now(),{cache:'no-store'}).then(function(r){return r.ok?r.json():null;}).then(function(U){if(U)uo(U);}).catch(function(){});
})();
