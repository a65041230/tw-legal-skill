"""把整部法規抓成本地快照（laws/<目錄>/articles.md），用來全文搜尋「哪一條提到某件事」。

用法（一律用 python -I 執行）：
  python -I law_snapshot.py                      # 更新預設的 12 部法規
  python -I law_snapshot.py B0000001 J0080001    # 只更新指定的法規代碼

快照只用來找條號。引用條文一律用 law_fetch.py 抓官方原文：快照不會隨修法自動更新。
做法參考 tern/taiwan-claude-legal（Apache-2.0）的 laws/ 快照；這版保留項、款分行，
只用標準函式庫，並驗證 HTTPS 憑證。
"""
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import law_fetch  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "laws")
# 前 5 部的目錄名稱沿用 taiwan-claude-legal；後 7 部是本 skill 常用的程序法與特別法
LAWS = {
    "B0000001": "civil-code", "J0080001": "company-act", "N0030001": "labor-standards-act",
    "I0050021": "pdpa", "J0070017": "copyright-act",
    "B0010001": "civil-procedure", "B0010004": "compulsory-enforcement", "B0010008": "non-contentious",
    "G0380028": "negotiable-instruments", "C0000001": "criminal-code", "C0010001": "criminal-procedure",
    "J0170001": "consumer-protection",
}
MARK = re.compile(r'<div class="h3[^"]*">|<div class="row">')
LINE = re.compile(r'<div class="(line-\d+|text-pre)[^"]*">(.*?)</div>', re.S)


def parse(page):
    """依網頁順序回傳 [("章", 標題) 或 ("條", 條號, [各行])]；項一行一行，款以全形空白縮排。"""
    body = page[page.find('class="law-reg-content"'):]
    marks = [m.start() for m in MARK.finditer(body)] + [len(body)]
    items = []
    for a, b in zip(marks, marks[1:]):
        seg = body[a:b]
        if seg.startswith('<div class="h3'):
            items.append(("章", law_fetch.plain(seg[seg.find(">") + 1:seg.find("</div>")])))
            continue
        no = re.search(r'<div class="col-no">(.*?)</div>', seg, re.S)
        if not no:
            continue
        lines = []
        for cls, txt in LINE.findall(seg):
            if cls == "text-pre":
                lines.append(law_fetch.html.unescape(re.sub(r"<[^>]+>", "", txt)).rstrip())
            else:
                lines.append("　" * (int(cls[5:]) // 4) + law_fetch.plain(txt))
        items.append(("條", law_fetch.plain(no.group(1)), lines))
    return items


def snapshot(pcode, folder):
    page = law_fetch.get(f"{law_fetch.BASE}/LawClass/LawAll.aspx?pcode={pcode}")
    head = law_fetch.law_header(pcode)
    items = parse(page)
    n = sum(1 for i in items if i[0] == "條")
    official = len(re.findall(r'<div class="col-no">', page))
    if n == 0 or n != official:
        raise RuntimeError(f"{pcode} 解析條數 {n} 和網頁條數 {official} 不同，不寫入")
    out = [f"# {head['law']}", "",
           f"- 法規代碼：{pcode}",
           f"- {head['date_label']}：{head['date']}",
           f"- 快照日期：{datetime.date.today().isoformat()}（共 {n} 條）",
           f"- 官方全文：{law_fetch.BASE}/LawClass/LawAll.aspx?pcode={pcode}",
           "- 用途：找條號。每一行是一項，全形空白縮排的是款。引用前用 law_fetch.py 抓官方原文。", ""]
    for it in items:
        if it[0] == "章":
            out += [f"## {it[1]}", ""]
        else:
            out += [f"### {it[1]}"] + it[2] + [""]
    path = os.path.join(ROOT, folder, "articles.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    return head, n


def write_index():
    rows = []
    for folder in sorted(os.listdir(ROOT)):
        path = os.path.join(ROOT, folder, "articles.md")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                head = [next(f).strip() for _ in range(6)]
            meta = dict(re.match(r"- (.+?)：(.+)", h).groups() for h in head[2:6])
            date_key = next(k for k in meta if k.endswith("日期") and k != "快照日期")
            rows.append(f"| {head[0][2:]} | {meta['法規代碼']} | `{folder}` | {meta[date_key]} | {meta['快照日期']} |")
    text = ["# 本地法規快照", "",
            "用 `scripts/law_search.py` 找條號；引用前一律用 `scripts/law_fetch.py` 抓官方原文。",
            "更新：`python -I scripts/law_snapshot.py`。快照日期超過 6 個月，或基準表的修正日期變了，就重抓。", "",
            "| 法規 | 代碼 | 目錄 | 最後修正或發布日期 | 快照日期 |", "|---|---|---|---|---|"] + rows
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(text) + "\n")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    targets = sys.argv[1:] or list(LAWS)
    for pcode in targets:
        if pcode not in LAWS:
            print(f"!! {pcode} 不在清單；請先在 LAWS 加上目錄名稱")
            continue
        try:
            head, n = snapshot(pcode, LAWS[pcode])
            print(f"OK {head['law']}（{pcode}）{head['date_label']} {head['date']}｜{n} 條 → laws/{LAWS[pcode]}/articles.md")
        except Exception as e:  # 網路或解析失敗要明講，不寫入半套資料
            print(f"!! {pcode} 失敗：{e}")
    write_index()


if __name__ == "__main__":
    main()
