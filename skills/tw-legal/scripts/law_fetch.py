# tw-legal 權利資訊｜著作人：沈慶隆（Ken Shen）｜授權：MIT｜官方來源：https://github.com/a65041230/tw-legal-skill｜識別碼：TWL-KS-20261029
"""從全國法規資料庫（law.moj.gov.tw）抓條文原文，避免憑記憶引用條文。

用法（一律用 python -I 執行）：
  python -I law_fetch.py B0010001:77-13 B0010004:18      # 抓條文：法規代碼:條號
  python -I law_fetch.py --find 非訟事件法                # 用法規名稱查法規代碼（pcode）
  python -I law_fetch.py --law B0010012                  # 只看法規名稱與修正日期
  python -I law_fetch.py --json out.json B0000001:205    # 另存 JSON，方便比對

每條輸出：法規名稱、法規修正日期、條號、條文全文、網址、查詢日。
條號寫法同網站，例如 77-13、14、258-1；也接受「第77條之13」。
日期欄：修正過的法規印「修正日期」，沒修正過的命令印「發布日期」。
"""
import argparse
import datetime
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://law.moj.gov.tw"
HEADERS = {"User-Agent": "Mozilla/5.0 (tw-legal law_fetch)"}


def get(url, tries=3):
    # 網站偶爾會斷線（Remote end closed connection），重試幾次；仍失敗就照實報錯
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2)


def plain(fragment):
    s = re.sub(r"<br\s*/?>", "\n", fragment)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def find(keyword):
    url = f"{BASE}/Law/LawSearchResult.aspx?ty=ONEBAR&kw={urllib.parse.quote(keyword)}"
    page = get(url)
    seen = []
    for pcode, name in re.findall(r'href="[^"]*pcode=([A-Z0-9]+)[^"]*"[^>]*>(.*?)</a>', page, re.S):
        name = plain(name)
        if name and name != "EN" and (pcode, name) not in seen:
            seen.append((pcode, name))
    return seen


_headers = {}


def law_header(pcode):
    """法規名稱、日期欄（修正日期／公布日期／發布日期）與是否廢止。"""
    if pcode not in _headers:
        page = get(f"{BASE}/LawClass/LawAll.aspx?pcode={pcode}")
        name = re.search(r'id="hlLawName"[^>]*>(.*?)</a>', page, re.S)
        # 修正過的法規是「修正日期」（trLNNDate）；沒修正過的命令只有「發布日期」（trLNODate）
        date = (re.search(r'id="trLNNDate"[^>]*>\s*<th>(.*?)</th>\s*<td>(.*?)</td>', page, re.S)
                or re.search(r'id="trLNODate"[^>]*>\s*<th>(.*?)</th>\s*<td>(.*?)</td>', page, re.S))
        head = page[: page.find("LawMenu")] if "LawMenu" in page else page[:20000]
        _headers[pcode] = {
            "law": plain(name.group(1)) if name else None,
            "date_label": plain(date.group(1)).rstrip("：") if date else None,
            "date": plain(date.group(2)) if date else None,
            "abolished": "廢止" in plain(head),
        }
    return _headers[pcode]


def article(pcode, flno):
    url = f"{BASE}/LawClass/LawSingle.aspx?pcode={pcode}&flno={flno}"
    page = get(url)
    no = re.search(r'<div class="col-no">(.*?)</div>', page, re.S)
    lines = []
    start = page.find('<div class="law-article">')
    if start >= 0:
        # 條文各行是不巢狀的 line-xxxx 區塊，表格是 text-pre 區塊（框線字元排版）；
        # 切到 clearfix 為止，避免漏掉最後一行
        end = page.find('class="clearfix"', start)
        segment = page[start:end if end > 0 else None]
        for cls, txt in re.findall(r'<div class="(line-\d+|text-pre)[^"]*">(.*?)</div>', segment, re.S):
            if cls == "text-pre":
                lines.append(html.unescape(re.sub(r"<[^>]+>", "", txt)).rstrip())
            else:
                lines.append("　" * (int(cls[5:]) // 4) + plain(txt))
    head = law_header(pcode)
    return {
        "pcode": pcode,
        "flno": flno,
        "law": head["law"],
        "date_label": head["date_label"],
        "date": head["date"],
        "abolished": head["abolished"],
        "article_no": plain(no.group(1)) if no else None,
        "text": "\n".join(lines) if lines else None,
        "url": url,
        "checked": datetime.date.today().isoformat(),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("items", nargs="*", help="法規代碼:條號，例如 B0010004:18")
    ap.add_argument("--find", help="用法規名稱查法規代碼")
    ap.add_argument("--law", help="只看這個法規代碼的名稱與修正日期")
    ap.add_argument("--json", help="另存 JSON 檔")
    args = ap.parse_args()

    if args.find:
        for pcode, name in find(args.find):
            print(f"{pcode}\t{name}")
    if args.law:
        h = law_header(args.law)
        print(f"{args.law}\t{h['law']}\t{h['date_label']}：{h['date']}" + ("\t※已廢止" if h["abolished"] else ""))

    results = []
    for item in args.items:
        pcode, _, flno = item.partition(":")
        # 容許「第77條之13」「77之13」這類寫法，換成網站用的 77-13
        flno = re.sub(r"\s*之\s*", "-", re.sub(r"[第條\s]", "", flno))
        try:
            r = article(pcode.strip(), flno.strip())
        except Exception as e:  # 網路錯誤要明講，不能當成查到
            print(f"!! {item} 查詢失敗：{e}\n")
            continue
        results.append(r)
        if not r["text"]:
            print(f"!! {item} 查無條文（條號錯、已刪除或網址改版），不得引用\n")
            continue
        flag = "　※法規已廢止" if r["abolished"] else ""
        print(f"【{r['law']}】{r['article_no']}{flag}")
        print(f"{r['date_label']}：{r['date']}｜查詢日：{r['checked']}")
        print(r["url"])
        print(r["text"])
        if re.search(r"如下表|附表|附件", r["text"]) and "─" not in r["text"]:
            print("※ 本條提到表格、附表或附件，但沒抓到表格內容；請開上方網址看原表，不要憑文字推算。")
        print()

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
