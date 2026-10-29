// 司法院裁判書系統批次核對：在內建瀏覽器開 https://judgment.judicial.gov.tw/FJUD/default.aspx ，
// 同一分頁用 javascript_exec 執行。Python 直接下載會被 bot-defense 擋（2026-10-28 實測）。
//
// 用法：把 tests 換成「id: [要核對的原文片段]」。
// - id 格式：法院代碼,民國年度,字別,號次,西元裁判日期,序號；舊裁判可能沒有序號。TLR 的 doc_id 可以直接用。
// - 片段可直接貼 TLR 摘錄：空白、換行、⟪法院見解⟫ 這類標記與 <em> 會自動去掉。標點照原文，不要改全半形。
// 結果：
// - title 是官方裁判名稱，含「民事」或「刑事」。「系統訊息」或空白代表 id 錯誤，不能引用。
// - ✓ 代表原文有這段；✗ 會附官方同位置的原文，方便看差在哪裡。
const tests = {
  'PCDV,114,聲,354,20260122,2': ['100萬元以上未滿1,000萬元者，2,000元'],
};
const SHOW = '';   // 想看某段前後文時填關鍵字，例如 '本院之判斷'；不需要就留空

const norm = s => s.replace(/⟪[^⟫]*⟫|<\/?em>/g, '').replace(/\s+/g, '');
const hit = (txt, raw) => {
  const k = norm(raw);
  if (txt.includes(k)) return '✓ ' + k;
  const p = k.slice(0, 6), i = txt.indexOf(p);
  return '✗ ' + k + (i < 0 ? '（前 6 字也沒有）' : '｜官方：' + txt.slice(i, i + k.length + 20));
};
const out = {};
for (const [id, kws] of Object.entries(tests)) {
  try {
    const html = await (await fetch('/FJUD/data.aspx?ty=JD&id=' + encodeURIComponent(id))).text();
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const box = doc.querySelector('.htmlcontent');   // 新版頁面的正文區；舊裁判是空的，改讀整頁
    const txt = ((box && box.innerText.trim()) ? box.innerText : doc.body.innerText).replace(/\s+/g, '');
    const title = doc.title.trim();
    const r = { title, hits: kws.map(k => hit(txt, k)) };
    if (!title || /系統訊息/.test(title)) r.warn = 'id 錯誤或查無此案，不能引用';
    if (SHOW) {
      const i = txt.indexOf(norm(SHOW));
      r.show = i < 0 ? SHOW + '：未出現' : txt.slice(i, i + 300);
    }
    out[id] = r;
  } catch (e) {
    out[id] = '錯誤：' + e;
  }
}
out
