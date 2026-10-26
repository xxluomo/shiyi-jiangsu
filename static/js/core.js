export const $ = s => document.querySelector(s);
export const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const state = {catalog:null,user:null,csrf:'',favorites:[],mode:'login'};
export const icon = (name,size=20) => {
 const paths={arrow:'M5 12h14m-6-6 6 6-6 6',search:'m21 21-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',heart:'M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8',user:'M20 21v-2a7 7 0 0 0-14 0v2M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0',map:'m3 5 6-3 6 3 6-3v17l-6 3-6-3-6 3Zm6-3v17m6-14v17',play:'m9 5 12 7-12 7Z',close:'m6 6 12 12M18 6 6 18',check:'m5 12 4 4L20 5',grid:'M3 3h7v7H3Zm11 0h7v7h-7ZM3 14h7v7H3Zm11 0h7v7h-7Z',download:'M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4',undo:'M3 7h10a7 7 0 0 1 0 14M3 7l5-5M3 7l5 5',sound:'m3 9 5 0 5-5v16l-5-5H3Zm13-2a7 7 0 0 1 0 10m3-13a11 11 0 0 1 0 16',spark:'m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3Z',book:'M3 4q5-2 9 1 4-3 9-1v16q-5-2-9 1-4-3-9-1Zm9 1v16'};
 return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[name]||paths.arrow}"/></svg>`;
};
export async function api(path,method='GET',body) {
 const response=await fetch(path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':state.csrf},...(body===undefined?{}:{body:JSON.stringify(body)})});
 const data=await response.json();
 if(!response.ok){if(response.status===401&&path!='/api/login'){state.user=null;state.csrf='';updateNav();}throw new Error(data.error||'请求失败');}
 return data;
}
export function toast(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').hidden=true,4000);}
export async function refreshCatalog(){state.catalog=await api('/api/catalog');return state.catalog;}
export function updateNav(){
 $('#user-action').innerHTML=state.user?`<span class="avatar">${esc(state.user.nickname.slice(0,1))}</span><span>${esc(state.user.nickname)}</span>`:`${icon('user',18)}<span>登录 / 注册</span>`;
 $('#favorites-count').textContent=state.favorites.length;
 const current=(location.hash.slice(1).split('/')[0]||'home');
 document.querySelectorAll('.nav-link').forEach(a=>{a.classList.toggle('active',a.dataset.page===current);if(a.dataset.page===current)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
}
export function auth(mode='login'){
 state.mode=mode;const register=mode==='register';
 $('#auth-body').innerHTML=`<div class="auth-brand"><span class="seal">拾</span><span>拾遗江苏 <small>JIANGSU HERITAGE</small></span></div><div class="eyebrow">CONTINUE YOUR DISCOVERY</div><h2>${register?'开启你的非遗之旅':'欢迎回到拾遗江苏'}</h2><p class="muted">登录后，把喜欢的手艺与自己的创作留在这里。</p><form id="auth-form"><label>账号<input name="username" autocomplete="username" placeholder="3—24位字母、数字或下划线" required minlength="3" maxlength="24"></label>${register?'<label>昵称<input name="nickname" maxlength="30" placeholder="怎么称呼你？" required></label>':''}<label>密码<input name="password" type="password" autocomplete="${register?'new-password':'current-password'}" value="123456" required minlength="6" maxlength="128"></label><p id="auth-error" class="error" role="alert"></p><button class="btn wide" type="submit">${register?'注册并登录':'登录'} ${icon('arrow',17)}</button></form><p class="auth-switch">${register?'已经有账号？':'第一次来到这里？'} <button id="auth-switch" class="text-button">${register?'去登录':'创建账号'}</button></p><div class="demo-note">本地演示：student / 123456<br>管理员：admin / 123456</div>`;
 $('#auth-switch').onclick=()=>auth(register?'login':'register');
 $('#auth-form').onsubmit=async event=>{event.preventDefault();const form=event.currentTarget;const button=form.querySelector('button[type=submit]');button.disabled=true;
  try{const data=await api(register?'/api/register':'/api/login','POST',Object.fromEntries(new FormData(form)));state.user=data.user;state.csrf=data.csrf;state.favorites=(await api('/api/favorites')).ids;updateNav();$('#auth-dialog').close();toast('欢迎，'+state.user.nickname);window.dispatchEvent(new Event('authchange'));}
  catch(error){$('#auth-error').textContent=error.message;}finally{button.disabled=false;}};
 if(!$('#auth-dialog').open)$('#auth-dialog').showModal();
}
export async function favorite(id){
 if(!state.user){auth();return;}
 try{const exists=state.favorites.includes(id);await api('/api/favorites/'+id,exists?'DELETE':'POST',exists?undefined:{});state.favorites=exists?state.favorites.filter(n=>n!==id):[...state.favorites,id];updateNav();syncFavorites();toast(exists?'已取消收藏':'已收藏到你的个人中心');}
 catch(error){toast(error.message);}
}
export function syncFavorites(){document.querySelectorAll('[data-favorite]').forEach(button=>{const active=state.favorites.includes(Number(button.dataset.favorite));button.classList.toggle('is-favorite',active);button.setAttribute('aria-pressed',String(active));button.setAttribute('aria-label',active?'取消收藏':'收藏项目');});}
export function card(item){const saved=state.favorites.includes(item.id);return `<article class="heritage-card"><div class="card-image"><a href="#item/${item.id}" aria-label="查看${esc(item.title)}"><img src="${esc(item.image)}" alt="${esc(item.title)}主题示意插画" loading="lazy"></a><span class="image-label">${esc(item.city)}</span><button class="favorite-button ${saved?'is-favorite':''}" data-favorite="${item.id}" aria-label="${saved?'取消收藏':'收藏项目'}" aria-pressed="${saved}">${icon('heart',18)}</button></div><div class="card-body"><div class="card-caption"><span>${esc(item.category)}</span><span>${esc(item.theme)}</span></div><h3><a href="#item/${item.id}">${esc(item.title)}</a></h3><p>${esc(item.summary)}</p><a class="card-discover" href="#item/${item.id}">走近这门手艺 ${icon('arrow',16)}</a></div></article>`;}
export function pageHeading(en,title,description){return `<div class="page-heading"><div class="eyebrow">${en}</div><h1>${title}</h1><p>${description}</p></div>`;}
export function dateTime(s){return s?new Date(s.replace(' ','T')+'Z').toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false}):'';}
export function errorPanel(error){return `<div class="empty-state"><h2>暂时无法读取内容</h2><p>${esc(error.message)}</p><button class="btn" data-reload>重新加载 ${icon('arrow',16)}</button></div>`;}
export function confirmAction(title,message,action){$('#confirm-title').textContent=title;$('#confirm-message').textContent=message;$('#confirm-error').textContent='';$('#confirm-yes').onclick=async()=>{const button=$('#confirm-yes');button.disabled=true;try{await action();$('#confirm-dialog').close();}catch(error){$('#confirm-error').textContent=error.message;}finally{button.disabled=false;}};$('#confirm-dialog').showModal();}
