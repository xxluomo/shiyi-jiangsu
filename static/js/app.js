import {$,state,api,refreshCatalog,updateNav,auth,favorite,errorPanel,toast} from './core.js';
import {home,explore,item} from './exhibition.js';
import {atlas} from './atlas.js';
import {workshop} from './workshop.js';
import {learn} from './learn.js';
import {account} from './account.js';
import {admin} from './admin.js';

let revision=0;
async function render(){
 const current=++revision;
 const [page='home',arg='']=(location.hash.slice(1)||'home').split('/');
 document.querySelectorAll('audio').forEach(audio=>audio.pause());
 updateNav();
 $('#app').innerHTML='<div class="loading-screen"><span class="seal">拾</span><p>正在展开文化长卷…</p></div>';
 window.scrollTo({top:0,behavior:'instant'});
 try{await refreshCatalog();if(current!==revision)return;const fn={home,explore,atlas,workshop,learn,account,admin,item}[page]||home;await fn(arg);}
 catch(error){if(current===revision)$('#app').innerHTML=errorPanel(error);}
 updateNav();
}
document.addEventListener('click',event=>{
 const close=event.target.closest('[data-close]');if(close)$('#'+close.dataset.close).close();
 const fav=event.target.closest('[data-favorite]');if(fav){event.preventDefault();favorite(Number(fav.dataset.favorite));}
 if(event.target.closest('[data-login]'))auth();
 if(event.target.closest('[data-reload]'))render();
});
$('#user-action').onclick=()=>state.user?location.hash='#account':auth();
window.addEventListener('hashchange',render);
window.addEventListener('authchange',()=>{if(['account','admin'].includes((location.hash.slice(1)||'').split('/')[0]))render();});
let zoom={x:0,y:0,start:null};
const applyZoom=()=>$('#zoom-image').style.transform=`translate(${zoom.x}px,${zoom.y}px) scale(${$('#zoom-range').value})`;
$('#zoom-range').oninput=applyZoom;
$('.zoom-stage').onpointerdown=event=>{zoom.start={x:event.clientX-zoom.x,y:event.clientY-zoom.y};event.currentTarget.setPointerCapture(event.pointerId);};
$('.zoom-stage').onpointermove=event=>{if(zoom.start){zoom.x=event.clientX-zoom.start.x;zoom.y=event.clientY-zoom.start.y;applyZoom();}};
$('.zoom-stage').onpointerup=$('.zoom-stage').onpointercancel=()=>zoom.start=null;
$('#zoom-dialog').addEventListener('close',()=>{zoom={x:0,y:0,start:null};$('#zoom-range').value=1;applyZoom();});
(async()=>{try{const session=await api('/api/session');state.user=session.user;state.csrf=session.csrf;if(state.user)state.favorites=(await api('/api/favorites')).ids;}catch(error){toast(error.message);}if(location.pathname.startsWith('/admin')&&!location.hash)location.hash='#admin';else render();})();
