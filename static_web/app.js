/*
  XT · 导航 前端逻辑
  功能: 读取 JSON→渲染分组/卡片；搜索/筛选/排序；置顶收藏；导入导出；主题切换；代码高对比高亮
  项目发起: di di
  共同开发: ChatGPT (OpenAI)
  日期: 2025-08-13
  许可: MIT License

  【代码高亮说明（简易）】
  - 深色主题: 关键字 #569CD6、注释 #6A9955、类型/宏 #C586C0、数字 #B5CEA8
  - 浅色主题: 关键字 #0000FF、注释 #008000、类型/宏 #B000B0、数字 #1C00CF
*/

(function(){
  'use strict';

  // ---------- DOM ----------
  const root = document.documentElement;
  const app = document.getElementById('app');
  const inpQ = document.getElementById('q');
  const selFilter = document.getElementById('filter');
  const selSort = document.getElementById('sort');
  const btnTheme = document.getElementById('btn-theme');
  const btnImport = document.getElementById('btn-import');
  const btnExport = document.getElementById('btn-export');
  const btnClearPin = document.getElementById('btn-clearpin');
  const dataSrc = document.getElementById('data-src');

  // ---------- State ----------
  let DATA = { groups: [] };
  const PIN_KEY = 'xt-nav-pins';
  const THEME_KEY = 'xt-nav-theme';
  let pins = new Set(JSON.parse(localStorage.getItem(PIN_KEY)||'[]'));

  // ---------- Utils ----------
  const byQS = (q) => (t) => t.title.toLowerCase().includes(q) ||
                            (t.desc||'').toLowerCase().includes(q) ||
                            (t.tags||[]).some(x=>x.toLowerCase().includes(q));

  function getTheme(){
    return localStorage.getItem(THEME_KEY) || 'light';
  }
  function setTheme(t){
    root.setAttribute('data-theme', t);
    localStorage.setItem(THEME_KEY, t);
  }

  // 简易高亮（对比度加强）
  function highlight(code, lang){
    const esc = s=>s.replace(/[&<>]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
    let t = esc(code);
    const isLight = root.getAttribute('data-theme') === 'light';
    const KW = getComputedStyle(root).getPropertyValue('--kw').trim();
    const CM = getComputedStyle(root).getPropertyValue('--cm').trim();
    const TY = getComputedStyle(root).getPropertyValue('--ty').trim();
    const NU = getComputedStyle(root).getPropertyValue('--nu').trim();

    if (lang === 'c' || lang === 'cpp' || lang === 'h') {
      t = t.replace(/\b(#define|#include|typedef|struct|enum|union)\b/g, `<b style="color:${TY}">$1</b>`);
      t = t.replace(/\b(int|void|char|float|double|static|const|volatile|return|if|else|for|while|switch|case|break|continue)\b/g, `<b style="color:${KW}">$1</b>`);
      t = t.replace(/\/\*([\s\S]*?)\*\//g, `<i style="color:${CM}">/*$1*/</i>`);
      t = t.replace(/\/\/.*/g, m=>`<i style="color:${CM}">${m}</i>`);
      t = t.replace(/\b(\d+)([uUlLfF]?)/g, `<span style="color:${NU}">$1$2</span>`);
    } else if (lang === 'js' || lang === 'ts') {
      t = t.replace(/\b(const|let|var|function|return|if|else|for|while|switch|case|break|continue|class|new|import|export|from|try|catch|finally)\b/g, `<b style="color:${KW}">$1</b>`);
      t = t.replace(/\/\*([\s\S]*?)\*\//g, `<i style="color:${CM}">/*$1*/</i>`);
      t = t.replace(/\/\/.*/g, m=>`<i style="color:${CM}">${m}</i>`);
      t = t.replace(/\b(\d+)([uUlLfF]?)/g, `<span style="color:${NU}">$1$2</span>`);
    }
    return t;
  }

  // ---------- Render ----------
  function render(){
    app.innerHTML = '';
    const q = (inpQ.value||'').trim().toLowerCase();
    const tag = selFilter.value;

    const groups = DATA.groups || [];
    const allTags = new Set();
    groups.forEach(g => (g.items||[]).forEach(i => (i.tags||[]).forEach(t => allTags.add(t))));

    // fill filter options once
    if (selFilter.options.length <= 1) {
      [...allTags].sort().forEach(t=>{
        const opt = document.createElement('option'); opt.value=t; opt.textContent=t;
        selFilter.appendChild(opt);
      });
    }

    // sort strategy
    const sortKey = selSort.value; // 'pin,name' | 'pin,group' | 'group,name'
    const byName = (a,b)=> a.title.localeCompare(b.title, 'zh-Hans-CN');
    const byGroup = (a,b)=> (a._g || '').localeCompare(b._g || '', 'zh-Hans-CN');
    const byPin = (a,b)=> (pins.has(b._id) - pins.has(a._id));

    // flatten for sorting, but render grouped
    let flat = [];
    groups.forEach((g,gi)=>{
      (g.items||[]).forEach((it,ii)=>{
        const item = Object.assign({}, it);
        item._g = g.name || '';
        item._id = `${gi}:${ii}`; // stable id
        flat.push(item);
      });
    });

    // filter
    if (q) flat = flat.filter(byQS(q));
    if (tag) flat = flat.filter(x=> (x.tags||[]).includes(tag));

    // sort
    const cmp = {
      'pin,name': (a,b)=> byPin(a,b) || byName(a,b),
      'pin,group':(a,b)=> byPin(a,b) || byGroup(a,b) || byName(a,b),
      'group,name':(a,b)=> byGroup(a,b) || byName(a,b),
    }[sortKey] || ((a,b)=>0);
    flat.sort(cmp);

    // regroup
    const map = new Map();
    flat.forEach(it=>{
      if (!map.has(it._g)) map.set(it._g, []);
      map.get(it._g).push(it);
    });

    // render groups
    for (const [gname, items] of map.entries()) {
      const sec = document.createElement('section');
      sec.className = 'group';
      sec.innerHTML = `<h2>${gname||'未命名分组'}</h2><div class="grid"></div>`;
      const grid = sec.querySelector('.grid');

      items.forEach(it=>{
        const div = document.createElement('div');
        div.className = 'item';
        const pinned = pins.has(it._id);
        const pin = document.createElement('span');
        pin.className = 'pin';
        pin.title = pinned? '取消置顶':'置顶';
        pin.textContent = pinned? '📌':'📍';
        pin.addEventListener('click', ()=>{
          if (pins.has(it._id)) pins.delete(it._id); else pins.add(it._id);
          localStorage.setItem(PIN_KEY, JSON.stringify([...pins]));
          render();
        });
        div.appendChild(pin);

        const title = document.createElement('div');
        title.className = 'title';
        title.textContent = it.title || '(未命名)';
        div.appendChild(title);

        const desc = document.createElement('div');
        desc.className = 'desc';
        desc.textContent = it.desc || '';
        div.appendChild(desc);

        if (it.type === 'link') {
          const a = document.createElement('a');
          a.className = 'btn';
          a.href = it.url || '#';
          a.target = '_blank';
          a.rel = 'noopener';
          a.textContent = '打开链接';
          div.appendChild(a);
        } else if (it.type === 'code') {
          const pre = document.createElement('pre');
          const code = document.createElement('code');
          code.innerHTML = highlight(it.code||'', (it.lang||'').toLowerCase());
          pre.appendChild(code);

          // 复制按钮
          const copy = document.createElement('a');
          copy.href='#'; copy.className='btn'; copy.style.marginTop='8px'; copy.textContent='复制';
          copy.addEventListener('click', (e)=>{
            e.preventDefault();
            navigator.clipboard.writeText(it.code||'').then(()=>{
              copy.textContent='已复制';
              setTimeout(()=>copy.textContent='复制', 1200);
            });
          });

          div.appendChild(pre);
          div.appendChild(copy);
        }

        // tags
        if ((it.tags||[]).length){
          const tags = document.createElement('div');
          tags.className = 'tags';
          it.tags.forEach(t=>{
            const span = document.createElement('span');
            span.className = 'tag';
            span.textContent = t;
            tags.appendChild(span);
          });
          div.appendChild(tags);
        }

        grid.appendChild(div);
      });

      app.appendChild(sec);
    }
  }

  // ---------- IO ----------
  async function loadData(){
    // 1) URL ?data=  (支持 base64 或 URI 编码 JSON)
    const p = new URLSearchParams(location.search);
    if (p.has('data')) {
      try{
        const raw = p.get('data');
        let txt = raw;
        // base64?
        if (/^[A-Za-z0-9+/=]+$/.test(raw)) {
          txt = atob(raw);
        } else {
          txt = decodeURIComponent(raw);
        }
        DATA = JSON.parse(txt);
        dataSrc.textContent = '数据来源：URL 参数';
        return;
      }catch(e){ console.warn('URL data parse error',e); }
    }
    // 2) 同目录 data.json
    try{
      const r = await fetch('data.json', {cache:'no-store'});
      if (r.ok) {
        DATA = await r.json();
        dataSrc.textContent = '数据来源：data.json';
        return;
      }
    }catch(e){ /* 本地 file:// 可能被拦截 */ }
    // 3) 内置 JSON
    try{
      const txt = document.getElementById('nav-data').textContent;
      DATA = JSON.parse(txt);
      dataSrc.textContent = '数据来源：内置 JSON';
    }catch(e){
      DATA = {groups:[]};
      dataSrc.textContent = '数据来源：空';
    }
  }

  // 导入/导出
  function exportJSON(){
    const blob = new Blob([JSON.stringify(DATA,null,2)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'nav-data.json';
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }
  function importJSON(){
    const inp = document.createElement('input');
    inp.type='file'; inp.accept='application/json';
    inp.onchange = async () => {
      const f = inp.files[0]; if (!f) return;
      const txt = await f.text();
      try{
        DATA = JSON.parse(txt);
        render();
        dataSrc.textContent = `数据来源：手动导入（${f.name}）`;
      }catch(e){ alert('JSON 解析失败：'+e.message); }
    };
    inp.click();
  }

  // ---------- Events ----------
  inpQ.addEventListener('input', render);
  selFilter.addEventListener('change', render);
  selSort.addEventListener('change', render);
  btnImport.addEventListener('click', importJSON);
  btnExport.addEventListener('click', exportJSON);
  btnClearPin.addEventListener('click', ()=>{ pins.clear(); localStorage.setItem(PIN_KEY,'[]'); render(); });
  btnTheme.addEventListener('click', ()=>{
    setTheme(getTheme()==='light'?'dark':'light');
    render(); // 让高亮颜色跟着主题刷新
  });

  // 快捷键 Ctrl+/
  window.addEventListener('keydown', (e)=>{
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
      e.preventDefault(); inpQ.focus();
    }
  });

  // ---------- Init ----------
  setTheme(getTheme());
  loadData().then(render);
})();
