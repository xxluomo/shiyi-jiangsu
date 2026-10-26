'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let csrf = '', items = [], image = '/assets/clay.svg', pendingDelete, uploading = false;
async function api(path, method='GET', body) {
  const response = await fetch(path, {method, headers:{'Content-Type':'application/json','X-CSRF-Token':csrf}, ...(body === undefined ? {} : {body:JSON.stringify(body)})});
  const data = await response.json();
  if (!response.ok) { if(response.status===401 && path!='/api/login') showLogin(); throw new Error(data.error || '请求失败'); }
  return data;
}
function toast(message) { $('#toast').textContent=message; $('#toast').hidden=false; clearTimeout(toast.timer); toast.timer=setTimeout(()=>$('#toast').hidden=true,3500); }
function showLogin() { csrf=''; $('#login-panel').hidden=false; $('#dashboard').hidden=true; for(const d of document.querySelectorAll('dialog[open]')) d.close(); }
function showDashboard(username) { $('#login-panel').hidden=true; $('#dashboard').hidden=false; $('#current-user').textContent=username; loadDashboard(); }
async function loadDashboard() {
  $('#admin-status').textContent='正在读取数据…';
  try {
    const [collection, stats] = await Promise.all([api('/api/items'),api('/api/admin/stats')]);
    items=collection.items;
    $('#stats').innerHTML=`<article><span>馆藏项目</span><strong>${stats.items}</strong><small>持续丰富文化内容</small></article><article><span>已完成答题</span><strong>${stats.attempts}</strong><small>真实提交记录</small></article><article><span>平均得分</span><strong>${stats.average}<em> / 100</em></strong><small>服务器统计</small></article>`;
    $('#item-rows').innerHTML=items.map(item=>`<tr><td><div class="table-title"><img src="${esc(item.image)}" alt=""><strong>${esc(item.title)}</strong></div></td><td>${esc(item.category)}</td><td>${esc(item.region)}</td><td><div class="row-actions"><button data-edit="${item.id}" class="text-link">编辑</button><button data-delete="${item.id}" class="text-link red">删除</button></div></td></tr>`).join('');
    $('#admin-status').textContent=`共 ${items.length} 项。保存修改后，前台刷新即可查看。`;
    $('#recent-attempts').innerHTML=stats.recent.length?`<div class="table-wrap"><table class="admin-table"><thead><tr><th>记录编号</th><th>得分</th><th>题数</th><th>提交时间（UTC）</th></tr></thead><tbody>${stats.recent.map(r=>`<tr><td>#${r.id}</td><td>${r.score} 分</td><td>${r.total}</td><td>${esc(r.created_at)}</td></tr>`).join('')}</tbody></table></div>`:'<p class="empty">暂时还没有答题记录，去前台完成一次小测吧。</p>';
  } catch(error) { $('#admin-status').textContent=error.message; }
}
$('#login-form').addEventListener('submit',async event=>{
  event.preventDefault(); const form=event.currentTarget; const button=form.querySelector('button'); button.disabled=true; $('#login-error').textContent='';
  try { const data=await api('/api/login','POST',Object.fromEntries(new FormData(form))); csrf=data.csrf; form.reset(); showDashboard(data.username); }
  catch(error) { $('#login-error').textContent=error.message; } finally { button.disabled=false; }
});
$('#logout').onclick=async()=>{try{await api('/api/logout','POST',{}); showLogin();}catch(error){toast(error.message);}};
function openEditor(item) {
  const form=$('#item-form'); form.reset(); $('#image-upload').value=''; $('#edit-error').textContent=''; $('#upload-status').textContent='配图需有使用权限，请在正文注明来源或原创身份。';
  $('#edit-heading').textContent=item?'编辑馆藏':'新增馆藏';
  for(const option of [...$('#image-select').options]) if(option.dataset.custom) option.remove();
  if(item) { for(const key of ['id','title','category','region','summary','content','source_name','source_url']) form.elements[key].value=item[key]; form.elements.steps.value=item.steps.join('\n'); }
  image=item?.image || '/assets/clay.svg'; setImage(image); $('#edit-dialog').showModal();
}
function setImage(url) {
  const select=$('#image-select');
  if(![...select.options].some(option=>option.value===url)) { const opt=new Option('已上传的图片',url); opt.dataset.custom='true'; select.add(opt); }
  select.value=url; image=url; $('#image-preview').src=url;
}
$('#new-item').onclick=()=>openEditor();
$('#image-select').onchange=event=>setImage(event.target.value);
$('#close-edit').onclick=$('#cancel-edit').onclick=()=>{if(!uploading) $('#edit-dialog').close();};
$('#image-upload').addEventListener('change',async event=>{
  const file=event.target.files[0]; if(!file) return;
  if(file.size>6*1024*1024) { $('#edit-error').textContent='图片不能超过6MB'; event.target.value=''; return; }
  uploading=true; $('#save-item').disabled=true; $('#edit-error').textContent=''; $('#upload-status').textContent='正在上传…';
  try {
    const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader(); reader.onload=()=>resolve(reader.result.split(',')[1]); reader.onerror=()=>reject(new Error('文件读取失败')); reader.readAsDataURL(file);});
    const data=await api('/api/upload','POST',{data:encoded}); setImage(data.url); $('#upload-status').textContent='图片上传成功。点击保存项目，才能更新馆藏。';
  } catch(error) { $('#edit-error').textContent=error.message; $('#upload-status').textContent='上传失败，原配图未改变。'; }
  finally { uploading=false; $('#save-item').disabled=false; }
});
$('#item-form').addEventListener('submit',async event=>{
  event.preventDefault(); if(uploading)return;
  const data=Object.fromEntries(new FormData(event.currentTarget)); const id=data.id; delete data.id; data.steps=data.steps.split('\n').map(s=>s.trim()).filter(Boolean); data.image=image;
  $('#save-item').disabled=true; $('#edit-error').textContent='';
  try { await api(id?'/api/items/'+id:'/api/items', id?'PUT':'POST',data); $('#edit-dialog').close(); toast('馆藏已保存'); await loadDashboard(); }
  catch(error) { $('#edit-error').textContent=error.message; } finally { $('#save-item').disabled=false; }
});
$('#item-rows').addEventListener('click',event=>{
  const edit=event.target.closest('[data-edit]'), del=event.target.closest('[data-delete]');
  if(edit) openEditor(items.find(item=>item.id===Number(edit.dataset.edit)));
  if(del) { pendingDelete=items.find(item=>item.id===Number(del.dataset.delete)); $('#delete-name').textContent=pendingDelete.title; $('#delete-error').textContent=''; $('#delete-dialog').showModal(); }
});
$('#cancel-delete').onclick=()=>$('#delete-dialog').close();
$('#confirm-delete').onclick=async()=>{
  $('#confirm-delete').disabled=true;
  try { await api('/api/items/'+pendingDelete.id,'DELETE'); $('#delete-dialog').close(); toast('项目已删除'); await loadDashboard(); }
  catch(error) { $('#delete-error').textContent=error.message; } finally { $('#confirm-delete').disabled=false; }
};
(async()=>{try{const data=await api('/api/session'); if(data.logged_in){csrf=data.csrf;showDashboard(data.username);}}catch(error){$('#login-error').textContent=error.message;}})();
