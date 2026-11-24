'use strict';
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const T = {
  en: {
    nav_chat: 'Chats', nav_models: 'Models', nav_presets: 'Presets', nav_apis: 'APIs',
    new_chat: 'New chat', send: 'Send', stop: 'Stop', thinking: 'Thinking', attach: 'Attach',
    placeholder: 'Write a message…', summarize: 'Summarize', export: 'Export', delete: 'Delete',
    sys_prompt: 'System prompt', save: 'Save', regenerate: 'Regenerate', no_model: 'No model is loaded.',
    open_models: 'Open Models', load: 'Load', unload: 'Unload', loaded: 'Loaded', refresh: 'Refresh',
    models_lead: 'GGUF files found in your models folder. Choose settings before a model is loaded into RAM.',
    presets_lead: 'A preset bundles load settings (applied when the model enters RAM) with sampling defaults.',
    apis_lead: 'Turn a prompt, a model and an optional JSON schema into a ready-to-call endpoint.',
    empty_chat_t: 'Start a conversation', empty_chat: 'Chats are stored independently of the model, so you can switch models at any time.',
    no_models: 'No GGUF files found. Put .gguf files in the models folder (the mounted /models volume in Docker), then reload this page.',
    preset: 'Preset', ctx: 'Context (n_ctx)', gpu: 'GPU layers (-1 = all)', threads: 'Threads', batch: 'Batch size',
    flash: 'Flash attention', mmap: 'Memory-map file', mlock: 'Lock in RAM', temp: 'Temperature', topp: 'Top-p',
    topk: 'Top-k', maxtok: 'Max tokens', rep: 'Repeat penalty', est: 'Estimated RAM', of: 'of', budget: 'budget',
    force: 'Load anyway', new_preset: 'New preset', name: 'Name', any_model: 'Any model', model: 'Model',
    prefilled: 'Template already opens <think>', offdir: 'Text that turns thinking off (e.g. /no_think)',
    slug: 'Slug (URL name)', desc: 'Description', tmpl: 'Input template ({{input}}, {{variable}})',
    schema: 'Output JSON schema (optional)', pinned: 'Pinned model (optional)', new_api: 'New API', run: 'Run',
    input: 'Input', vars: 'Variables (JSON)', summary: 'Summary', free: 'free', ram: 'RAM', saved: 'Saved',
    deleted: 'Deleted', confirm_del: 'Delete this? This cannot be undone.', loading: 'Loading…',
    api_key: 'This server needs an API key:', untitled: 'New chat', you: 'You', switched: 'Model loaded',
    unloaded: 'Model unloaded', vision: 'vision', size: 'Size', image_ok: 'Images', stopped: 'stopped',
  },
  ar: {
    nav_chat: 'المحادثات', nav_models: 'النماذج', nav_presets: 'الإعدادات المسبقة', nav_apis: 'واجهات API',
    new_chat: 'محادثة جديدة', send: 'إرسال', stop: 'إيقاف', thinking: 'التفكير', attach: 'إرفاق',
    placeholder: 'اكتب رسالة…', summarize: 'تلخيص', export: 'تصدير', delete: 'حذف',
    sys_prompt: 'تعليمات النظام', save: 'حفظ', regenerate: 'إعادة التوليد', no_model: 'لا يوجد نموذج محمّل.',
    open_models: 'افتح النماذج', load: 'تحميل', unload: 'تفريغ', loaded: 'محمّل', refresh: 'تحديث',
    models_lead: 'ملفات GGUF الموجودة في مجلد النماذج. اختر الإعدادات قبل أن يُحمَّل النموذج إلى الذاكرة.',
    presets_lead: 'الإعداد المسبق يجمع إعدادات التحميل (تُطبَّق عند دخول النموذج إلى الذاكرة) مع إعدادات التوليد الافتراضية.',
    apis_lead: 'حوّل تعليمات ونموذجًا ومخطط JSON اختياريًا إلى نقطة نهاية جاهزة للاستدعاء.',
    empty_chat_t: 'ابدأ محادثة', empty_chat: 'تُحفظ المحادثات بشكل مستقل عن النموذج، فيمكنك تبديل النموذج في أي وقت.',
    no_models: 'لا توجد ملفات GGUF. ضع ملفات .gguf في مجلد النماذج (مجلد /models المربوط في Docker) ثم أعد تحميل الصفحة.',
    preset: 'الإعداد المسبق', ctx: 'طول السياق (n_ctx)', gpu: 'طبقات GPU (‏-1 = الكل)', threads: 'عدد الخيوط', batch: 'حجم الدفعة',
    flash: 'Flash attention', mmap: 'تعيين الملف في الذاكرة', mlock: 'تثبيت في الذاكرة', temp: 'درجة الحرارة', topp: 'Top-p',
    topk: 'Top-k', maxtok: 'أقصى عدد رموز', rep: 'عقوبة التكرار', est: 'الذاكرة المقدّرة', of: 'من', budget: 'الميزانية',
    force: 'حمّل رغم ذلك', new_preset: 'إعداد جديد', name: 'الاسم', any_model: 'أي نموذج', model: 'النموذج',
    prefilled: 'القالب يفتح <think> مسبقًا', offdir: 'نص يوقف التفكير (مثل /no_think)',
    slug: 'المعرّف (اسم الرابط)', desc: 'الوصف', tmpl: 'قالب الإدخال ({{input}}, {{variable}})',
    schema: 'مخطط JSON للمخرجات (اختياري)', pinned: 'نموذج ثابت (اختياري)', new_api: 'واجهة جديدة', run: 'تشغيل',
    input: 'الإدخال', vars: 'المتغيرات (JSON)', summary: 'الملخص', free: 'متاح', ram: 'الذاكرة', saved: 'تم الحفظ',
    deleted: 'تم الحذف', confirm_del: 'حذف هذا العنصر؟ لا يمكن التراجع.', loading: 'جارٍ التحميل…',
    api_key: 'هذا الخادم يحتاج مفتاح API:', untitled: 'محادثة جديدة', you: 'أنت', switched: 'تم تحميل النموذج',
    unloaded: 'تم تفريغ النموذج', vision: 'رؤية', size: 'الحجم', image_ok: 'الصور', stopped: 'أُوقف',
  },
};
const S = { lang: localStorage.gb_lang || 'en', chatId: null, chat: null, chats: [], models: [], presets: [], apis: [],
  status: null, attachments: [], streaming: null, editPreset: null, editApi: null };
const t = k => T[S.lang][k] ?? T.en[k] ?? k;

function applyLang() {
  document.documentElement.lang = S.lang;
  document.documentElement.dir = S.lang === 'ar' ? 'rtl' : 'ltr';
  $$('[data-i]').forEach(e => e.textContent = t(e.dataset.i));
  $$('[data-ph]').forEach(e => e.placeholder = t(e.dataset.ph));
  $('#langBtn').textContent = S.lang === 'ar' ? 'English' : 'العربية';
}

// ---------- network ----------
const headers = () => ({ 'Content-Type': 'application/json', ...(localStorage.gb_key ? { 'x-api-key': localStorage.gb_key } : {}) });
const mk = opts => {
  const h = { ...headers(), ...(opts.headers || {}) };
  for (const k of Object.keys(h)) if (h[k] === undefined) delete h[k];  // let the browser set multipart boundaries
  return { ...opts, headers: h };
};
async function raw(path, opts = {}) {
  let res = await fetch(path, mk(opts));
  if (res.status === 401) {
    const k = prompt(t('api_key'));
    if (!k) throw new Error('Unauthorized');
    localStorage.gb_key = k;
    res = await fetch(path, mk(opts));
  }
  if (!res.ok) {
    let msg = res.statusText, details;
    try { const j = await res.json(); msg = j.error?.message || JSON.stringify(j.detail || j); details = j.error?.details; } catch {}
    const e = new Error(msg); e.status = res.status; e.details = details; throw e;
  }
  return res;
}
async function api(path, { method = 'GET', body } = {}) {
  const res = await raw(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });
  return res.status === 204 ? null : res.json();
}
async function sse(path, body, onEvent, signal) {
  const res = await raw(path, { method: 'POST', body: JSON.stringify(body), signal });
  const reader = res.body.getReader(), dec = new TextDecoder();
  let buf = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf('\n\n')) >= 0) {
      const block = buf.slice(0, i); buf = buf.slice(i + 2);
      let ev = 'message', data = '';
      for (const l of block.split('\n')) {
        if (l.startsWith('event:')) ev = l.slice(6).trim(); else if (l.startsWith('data:')) data += l.slice(5).trim();
      }
      if (data) onEvent(ev, JSON.parse(data));
    }
  }
}
let toastTimer;
function toast(msg, err = false) {
  const el = $('#toast'); el.textContent = msg; el.className = 'toast on' + (err ? ' err' : '');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => el.className = 'toast', 3500);
}
const guard = fn => async (...a) => { try { return await fn(...a); } catch (e) { if (e.name !== 'AbortError') toast(e.message, true); } };

// ---------- helpers ----------
const fmtGB = b => (b / 1024 ** 3).toFixed(b > 10 * 1024 ** 3 ? 0 : 1) + ' GB';
function md(text) {
  return String(text ?? '').split('```').map((p, i) => i % 2
    ? '<pre><code>' + esc(p.replace(/^[\w+#.-]*\n/, '')) + '</code></pre>'
    : esc(p).replace(/`([^`\n]+)`/g, '<code>$1</code>').replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')).join('');
}
const keyQ = () => localStorage.gb_key ? '?key=' + encodeURIComponent(localStorage.gb_key) : '';

// ---------- navigation + meter ----------
function show(view) {
  $$('.view').forEach(v => v.classList.toggle('on', v.id === 'view-' + view));
  $$('#nav button').forEach(b => b.classList.toggle('on', b.dataset.view === view));
  ({ chat: loadChats, models: renderModels, presets: renderPresets, apis: renderApis })[view]?.();
}
async function refreshMeter() {
  try {
    const s = await api('/api/system'); S.status = s.model;
    const m = s.memory, total = m.total, used = total - m.available, rss = m.process_rss;
    const loaded = s.model.loaded ? s.model.model : null;
    $('#mModel').style.width = (rss / total * 100) + '%';
    $('#mOther').style.width = (Math.max(used - rss, 0) / total * 100) + '%';
    $('#meterLabel').textContent = `${loaded ? loaded.name + ' · ' + fmtGB(rss) + ' · ' : ''}${t('ram')} ${fmtGB(m.available)} ${t('free')} / ${fmtGB(total)}`;
    $('#noModel').hidden = !!loaded || !$('#view-chat').classList.contains('on');
    $('#regen').hidden = !(S.chat?.messages?.length);
  } catch {}
}

// ---------- chats ----------
async function loadChats() {
  S.chats = await api('/api/chats');
  $('#chats').innerHTML = S.chats.map(c => `<li data-id="${c.id}" class="${c.id === S.chatId ? 'on' : ''}" title="${esc(c.title)}">${esc(c.title)}</li>`).join('');
  if (!S.chatId && S.chats.length) return openChat(S.chats[0].id);
  if (!S.chatId) renderEmpty();
  refreshMeter();
}
function renderEmpty() {
  $('#chatTitle').textContent = t('untitled'); $('#summaryBox').hidden = true;
  $('#msgs').innerHTML = `<div class="empty"><h2>${esc(t('empty_chat_t'))}</h2><p>${esc(t('empty_chat'))}</p></div>`;
  $('#sysText').value = ''; S.chat = null;
}
async function openChat(id) {
  S.chatId = id; S.chat = await api('/api/chats/' + id);
  $('#chatTitle').textContent = S.chat.title; $('#sysText').value = S.chat.system_prompt;
  const sb = $('#summaryBox'); sb.hidden = !S.chat.summary; sb.textContent = S.chat.summary ? t('summary') + ': ' + S.chat.summary : '';
  $('#msgs').innerHTML = S.chat.messages.length ? '' : `<div class="empty"><h2>${esc(t('empty_chat_t'))}</h2><p>${esc(t('empty_chat'))}</p></div>`;
  S.chat.messages.forEach(m => $('#msgs').append(msgEl(m)));
  scrollDown();
  $$('#chats li').forEach(li => li.classList.toggle('on', li.dataset.id === id));
  refreshMeter();
}
const scrollDown = () => { const m = $('#msgs'); m.scrollTop = m.scrollHeight; };
function msgEl(m) {
  const el = document.createElement('div'); el.className = 'msg ' + m.role; el.dataset.id = m.id || '';
  const atts = (m.attachments || []).map(id => `<span class="att" data-att="${id}">📎 ${esc(id.slice(0, 6))}</span>`).join('');
  const think = m.reasoning ? `<details class="think"><summary>${esc(t('thinking'))}</summary><div>${esc(m.reasoning)}</div></details>` : '';
  const tps = m.usage?.tokens_per_second ? ` · ${m.usage.tokens_per_second} tok/s` : '';
  const stopped = m.usage?.finish_reason === 'cancelled' ? ` · ${t('stopped')}` : '';
  const meta = m.role === 'assistant' && m.model ? `<div class="meta">${esc(m.model.split('/').pop())}${tps}${stopped}</div>` : '';
  el.innerHTML = `${think}<div class="body">${atts}${md(m.content)}</div>${meta}`;
  return el;
}
const newChat = guard(async () => { const c = await api('/api/chats', { method: 'POST', body: {} }); S.chatId = c.id; await loadChats(); await openChat(c.id); $('#input').focus(); });

const send = guard(async (regenerate = false) => {
  if (S.streaming) return;
  const text = $('#input').value.trim();
  if (!regenerate && !text && !S.attachments.length) return;
  if (!S.chatId) { const c = await api('/api/chats', { method: 'POST', body: {} }); S.chatId = c.id; S.chat = { ...c, messages: [] }; }
  const id = S.chatId, atts = S.attachments.map(a => a.id);
  const box = $('#msgs'); box.querySelector('.empty')?.remove();
  if (regenerate) box.querySelector('.msg.assistant:last-child')?.remove();
  else box.append(msgEl({ role: 'user', content: text, attachments: atts }));
  const el = msgEl({ role: 'assistant', content: '' }); box.append(el); scrollDown();
  const body = el.querySelector('.body'); let think = null, tbox = null, content = '', reasoning = '';
  const ctrl = new AbortController(); S.streaming = ctrl; toggleSend(true);
  $('#input').value = ''; S.attachments = []; renderChips();
  try {
    await sse(`/api/chats/${id}/messages`, { content: regenerate ? '' : text, attachments: atts, thinking: $('#think').checked, regenerate }, (ev, d) => {
      if (ev === 'token') { content += d.text; body.innerHTML = md(content); }
      else if (ev === 'reasoning') {
        if (!think) { think = document.createElement('details'); think.className = 'think'; think.open = true; think.innerHTML = `<summary>${esc(t('thinking'))}</summary><div></div>`; tbox = think.querySelector('div'); el.prepend(think); }
        reasoning += d.text; tbox.textContent = reasoning;
      } else if (ev === 'error') toast(d.message, true);
      scrollDown();
    }, ctrl.signal);
  } finally { S.streaming = null; toggleSend(false); await loadChats(); await openChat(id); }
});
const toggleSend = on => { $('#sendBtn').hidden = on; $('#stopBtn').hidden = !on; };

function renderChips() {
  $('#chips').innerHTML = S.attachments.map((a, i) => `<span class="att">${a.kind === 'image' ? '🖼' : '📄'} ${esc(a.filename)} <button data-rm="${i}" aria-label="remove">✕</button></span>`).join('');
}
async function uploadFile(f) {
  const fd = new FormData(); fd.append('file', f);
  const res = await raw('/api/uploads', { method: 'POST', body: fd, headers: { 'Content-Type': undefined } });
  S.attachments.push(await res.json()); renderChips();
}
async function download(fmt) {
  const res = await raw(`/api/chats/${S.chatId}/export?format=${fmt}`);
  const a = document.createElement('a'); a.href = URL.createObjectURL(await res.blob());
  a.download = `${S.chat.title.slice(0, 40)}.${fmt}`; a.click(); URL.revokeObjectURL(a.href);
}

// ---------- shared field renderers ----------
const LOAD_DEFAULTS = { n_ctx: 4096, n_gpu_layers: 0, n_threads: '', n_batch: 512, flash_attn: false, use_mmap: true, use_mlock: false };
function loadFields(v = {}) {
  v = { ...LOAD_DEFAULTS, ...v };
  const num = (k, label) => `<label>${t(label)}<input type="number" name="${k}" value="${v[k] ?? ''}"></label>`;
  const chk = (k, label) => `<label class="inline"><input type="checkbox" name="${k}" ${v[k] ? 'checked' : ''}>${t(label)}</label>`;
  return num('n_ctx', 'ctx') + num('n_gpu_layers', 'gpu') + num('n_threads', 'threads') + num('n_batch', 'batch') + chk('flash_attn', 'flash') + chk('use_mmap', 'mmap') + chk('use_mlock', 'mlock');
}
function readLoad(root) {
  const g = n => root.querySelector(`[name=${n}]`), o = {};
  for (const k of ['n_ctx', 'n_gpu_layers', 'n_batch']) o[k] = +g(k).value;
  if (g('n_threads').value) o.n_threads = +g('n_threads').value;
  for (const k of ['flash_attn', 'use_mmap', 'use_mlock']) o[k] = g(k).checked;
  return o;
}
const GEN_DEFAULTS = { temperature: 0.7, top_p: 0.95, top_k: 40, max_tokens: 1024, repeat_penalty: 1.1 };
function genFields(v = {}) {
  v = { ...GEN_DEFAULTS, ...v };
  const f = (k, label, step) => `<label>${t(label)}<input type="number" step="${step}" name="g_${k}" value="${v[k]}"></label>`;
  return f('temperature', 'temp', '0.05') + f('top_p', 'topp', '0.01') + f('top_k', 'topk', '1') + f('max_tokens', 'maxtok', '1') + f('repeat_penalty', 'rep', '0.01');
}
const readGen = root => Object.fromEntries(Object.keys(GEN_DEFAULTS).map(k => [k, +root.querySelector(`[name=g_${k}]`).value]));

// ---------- models ----------
const renderModels = guard(async () => {
  const [models, status, presets] = await Promise.all([api('/api/models'), api('/api/models/status'), api('/api/presets')]);
  S.models = models; S.presets = presets; S.status = status;
  const live = status.loaded ? status.model.filename : null;
  const box = $('#modelCards');
  if (!models.length) { box.innerHTML = `<div class="empty">${esc(t('no_models'))}</div>`; return; }
  box.innerHTML = models.map(m => {
    const isLive = m.filename === live;
    return `<div class="card ${isLive ? 'live' : ''}" data-file="${esc(m.filename)}">
      <div class="card-head"><h3>${esc(m.name)}</h3>
        ${m.quant ? `<span class="tag">${esc(m.quant)}</span>` : ''}<span class="tag">${fmtGB(m.size_bytes)}</span>
        ${m.vision ? `<span class="tag vision">${t('vision')}</span>` : ''}
        ${isLive ? `<span class="tag">${t('loaded')} · ${status.model.load_seconds}s</span><button class="ghost" data-act="unload">${t('unload')}</button>` : ''}
        <button class="${isLive ? 'ghost' : 'primary'}" data-act="open">${t('load')}…</button></div>
      <div class="panelbox" hidden></div></div>`;
  }).join('');
});
function openLoadPanel(card) {
  const box = $('.panelbox', card);
  if (!box.hidden) { box.hidden = true; return; }
  const file = card.dataset.file, cur = S.status.loaded && S.status.model.filename === file ? S.status.model : null;
  const preset = S.presets.find(p => p.model_filename === file) || S.presets[0];
  box.innerHTML = `<label class="fields"><span class="wide" style="grid-column:1/-1;display:flex;gap:8px;align-items:center">${t('preset')}
      <select name="preset" style="max-width:260px">${S.presets.map(p => `<option value="${p.id}" ${p.id === (cur?.preset_id || preset?.id) ? 'selected' : ''}>${esc(p.name)}</option>`).join('')}</select></span></label>
    <div class="fields" data-load>${loadFields(cur ? cur.params : preset?.load_params)}</div>
    <div class="est" data-est></div>
    <div class="btns"><label class="check" data-force hidden><input type="checkbox" name="force">${t('force')}</label><span class="grow"></span><button class="primary" data-act="go">${t('load')}</button></div>`;
  box.hidden = false;
  const fields = $('[data-load]', box), sel = $('[name=preset]', box);
  const fill = () => { const p = S.presets.find(x => x.id === sel.value); fields.innerHTML = loadFields(p?.load_params); estimate(card); };
  sel.onchange = fill;
  fields.oninput = () => { clearTimeout(box._t); box._t = setTimeout(() => estimate(card), 300); };
  estimate(card);
}
async function estimate(card) {
  const box = $('.panelbox', card), p = readLoad(box);
  try {
    const e = await api(`/api/models/estimate?filename=${encodeURIComponent(card.dataset.file)}&n_ctx=${p.n_ctx}&n_gpu_layers=${p.n_gpu_layers}`);
    const el = $('[data-est]', box); el.className = 'est' + (e.fits ? '' : ' bad');
    el.textContent = `${t('est')}: ${fmtGB(e.total_bytes)} ${t('of')} ${fmtGB(e.budget_bytes)} ${t('budget')}`;
    $('[data-force]', box).hidden = e.fits;
  } catch {}
}
const doLoad = guard(async card => {
  const box = $('.panelbox', card), btn = $('[data-act=go]', box);
  btn.disabled = true; btn.textContent = t('loading');
  try {
    await api('/api/models/load', { method: 'POST', body: { filename: card.dataset.file, preset_id: $('[name=preset]', box).value, overrides: readLoad(box), force: $('[name=force]', box).checked } });
    toast(t('switched')); await renderModels(); refreshMeter();
  } catch (e) { if (e.status === 409 && e.details) { $('[data-force]', box).hidden = false; } throw e; }
  finally { btn.disabled = false; btn.textContent = t('load'); }
});

// ---------- presets ----------
const BLANK_PRESET = { id: null, name: '', model_filename: null, load_params: {}, gen_params: {}, options: {} };
const renderPresets = guard(async () => {
  [S.presets, S.models] = await Promise.all([api('/api/presets'), api('/api/models')]);
  if (!S.editPreset) S.editPreset = S.presets[0] || BLANK_PRESET;
  $('#presetList').innerHTML = `<li data-new>+ ${t('new_preset')}</li>` + S.presets.map(p => `<li data-id="${p.id}" class="${p.id === S.editPreset.id ? 'on' : ''}">${esc(p.name)}</li>`).join('');
  const p = S.editPreset;
  $('#presetForm').innerHTML = `<label>${t('name')}<input type="text" name="name" value="${esc(p.name)}" required></label>
    <label style="display:block;margin-top:10px">${t('model')}<select name="model_filename"><option value="">${t('any_model')}</option>${S.models.map(m => `<option value="${esc(m.filename)}" ${m.filename === p.model_filename ? 'selected' : ''}>${esc(m.name)}</option>`).join('')}</select></label>
    <div class="fields" data-load>${loadFields(p.load_params)}</div><div class="fields" data-gen>${genFields(p.gen_params)}</div>
    <div class="fields"><label class="inline wide"><input type="checkbox" name="think_prefilled" ${p.options.think_prefilled ? 'checked' : ''}>${t('prefilled')}</label>
    <label class="wide">${t('offdir')}<input type="text" name="think_off_directive" value="${esc(p.options.think_off_directive || '')}"></label></div>
    <div class="btns"><button class="primary" type="submit">${t('save')}</button>${p.id ? `<button class="ghost danger" type="button" data-act="del">${t('delete')}</button>` : ''}</div>`;
});
const savePreset = guard(async form => {
  const body = { name: form.name.value, model_filename: form.model_filename.value || null, load_params: readLoad(form),
    gen_params: readGen(form), options: { think_prefilled: form.think_prefilled.checked, think_off_directive: form.think_off_directive.value } };
  const saved = S.editPreset.id ? await api('/api/presets/' + S.editPreset.id, { method: 'PUT', body }) : await api('/api/presets', { method: 'POST', body });
  S.editPreset = saved; toast(t('saved')); renderPresets();
});

// ---------- virtual APIs ----------
const BLANK_API = { slug: '', name: '', description: '', system_prompt: '', input_template: '', preset_id: null, model_filename: null, gen_params: {}, output_schema: null };
const renderApis = guard(async () => {
  [S.apis, S.presets, S.models] = await Promise.all([api('/api/virtual-apis'), api('/api/presets'), api('/api/models')]);
  const a = S.editApi || (S.editApi = S.apis[0] || BLANK_API), isNew = !S.apis.some(x => x.slug === a.slug);
  $('#apiList').innerHTML = `<li data-new>+ ${t('new_api')}</li>` + S.apis.map(x => `<li data-slug="${x.slug}" class="${x.slug === a.slug ? 'on' : ''}">${esc(x.name)}<br><small>/api/v/${esc(x.slug)}</small></li>`).join('');
  $('#apiForm').innerHTML = `<div class="fields"><label>${t('name')}<input type="text" name="name" value="${esc(a.name)}" required></label>
    <label>${t('slug')}<input type="text" name="slug" value="${esc(a.slug)}" ${isNew ? '' : 'readonly'} required pattern="[a-z0-9][a-z0-9\\-]{1,40}"></label>
    <label class="wide">${t('desc')}<input type="text" name="description" value="${esc(a.description)}"></label>
    <label class="wide">${t('sys_prompt')}<textarea name="system_prompt" rows="3">${esc(a.system_prompt)}</textarea></label>
    <label class="wide">${t('tmpl')}<textarea name="input_template" rows="2">${esc(a.input_template)}</textarea></label>
    <label>${t('preset')}<select name="preset_id"><option value="">—</option>${S.presets.map(p => `<option value="${p.id}" ${p.id === a.preset_id ? 'selected' : ''}>${esc(p.name)}</option>`).join('')}</select></label>
    <label>${t('pinned')}<select name="model_filename"><option value="">—</option>${S.models.map(m => `<option value="${esc(m.filename)}" ${m.filename === a.model_filename ? 'selected' : ''}>${esc(m.name)}</option>`).join('')}</select></label>
    <label>${t('temp')}<input type="number" step="0.05" name="temperature" value="${a.gen_params.temperature ?? ''}"></label>
    <label>${t('maxtok')}<input type="number" name="max_tokens" value="${a.gen_params.max_tokens ?? ''}"></label>
    <label class="wide">${t('schema')}<textarea name="output_schema" rows="4" style="font-family:var(--mono)">${a.output_schema ? esc(JSON.stringify(a.output_schema, null, 2)) : ''}</textarea></label></div>
    <div class="btns"><button class="primary" type="submit">${t('save')}</button>${isNew ? '' : `<button class="ghost danger" type="button" data-act="del">${t('delete')}</button>`}</div>`;
  const test = $('#apiTest'); test.hidden = isNew;
  if (!isNew) test.innerHTML = `<h3>${t('run')}</h3><label>${t('input')}<textarea id="tIn" rows="3"></textarea></label>
    <label style="display:block;margin-top:8px">${t('vars')}<textarea id="tVars" rows="2" style="font-family:var(--mono)">{}</textarea></label>
    <div class="btns"><button class="primary" data-act="run">${t('run')}</button></div><pre class="out" id="tOut" style="margin-top:10px">${esc(curl(a.slug))}</pre>`;
});
const curl = slug => `curl -X POST ${location.origin}/api/v/${slug} \\\n  -H "Content-Type: application/json" ${localStorage.gb_key ? '\\\n  -H "x-api-key: <key>" ' : ''}\\\n  -d '{"input": "..."}'`;
const saveApi = guard(async form => {
  let schema = null;
  if (form.output_schema.value.trim()) { try { schema = JSON.parse(form.output_schema.value); } catch { throw new Error('Output schema is not valid JSON'); } }
  const gen = {}; if (form.temperature.value) gen.temperature = +form.temperature.value; if (form.max_tokens.value) gen.max_tokens = +form.max_tokens.value;
  const body = { slug: form.slug.value, name: form.name.value, description: form.description.value, system_prompt: form.system_prompt.value,
    input_template: form.input_template.value, preset_id: form.preset_id.value || null, model_filename: form.model_filename.value || null, gen_params: gen, output_schema: schema };
  const exists = S.apis.some(x => x.slug === body.slug);
  S.editApi = await api(exists ? '/api/virtual-apis/' + body.slug : '/api/virtual-apis', { method: exists ? 'PUT' : 'POST', body });
  toast(t('saved')); renderApis();
});
const runApi = guard(async () => {
  const out = $('#tOut'); out.textContent = t('loading');
  let variables = {}; try { variables = JSON.parse($('#tVars').value || '{}'); } catch { throw new Error('Variables must be valid JSON'); }
  try { out.textContent = JSON.stringify(await api('/api/v/' + S.editApi.slug, { method: 'POST', body: { input: $('#tIn').value, variables } }), null, 2); }
  catch (e) { out.textContent = e.message; throw e; }
});

// ---------- wiring ----------
document.addEventListener('click', e => {
  const el = e.target.closest('button, li, [data-goto]'); if (!el) return;
  if (el.dataset.view) show(el.dataset.view);
  else if (el.dataset.goto) show(el.dataset.goto);
  else if (el.id === 'newChat') newChat();
  else if (el.id === 'langBtn') { S.lang = S.lang === 'en' ? 'ar' : 'en'; localStorage.gb_lang = S.lang; applyLang(); show($('.view.on').id.slice(5)); }
  else if (el.id === 'sendBtn') send(false);
  else if (el.id === 'stopBtn') S.streaming?.abort();
  else if (el.id === 'regen') send(true);
  else if (el.id === 'sumBtn') guard(async () => { if (!S.chatId) return; el.disabled = true; try { await api(`/api/chats/${S.chatId}/summarize`, { method: 'POST' }); await openChat(S.chatId); } finally { el.disabled = false; } })();
  else if (el.id === 'delBtn') { if (S.chatId && confirm(t('confirm_del'))) guard(async () => { await api('/api/chats/' + S.chatId, { method: 'DELETE' }); S.chatId = null; await loadChats(); })(); }
  else if (el.id === 'sysSave') guard(async () => { if (!S.chatId) await newChat(); await api('/api/chats/' + S.chatId, { method: 'PATCH', body: { system_prompt: $('#sysText').value } }); toast(t('saved')); })();
  else if (el.dataset.rm) { S.attachments.splice(+el.dataset.rm, 1); renderChips(); }
  else if (el.closest('#chats') && el.tagName === 'LI') openChat(el.dataset.id);
  else if (el.closest('#modelCards')) { const card = el.closest('.card'); if (el.dataset.act === 'open') openLoadPanel(card); else if (el.dataset.act === 'go') doLoad(card); else if (el.dataset.act === 'unload') guard(async () => { await api('/api/models/unload', { method: 'POST' }); toast(t('unloaded')); await renderModels(); refreshMeter(); })(); }
  else if (el.closest('#presetList') && el.tagName === 'LI') { S.editPreset = el.dataset.new !== undefined ? { ...BLANK_PRESET } : S.presets.find(p => p.id === el.dataset.id); renderPresets(); }
  else if (el.closest('#presetForm') && el.dataset.act === 'del') { if (confirm(t('confirm_del'))) guard(async () => { await api('/api/presets/' + S.editPreset.id, { method: 'DELETE' }); S.editPreset = null; toast(t('deleted')); renderPresets(); })(); }
  else if (el.closest('#apiList') && el.tagName === 'LI') { S.editApi = el.dataset.new !== undefined ? { ...BLANK_API } : S.apis.find(a => a.slug === el.dataset.slug); renderApis(); }
  else if (el.closest('#apiForm') && el.dataset.act === 'del') { if (confirm(t('confirm_del'))) guard(async () => { await api('/api/virtual-apis/' + S.editApi.slug, { method: 'DELETE' }); S.editApi = null; toast(t('deleted')); renderApis(); })(); }
  else if (el.dataset.act === 'run') runApi();
});
$('#presetForm').addEventListener('submit', e => { e.preventDefault(); savePreset(e.target); });
$('#apiForm').addEventListener('submit', e => { e.preventDefault(); saveApi(e.target); });
$('#exportSel').addEventListener('change', e => { if (e.target.value && S.chatId) guard(download)(e.target.value); e.target.value = ''; });
$('#file').addEventListener('change', e => { const f = e.target.files[0]; e.target.value = ''; if (f) guard(uploadFile)(f); });
$('#input').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(false); } });
$('#chatTitle').addEventListener('click', guard(async () => {
  if (!S.chatId) return; const n = prompt(t('name'), S.chat.title); if (!n) return;
  await api('/api/chats/' + S.chatId, { method: 'PATCH', body: { title: n } }); await loadChats(); await openChat(S.chatId);
}));

applyLang(); loadChats(); refreshMeter(); setInterval(refreshMeter, 4000);
