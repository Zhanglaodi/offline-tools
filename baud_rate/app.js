/*
  CAN Bitrate Calculator 前端逻辑
  功能: 波特率计算 / 搜索 / CSV 导出
  项目发起: zxt
  共同开发: ChatGPT (OpenAI)
  日期: 2025-08-13
  许可: MIT License
*/
(function(){
  'use strict';

  // ---------- DOM ----------
  const $ = (sel) => document.querySelector(sel);
  const modeSel = $('#mode');
  const clkInp = $('#clk');
  const pills = Array.from(document.querySelectorAll('.pill'));

  const rowGen = $('#row-generic');
  const rowBx  = $('#row-bxcan');

  // generic inputs
  const divG = $('#div'), tprop = $('#tprop'), tseg1 = $('#tseg1'), tseg2 = $('#tseg2'), sjw = $('#sjw');

  // bxCAN inputs
  const divB = $('#div_bx'), bs1 = $('#bs1'), bs2 = $('#bs2'), sjwB = $('#sjw_bx');

  // calc output
  const btnCalc = $('#btn-calc'), calcErr = $('#calc-error');
  const outTqNs = $('#tq_ns'), outTqTotal = $('#tq_total'), outBr = $('#bitrate'), outSp = $('#sample');

  // search
  const targetBr = $('#target_br'), targetSp = $('#target_sp'), topk = $('#topk');
  const sg = {
    div_lo: $('#g_div_lo'), div_hi: $('#g_div_hi'),
    prop_lo: $('#g_prop_lo'), prop_hi: $('#g_prop_hi'),
    seg1_lo: $('#g_seg1_lo'), seg1_hi: $('#g_seg1_hi'),
    seg2_lo: $('#g_seg2_lo'), seg2_hi: $('#g_seg2_hi'),
    sjw_lo:  $('#g_sjw_lo'),  sjw_hi:  $('#g_sjw_hi'),
  };
  const sb = {
    div_lo: $('#b_div_lo'), div_hi: $('#b_div_hi'),
    bs1_lo: $('#b_bs1_lo'), bs1_hi: $('#b_bs1_hi'),
    bs2_lo: $('#b_bs2_lo'), bs2_hi: $('#b_bs2_hi'),
    sjw_lo: $('#b_sjw_lo'), sjw_hi: $('#b_sjw_hi'),
  };
  const btnSearch = $('#btn-search'), btnExport = $('#btn-export'), searchErr = $('#search-error');
  const theadRow = $('#thead-row'), tbody = $('#tbody');

  // ---------- Helpers ----------
  const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);
  const isBx = () => modeSel.value === 'bxcan';
  const fmt = (v, digits=3) => {
    if (!isFinite(v)) return '—';
    const p = Math.pow(10, digits);
    return String(Math.round(v*p)/p);
  };
  const ppm = (a, b) => (b <= 0) ? Infinity : Math.abs(a - b) / b * 1e6;

  // ---------- Calculation core ----------
  function validateGeneric(div, tprop, tseg1, tseg2, sjw){
    if (div < 1 || div > 1024) return 'DIV 超出 [1..1024]';
    if (tprop < 0 || tprop > 8) return 'Tprop 超出 [0..8]';
    if (tseg1 < 1 || tseg1 > 16) return 'Tseg1 超出 [1..16]';
    if (tseg2 < 1 || tseg2 > 8) return 'Tseg2 超出 [1..8]';
    if (sjw < 1 || sjw > 4) return 'SJW 超出 [1..4]';
    if (tseg2 < sjw) return '要求 Tseg2 >= SJW';
    return '';
  }
  function validateBx(div, bs1, bs2, sjw){
    if (div < 1 || div > 1024) return 'DIV 超出 [1..1024]';
    if (bs1 < 1 || bs1 > 16) return 'BS1 超出 [1..16]';
    if (bs2 < 1 || bs2 > 8) return 'BS2 超出 [1..8]';
    if (sjw < 1 || sjw > 4) return 'SJW 超出 [1..4]';
    if (bs2 < sjw) return '要求 BS2 >= SJW';
    return '';
  }

  function calcGeneric(clk, div, tprop, tseg1, tseg2){
    const tq_sum = 1 + tprop + tseg1 + tseg2;
    const tq_s = div / clk;
    const tq_ns = tq_s * 1e9;
    const bitrate = clk / (div * tq_sum);
    const sample = (1 + tprop + tseg1) / tq_sum;
    return {tq_ns, tq_sum, bitrate, sample};
    // 备注：SyncSeg 固定为 1 TQ
  }
  function calcBx(clk, div, bs1, bs2){
    const tq_sum = 1 + bs1 + bs2;
    const tq_s = div / clk;
    const tq_ns = tq_s * 1e9;
    const bitrate = clk / (div * tq_sum);
    const sample = (1 + bs1) / tq_sum;
    return {tq_ns, tq_sum, bitrate, sample};
  }

  // ---------- UI switches ----------
  function updateModeUI(){
    const bx = isBx();
    rowGen.classList.toggle('hidden', bx);
    rowBx.classList.toggle('hidden', !bx);

    // 搜索区域
    $('#srch-generic').classList.toggle('hidden', bx);
    $('#srch-bxcan').classList.toggle('hidden', !bx);

    // 更新表头
    renderTableHeader();
  }

  // ---------- Renderers ----------
  function renderCalcResult(obj){
    outTqNs.textContent   = fmt(obj.tq_ns, 3);
    outTqTotal.textContent= String(obj.tq_sum);
    outBr.textContent     = fmt(obj.bitrate, 3);
    outSp.textContent     = fmt(obj.sample*100.0, 3);
  }

  function renderTableHeader(){
    const bx = isBx();
    theadRow.innerHTML = '';
    const cols = bx
      ? ['DIV','BS1','BS2','SJW','Bitrate(bps)','SP(%)','BR误差(ppm)']
      : ['DIV','Tprop','Tseg1','Tseg2','SJW','Bitrate(bps)','SP(%)','BR误差(ppm)'];
    cols.forEach(c=>{
      const th = document.createElement('th'); th.textContent = c; theadRow.appendChild(th);
    });
  }

  function renderRows(rows){
    tbody.innerHTML = '';
    const bx = isBx();
    const frag = document.createDocumentFragment();
    rows.forEach(r=>{
      const tr = document.createElement('tr');
      const cells = bx
        ? [r.div, r.bs1, r.bs2, r.sjw, fmt(r.br,3), fmt(r.sp*100,3), fmt(r.err_ppm,3)]
        : [r.div, r.tprop, r.tseg1, r.tseg2, r.sjw, fmt(r.br,3), fmt(r.sp*100,3), fmt(r.err_ppm,3)];
      cells.forEach(val=>{
        const td = document.createElement('td'); td.textContent = val; tr.appendChild(td);
      });
      frag.appendChild(tr);
    });
    tbody.appendChild(frag);
  }

  // ---------- CSV ----------
  function toCSV(rows){
    const bx = isBx();
    const header = bx
      ? ['DIV','BS1','BS2','SJW','Bitrate(bps)','SP(%)','BR_err_ppm']
      : ['DIV','Tprop','Tseg1','Tseg2','SJW','Bitrate(bps)','SP(%)','BR_err_ppm'];
    const lines = [header.join(',')];
    rows.forEach(r=>{
      const arr = bx
        ? [r.div,r.bs1,r.bs2,r.sjw,fmt(r.br,6),fmt(r.sp*100,6),fmt(r.err_ppm,3)]
        : [r.div,r.tprop,r.tseg1,r.tseg2,r.sjw,fmt(r.br,6),fmt(r.sp*100,6),fmt(r.err_ppm,3)];
      lines.push(arr.join(','));
    });
    return lines.join('\n');
  }

  function downloadCSV(rows){
    const csv = toCSV(rows);
    const blob = new Blob([csv], {type:'text/csv;charset=utf-8;'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const ts = new Date().toISOString().replace(/[:.]/g,'-');
    a.href = url;
    a.download = `can_bitrate_${isBx()?'bxcan':'generic'}_${ts}.csv`;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    a.remove();
  }

  // ---------- Events ----------
  modeSel.addEventListener('change', updateModeUI);
  pills.forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const v = Number(btn.getAttribute('data-preset')||'0');
      if (v>0) clkInp.value = String(v);
    });
  });

  btnCalc.addEventListener('click', ()=>{
    calcErr.textContent = '';
    try{
      const clk = Number(clkInp.value||'0');
      if (!isFinite(clk) || clk<=0) throw new Error('时钟必须为正数');
      let res;
      if (isBx()){
        const div = Number(divB.value), b1=Number(bs1.value), b2=Number(bs2.value), sw=Number(sjwB.value);
        const why = validateBx(div,b1,b2,sw); if (why) throw new Error(why);
        res = calcBx(clk, div, b1, b2);
      }else{
        const div = Number(divG.value), p=Number(tprop.value), s1=Number(tseg1.value), s2=Number(tseg2.value), sw=Number(sjw.value);
        const why = validateGeneric(div,p,s1,s2,sw); if (why) throw new Error(why);
        res = calcGeneric(clk, div, p, s1, s2);
      }
      renderCalcResult(res);
    }catch(e){
      calcErr.textContent = e.message || String(e);
    }
  });

  const MAX_COMBINATIONS = 1_200_000; // 防卡浏览器：最大穷举组合阈值
  let lastRows = [];

  btnSearch.addEventListener('click', ()=>{
    searchErr.textContent = '';
    btnExport.disabled = true;
    tbody.innerHTML = '';
    try{
      const clk = Number(clkInp.value||'0');
      if (!isFinite(clk) || clk<=0) throw new Error('时钟必须为正数');

      const target = Number(targetBr.value||'0');
      if (!isFinite(target) || target<=0) throw new Error('目标 Bitrate 必须为正数');

      const spStr = (targetSp.value||'').trim();
      const spWant = spStr === '' ? null : Number(spStr);
      if (spWant!=null && !(spWant>=0 && spWant<=1)) throw new Error('采样点需在 0..1 之间或留空');

      const K = clamp(Number(topk.value||'0'), 1, 500);

      const rows = [];
      let combos = 0;

      if (isBx()){
        const r = {
          div_lo: Number(sb.div_lo.value), div_hi: Number(sb.div_hi.value),
          bs1_lo: Number(sb.bs1_lo.value), bs1_hi: Number(sb.bs1_hi.value),
          bs2_lo: Number(sb.bs2_lo.value), bs2_hi: Number(sb.bs2_hi.value),
          sjw_lo: Number(sb.sjw_lo.value), sjw_hi: Number(sb.sjw_hi.value),
        };
        // 组合数量估算
        combos = (r.div_hi-r.div_lo+1)*(r.bs1_hi-r.bs1_lo+1)*(r.bs2_hi-r.bs2_lo+1)*(r.sjw_hi-r.sjw_lo+1);
        if (combos>MAX_COMBINATIONS) throw new Error(`组合过大：${combos.toLocaleString()}，请缩小范围（当前阈值 ${MAX_COMBINATIONS.toLocaleString()}）`);

        for (let div=r.div_lo; div<=r.div_hi; ++div){
          for (let b1=r.bs1_lo; b1<=r.bs1_hi; ++b1){
            for (let b2=r.bs2_lo; b2<=r.bs2_hi; ++b2){
              for (let sw=r.sjw_lo; sw<=r.sjw_hi; ++sw){
                if (b2 < sw) continue;
                const out = calcBx(clk, div, b1, b2);
                const err = ppm(out.bitrate, target);
                const sperr = spWant==null ? 0 : Math.abs(out.sample - spWant);
                rows.push({div, bs1:b1, bs2:b2, sjw:sw, br:out.bitrate, sp:out.sample, err_ppm:err, sp_err:sperr});
              }
            }
          }
        }
        rows.sort((a,b)=> (a.err_ppm!==b.err_ppm)? (a.err_ppm-b.err_ppm) : (a.sp_err-b.sp_err));
      }else{
        const r = {
          div_lo: Number(sg.div_lo.value), div_hi: Number(sg.div_hi.value),
          prop_lo: Number(sg.prop_lo.value), prop_hi: Number(sg.prop_hi.value),
          seg1_lo: Number(sg.seg1_lo.value), seg1_hi: Number(sg.seg1_hi.value),
          seg2_lo: Number(sg.seg2_lo.value), seg2_hi: Number(sg.seg2_hi.value),
          sjw_lo:  Number(sg.sjw_lo.value),  sjw_hi:  Number(sg.sjw_hi.value),
        };
        combos = (r.div_hi-r.div_lo+1)*(r.prop_hi-r.prop_lo+1)*(r.seg1_hi-r.seg1_lo+1)*(r.seg2_hi-r.seg2_lo+1)*(r.sjw_hi-r.sjw_lo+1);
        if (combos>MAX_COMBINATIONS) throw new Error(`组合过大：${combos.toLocaleString()}，请缩小范围（当前阈值 ${MAX_COMBINATIONS.toLocaleString()}）`);

        for (let div=r.div_lo; div<=r.div_hi; ++div){
          for (let p=r.prop_lo; p<=r.prop_hi; ++p){
            for (let s1=r.seg1_lo; s1<=r.seg1_hi; ++s1){
              for (let s2=r.seg2_lo; s2<=r.seg2_hi; ++s2){
                for (let sw=r.sjw_lo; sw<=r.sjw_hi; ++sw){
                  if (s2 < sw) continue;
                  const out = calcGeneric(clk, div, p, s1, s2);
                  const err = ppm(out.bitrate, target);
                  const sperr = spWant==null ? 0 : Math.abs(out.sample - spWant);
                  rows.push({div, tprop:p, tseg1:s1, tseg2:s2, sjw:sw, br:out.bitrate, sp:out.sample, err_ppm:err, sp_err:sperr});
                }
              }
            }
          }
        }
        rows.sort((a,b)=> (a.err_ppm!==b.err_ppm)? (a.err_ppm-b.err_ppm) : (a.sp_err-b.sp_err));
      }

      const topRows = rows.slice(0, K);
      renderRows(topRows);
      lastRows = topRows;
      btnExport.disabled = lastRows.length === 0;
    }catch(e){
      searchErr.textContent = e.message || String(e);
    }
  });

  btnExport.addEventListener('click', ()=>{
    if (lastRows && lastRows.length>0) downloadCSV(lastRows);
  });

  // ---------- init ----------
  updateModeUI();
  renderTableHeader();
})();
