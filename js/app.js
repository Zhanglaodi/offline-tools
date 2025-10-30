// —— 数据层：默认示例，用户可增删改，存于 localStorage ——
const STORAGE_KEY = 'links-hub-v1';

/** @type {Array < { id: string, title: string, url: string, desc: string, tags: string[], kind: 'WEB' | 'LOCAL', online?: boolean, fav?: boolean } >} */
const DEFAULT_LINKS = [
    { id: crypto.randomUUID(), title: 'DBC 编写工具', url: './tools/dbc_editor/index.html', desc: '本地页面：修复跨行注释的 DBC 可视化。', tags: ['CAN', 'DBC', '前端'], kind: 'LOCAL', online: true },
    { id: crypto.randomUUID(), title: '进制转换工具', url: './tools/base_converter/index.html', desc: '进制之间互转', tags: ['进制', '工具'], kind: 'LOCAL', online: true },
    { id: crypto.randomUUID(), title: '波特率计算工具', url: './tools/baud_rate/index.html', desc: '波特率计算', tags: ['波特率', '调试'], kind: 'LOCAL', online: true },
    { id: crypto.randomUUID(), title: '创芯曲线工具', url: './tools/创芯科技/index.html', desc: '创新科技曲线工具,只支持csv文件', tags: ['曲线', '创芯', '工具'], kind: 'LOCAL', online: true },
    { id: crypto.randomUUID(), title: '周立功曲线工具', url: './tools/周立功/index.html', desc: '支持解析ASC文件', tags: ['曲线', '周立功', '工具'], kind: 'LOCAL', online: true },
    { id: crypto.randomUUID(), title: '串口工具-网页', url: './tools/serial/index.html', desc: '串口工具-仅供娱乐', tags: ['串口', '工具'], kind: 'LOCAL', online: true },
    { id: crypto.randomUUID(), title: '塞弗转向-计算轮距', url: './tools/塞弗转向-计算轮距/index.html', desc: '塞弗转向-计算轮距', tags: ['汽车', '工具'], kind: 'LOCAL', online: true },
    { id: crypto.randomUUID(), title: 'CRC-校验', url: './tools/CRC-校验/index.html', desc: '支持自定义多项式，支持多种CRC校验', tags: ['工具', 'CRC校验'], kind: 'LOCAL', online: true },
    { id: crypto.randomUUID(), title: 'BCC-校验', url: './tools/BCC校验/index.html', desc: '支持BCC校验', tags: ['工具', 'BCC校验'], kind: 'LOCAL', online: true },
    { id: crypto.randomUUID(), title: 'STM32 文档 (F4 HAL)', url: 'https://www.st.com/en/embedded-software/stm32cube-mcu-packages.html', desc: 'F4 HAL 参考与例程入口。', tags: ['STM32', 'HAL', '文档'], kind: 'WEB', online: true },
    { id: crypto.randomUUID(), title: 'asc曲线工具(独立运行版)', url: 'https://pan.baidu.com/s/5iUl1EJqsuVKNUqp-m0dtJg', desc: 'asc文件曲线工具', tags: ['zlg', '曲线', '汽车'], kind: 'WEB', online: true }
];

let state = {
    q: "",
    tag: null, // 当前选中标签
    links: loadLinks(),
    editing: null,
};

function loadLinks() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) { return DEFAULT_LINKS; }
        const parsed = JSON.parse(raw);
        // 合并与迁移
        return parsed.map(x => ({ ...x, kind: x.kind || (x.url?.startsWith('http') ? 'WEB' : 'LOCAL') }));
    } catch (e) { console.warn('load fail', e); return DEFAULT_LINKS; }
}
function save() { localStorage.setItem(STORAGE_KEY, JSON.stringify(state.links)); }

// —— 渲染工具 ——
const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));

function renderTags() {
    const box = $('#tags');
    const all = new Set();
    state.links.forEach(l => (l.tags || []).forEach(t => all.add(t)));
    const tags = ['全部', ...Array.from(all).sort((a, b) => a.localeCompare(b, 'zh'))];
    box.innerHTML = tags.map(t => `<button class="tag ${state.tag === t || (t === '全部' && !state.tag) ? 'active' : ''}" data-tag="${t}">${t}</button>`).join('');
    $$('#tags .tag').forEach(el => el.onclick = () => { state.tag = (el.dataset.tag === '全部') ? null : el.dataset.tag; render(); });
}

function matches(l) {
    const hitText = [l.title, l.desc, (l.tags || []).join(' ')].join(' ').toLowerCase();
    const okQ = !state.q || hitText.includes(state.q.toLowerCase());
    const okTag = !state.tag || (l.tags || []).includes(state.tag);
    return okQ && okTag;
}

function icon(kind) {
    return kind === 'WEB'
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18" /></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="6" width="18" height="12" rx="2" /><path d="M7 6v12M17 6v12" /></svg>'
}

function renderList() {
    const box = $('#list');
    const arr = state.links.filter(matches);
    $('#count').textContent = arr.length + ' / ' + state.links.length;
    if (arr.length === 0) { box.innerHTML = '<div class="muted" style="grid-column:1/-1;padding:24px">没有匹配的结果。</div>'; return; }
    box.innerHTML = arr.map(l => {
        const tagHtml = (l.tags || []).map(t => `<span class="badge">#${t}</span>`).join(' ');
        const ledClass = (l.online === false) ? 'off' : (l.online === true ? 'on' : '');
        const safeUrl = (l.url || '').replace(/"/g, '&quot;');
        return `
    <article class="card" data-id="${l.id}">
        <div class="row">
            <div class="led ${ledClass}" title="${l.online === false ? '标记为离线' : '标记为在线'}"></div>
            <div class="badge">${l.kind}</div>
            <button class="fav ${l.fav ? 'active' : ''}" title="收藏">★</button>
        </div>
        <h3 class="row" style="gap:8px; margin-top:6px">${icon(l.kind)} <span>${l.title}</span></h3>
        <p>${l.desc || ''}</p>
        <div class="row">${tagHtml}</div>
        <div class="actions">
            <a class="btn sm link" href="${safeUrl}" target="_blank" rel="noopener">打开链接 ↗</a>
            <button class="btn sm" data-act="copy">复制</button>
            <button class="btn sm" data-act="edit">编辑</button>
            <button class="btn sm" data-act="del" style="border-color:rgba(255,107,107,.45); color:${'var(--danger)'}">删除</button>
        </div>
    </article>`
    }).join('');

    // 绑定卡片按钮
    $$('#list .card').forEach(card => {
        const id = card.dataset.id;
        card.querySelector('.fav').onclick = () => { toggleFav(id); };
        card.querySelector('[data-act="copy"]').onclick = () => { copyUrl(id); };
        card.querySelector('[data-act="edit"]').onclick = () => { openModal(id); };
        card.querySelector('[data-act="del"]').onclick = () => { del(id); };
    });
}

function render() {
    renderTags(); renderList();
    // 放在 <script> 最后或 DOMContentLoaded 后执行
    (function showConsoleEasterEgg() {
        if (window.__ce_done__) return;  // 防重复
        window.__ce_done__ = true;

        // 用 collapsed 分组，避免占空间
        console.groupCollapsed('%c✨ Hi, Hacker! 欢迎探索~',
            'background:#111;color:#9ae6b4;padding:6px 10px;border-radius:6px;font-size:14px');
        console.log('%c项目: Web Serial 工具', 'color:#a0aec0');
        console.log('%c提示: 输入 help() 获取隐藏指令', 'color:#63b3ed');
        console.groupEnd();

        // 简单命令
        window.help = () => console.log('%c命令: pro(), about()', 'color:#f6ad55');
        window.pro = () => console.log('%c专业模式未开放，敬请期待~', 'color:#ed64a6');
        window.about = () => console.log('%cAuthor: xt  |  Build: ' + new Date().toLocaleString(), 'color:#cbd5e0');
        window.djb = () => {
            console.log('%c👉 点击这里: https://ncnm4gvv4snr.feishu.cn/drive/folder/P9ZSfBfs4lLhBIdmdyjcKR1gnng',
                'color:#48bb78;font-weight:bold;text-decoration:underline;');
        };
    })();
}

// —— 交互 ——
const q = $('#q');
q.addEventListener('input', () => { state.q = q.value.trim(); renderList(); });
window.addEventListener('keydown', (e) => { if (e.key === '/') { e.preventDefault(); q.focus(); } });

// 添加 / 编辑
const mask = $('#mask');
const fTitle = $('#f-title');
const fUrl = $('#f-url');
const fDesc = $('#f-desc');
const fTags = $('#f-tags');

$('#btn-add').onclick = () => openModal();
$('#btn-cancel').onclick = closeModal;
$('#btn-save').onclick = saveModal;

function openModal(id) {
    state.editing = id || null;
    $('#modal-title').textContent = id ? '编辑链接' : '添加链接';
    if (id) {
        const l = state.links.find(x => x.id === id);
        fTitle.value = l.title || ''; fUrl.value = l.url || ''; fDesc.value = l.desc || ''; fTags.value = (l.tags || []).join(', ');
    } else {
        fTitle.value = ''; fUrl.value = ''; fDesc.value = ''; fTags.value = '';
    }
    mask.style.display = 'flex'; fTitle.focus();
}
function closeModal() { mask.style.display = 'none'; }

function normalizeKind(url) { return /^https?:\/\//i.test(url) ? 'WEB' : 'LOCAL'; }

function saveModal() {
    const title = fTitle.value.trim();
    const url = fUrl.value.trim();
    if (!title || !url) { alert('名称与 URL 必填'); return; }
    const item = {
        title,
        url,
        desc: fDesc.value.trim(),
        tags: fTags.value.split(',').map(s => s.trim()).filter(Boolean),
        kind: normalizeKind(url),
        online: true,
    };
    if (state.editing) {
        const i = state.links.findIndex(x => x.id === state.editing);
        state.links[i] = { ...state.links[i], ...item };
    } else {
        state.links.unshift({ id: crypto.randomUUID(), ...item });
    }
    save(); closeModal(); render();
}

function copyUrl(id) {
    const l = state.links.find(x => x.id === id); if (!l) return;
    navigator.clipboard?.writeText(l.url).then(() => {
        toast('已复制链接：' + l.url);
    });
}
function del(id) {
    if (!confirm('确定删除该链接？')) return;
    state.links = state.links.filter(x => x.id !== id); save(); render();
}
function toggleFav(id) {
    const i = state.links.findIndex(x => x.id === id);
    state.links[i].fav = !state.links[i].fav; save(); renderList();
}

// 导出/导入
$('#btn-export').onclick = () => {
    const payload = JSON.stringify(state.links, null, 2);
    const blob = new Blob([payload], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'links-hub.json'; a.click(); URL.revokeObjectURL(a.href);
};
$('#btn-import').onclick = async () => {
    const inp = document.createElement('input'); inp.type = 'file'; inp.accept = '.json,application/json';
    inp.onchange = async () => {
        const file = inp.files[0]; if (!file) return;
        const txt = await file.text();
        try {
            const arr = JSON.parse(txt);
            if (!Array.isArray(arr)) throw new Error('格式错误');
            // 简单清洗
            state.links = arr.map(x => ({ id: x.id || crypto.randomUUID(), title: x.title || '未命名', url: x.url || '', desc: x.desc || '', tags: x.tags || [], kind: x.kind || (x.url?.startsWith('http') ? 'WEB' : 'LOCAL'), fav: !!x.fav, online: x.online }));
            save(); render();
        } catch (e) { alert('导入失败：' + e.message); }
    };
    inp.click();
};

// 轻量提示
function toast(msg) {
    const d = document.createElement('div');
    d.textContent = msg; d.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#0f1710;border:1px solid rgba(92,230,92,.45);padding:10px 14px;border-radius:12px;box-shadow:var(--shadow);z-index:30';
    document.body.appendChild(d); setTimeout(() => d.remove(), 1800);
}

// 作者信息弹窗功能
function initAuthorNotification() {
  const notification = document.getElementById('author-notification');
  const closeBtn = document.getElementById('close-author');
  
  // 页面加载后延迟显示
  setTimeout(() => {
    notification.classList.add('show');
  }, 1000);
  
  // 关闭按钮事件
  closeBtn.addEventListener('click', () => {
    notification.classList.remove('show');
  });
  
  // 5秒后自动关闭
  setTimeout(() => {
    notification.classList.remove('show');
  }, 8000);
  
  // 点击弹窗外部区域关闭（可选）
  notification.addEventListener('click', (e) => {
    if (e.target === notification) {
      notification.classList.remove('show');
    }
  });
}

// 在页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  // ...existing code...
  initAuthorNotification();
});

// 初始渲染
render();