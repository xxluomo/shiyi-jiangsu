'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || '请求失败，请稍后再试');
  return data;
}
let category = '', listRequest = 0, detailRequest = 0;
function toast(message) { $('#toast').textContent = message; $('#toast').hidden = false; clearTimeout(toast.timer); toast.timer = setTimeout(() => $('#toast').hidden = true, 4500); }
async function loadItems() {
  const request = ++listRequest;
  $('#collection-status').textContent = '正在读取馆藏…';
  try {
    const data = await api('/api/items?' + new URLSearchParams({q: $('#search').value.trim(), category}));
    if (request !== listRequest) return;
    $('#collection-status').textContent = `共 ${data.items.length} 项馆藏 · 点击卡片阅读故事`;
    $('#empty').hidden = !!data.items.length;
    $('#collection-grid').innerHTML = data.items.map((item, i) => `<button class="collection-card" data-id="${item.id}" aria-label="查看${esc(item.title)}详情"><div class="card-art"><img src="${esc(item.image)}" alt="${esc(item.title)}主题配图" loading="lazy"><span class="card-index">${String(i+1).padStart(2,'0')}</span><span class="card-arrow">↗</span></div><div class="card-meta"><span>${esc(item.category)}</span><span>${esc(item.region)}</span></div><h3>${esc(item.title)}</h3><p>${esc(item.summary)}</p></button>`).join('');
  } catch (error) { if (request === listRequest) { $('#collection-status').textContent = error.message; $('#collection-grid').innerHTML = ''; $('#empty').hidden = true; } }
}
$('.tabs').addEventListener('click', event => {
  const button = event.target.closest('[data-category]'); if (!button) return;
  category = button.dataset.category;
  document.querySelectorAll('.tab').forEach(tab => { tab.classList.toggle('active', tab === button); tab.setAttribute('aria-pressed', String(tab === button)); });
  loadItems();
});
$('#search-form').addEventListener('submit', event => { event.preventDefault(); loadItems(); });
$('#clear-search').addEventListener('click', () => { $('#search').value = ''; $('.tab').click(); });
$('#collection-grid').addEventListener('click', async event => {
  const card = event.target.closest('[data-id]'); if (!card) return;
  const request = ++detailRequest;
  try {
    const item = await api('/api/items/' + card.dataset.id);
    if (request !== detailRequest) return;
    $('#detail-content').innerHTML = `<div class="detail-hero"><button id="enlarge-image" class="detail-image" aria-label="放大项目配图"><img src="${esc(item.image)}" alt="${esc(item.title)}配图"><span>点击放大 ↗</span></button><div><span class="tag">${esc(item.category)} / ${esc(item.region)}</span><h2>${esc(item.title)}</h2><p>${esc(item.summary)}</p><small class="muted">馆藏插画为示意；上传图片以管理员标注为准。</small></div></div><div class="detail-body"><div class="eyebrow">手艺的故事</div>${item.content.split('\n').filter(Boolean).map(p=>`<p>${esc(p)}</p>`).join('')}<h3>工艺概览</h3><p class="muted">以下为教学性概览，实际制作请参考专业资料。</p><ol class="process-list">${item.steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol><div class="source-box">资料参考：<a href="${esc(item.source_url)}" target="_blank" rel="noopener noreferrer">${esc(item.source_name)} ↗</a><br><small>正文为整理性介绍，非原文转载。</small></div></div>`;
    $('#enlarge-image').addEventListener('click', () => { $('#zoom-image').src = item.image; $('#zoom-image').alt = item.title + '放大配图'; $('#zoom-dialog').showModal(); });
    if (!$('#detail-dialog').open) $('#detail-dialog').showModal();
  } catch (error) { toast(error.message); }
});
$('#close-detail').addEventListener('click', () => $('#detail-dialog').close());
$('#close-zoom').addEventListener('click', () => $('#zoom-dialog').close());
for (const name of ['detail-dialog','zoom-dialog']) $('#'+name).addEventListener('click', event => { if (event.target === event.currentTarget) { const r=event.currentTarget.getBoundingClientRect(); if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom) event.currentTarget.close(); } });
let currentQuiz;
async function startQuiz() {
  $('#quiz-content').innerHTML = '<p role="status">正在抽取题目…</p>';
  try {
    currentQuiz = await api('/api/quiz');
    $('#quiz-content').innerHTML = `<form id="quiz-form">${currentQuiz.questions.map((q,i)=>`<fieldset class="question"><legend><span>${String(i+1).padStart(2,'0')}</span>${esc(q.prompt)}</legend><div class="options">${q.options.map((option,j)=>`<label><input type="radio" name="q${q.id}" value="${j}" required><span>${String.fromCharCode(65+j)}. ${esc(option)}</span></label>`).join('')}</div></fieldset>`).join('')}<p id="quiz-error" class="error" role="alert"></p><button class="button" type="submit">提交并查看解析 →</button></form>`;
    $('#quiz-form').addEventListener('submit', submitQuiz);
  } catch (error) { $('#quiz-content').innerHTML = `<p class="error">${esc(error.message)}</p><button id="retry-quiz" class="button">重新加载</button>`; $('#retry-quiz').onclick = startQuiz; }
}
async function submitQuiz(event) {
  event.preventDefault();
  const button = event.currentTarget.querySelector('button[type="submit"]'); button.disabled = true;
  const answers = {}; const form = new FormData(event.currentTarget);
  for (const q of currentQuiz.questions) answers[q.id] = Number(form.get('q'+q.id));
  try {
    const result = await api('/api/quiz/submit', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ticket:currentQuiz.ticket, answers})});
    $('#quiz-content').innerHTML = `<div class="quiz-result"><span class="eyebrow">探索完成 / YOUR RESULT</span><h3><strong>${result.score}</strong> 分</h3><p>答对 ${result.correct} / ${result.total} 题。${result.score===100?'很棒，继续发现更多手艺。':'每一次好奇，都让我们更靠近传统。'}</p></div><div class="result-list">${result.results.map((r,i)=>`<article><h4><span class="${r.correct?'correct':'incorrect'}">${r.correct?'✓':'○'}</span> ${i+1}. ${esc(r.prompt)}</h4><p>正确答案：${esc(r.correct_text)}</p><p class="muted">${esc(r.explanation)}</p></article>`).join('')}</div><button class="button secondary" id="restart-quiz">再挑战一次 ↻</button>`;
    $('#restart-quiz').onclick = startQuiz;
  } catch (error) { $('#quiz-error').textContent = error.message; button.disabled = false; }
}
$('#start-quiz').addEventListener('click', startQuiz);
loadItems();
