"""書狀 PDF 送出前檢查：頁數、紙張、邊界、字級、頁碼、必含／禁止字詞、版本雜湊、逐頁比對。

用法（用 -E -P 執行；不要 cd 到證物資料夾，避免載入來路不明的模組）：
  python -E -P pdf_check.py A.pdf
  python -E -P pdf_check.py A.pdf --must 曾討論由被告到場收取 --forbid 前一日 --forbid BQ
  python -E -P pdf_check.py A.pdf --words 字詞清單.txt          # 每行一個詞；開頭 ! 表示禁止出現
  python -E -P pdf_check.py A.pdf --render out_dir --pages 1,6,14   # 輸出 PNG 供目視（all＝全部）
  python -E -P pdf_check.py A.pdf --compare 舊版.pdf            # 逐頁比對，列出畫面不同的頁
  python -E -P pdf_check.py A.pdf --exhibits 7-23               # 指定證物頁，這些頁不判斷邊界與字級

格式標準依民事訴訟書狀規則第3條（民國114年8月29日修正）：A4、四邊2.5公分、
字型14～20號、頁面底端頁碼。行距與雙面列印無法從 PDF 可靠判斷，要人工確認。
證物頁（截圖、收據影像）的邊界與字級不受此限，報告中只供參考。
沒給 --exhibits 時，用「這頁有沒有影像」猜證物頁；純向量的網頁列印證物會被當成書狀頁而誤報，
所以書狀後面接證物時，請用 --exhibits 指定證物頁範圍。
"""
import argparse
import hashlib
import os
import re
import sys

import fitz  # PyMuPDF

A4 = (595.28, 841.89)
PT_PER_CM = 72 / 2.54
# 「起訴狀　第1頁／共6頁」「附件第2頁」「- 3 -」「3/23」都算頁碼
PAGE_NO = re.compile(r"第\s*\d+\s*頁|^[\s\-－—]*\d+[\s\-－—]*$|\d+\s*[/／]\s*\d+")


def norm(s):
    """去掉空白與換行；PDF 文字常被換行切斷，比對前一定要先正規化。"""
    return re.sub(r"[\s　]+", "", s)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def page_report(page):
    w, h = page.rect.width, page.rect.height
    blocks = [b for b in page.get_text("dict")["blocks"] if b.get("type") == 0]
    sizes = {}
    xs0, ys0, xs1, ys1 = [], [], [], []
    has_page_no = False
    for b in blocks:
        for line in b["lines"]:
            text = "".join(s["text"] for s in line["spans"]).strip()
            if not text:
                continue
            x0, y0, x1, y1 = line["bbox"]
            if y0 > h * 0.85 and PAGE_NO.search(text):
                has_page_no = True
                continue  # 頁碼本來就放在底端邊界內，不算進正文邊界
            xs0.append(x0); ys0.append(y0); xs1.append(x1); ys1.append(y1)
            for s in line["spans"]:
                n = len(s["text"].strip())
                if n:
                    key = round(s["size"] * 2) / 2
                    sizes[key] = sizes.get(key, 0) + n
    margins = None
    if xs0:
        margins = tuple(round(v / PT_PER_CM, 2) for v in (min(xs0), min(ys0), w - max(xs1), h - max(ys1)))
    images = len(page.get_images(full=True))
    return {"size": (w, h), "margins": margins, "font_sizes": sizes, "page_no": has_page_no, "images": images}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--must", action="append", default=[], help="必須出現的字詞（可重複）")
    ap.add_argument("--forbid", action="append", default=[], help="不得出現的字詞（可重複）")
    ap.add_argument("--words", help="字詞清單檔：每行一個，開頭 ! 表示禁止")
    ap.add_argument("--render", help="輸出 PNG 的資料夾")
    ap.add_argument("--pages", default="all", help="要輸出的頁碼，例如 1,6,14 或 all")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--compare", help="另一版 PDF，逐頁比對畫面")
    ap.add_argument("--exhibits", help="證物頁範圍，例如 7-23 或 9-12,15；這些頁不判斷邊界與字級")
    args = ap.parse_args()

    exhibits = set()
    for part in (args.exhibits or "").split(","):
        if part.strip():
            a, _, b = part.strip().partition("-")
            exhibits.update(range(int(a), int(b or a) + 1))

    doc = fitz.open(args.pdf)
    print(f"檔案：{os.path.abspath(args.pdf)}")
    print(f"SHA-256：{sha256(args.pdf)}")
    print(f"頁數：{doc.page_count}")

    problems = []
    texts = []
    print("\n頁｜紙張｜正文邊界 左/上/右/下(cm)｜主要字級(pt:字數)｜頁碼｜影像數")
    for i, page in enumerate(doc, 1):
        r = page_report(page)
        texts.append(norm(page.get_text()))
        w, h = r["size"]
        paper = "A4" if abs(w - A4[0]) < 3 and abs(h - A4[1]) < 3 else f"非A4({w:.0f}x{h:.0f}pt)"
        top_sizes = sorted(r["font_sizes"].items(), key=lambda kv: -kv[1])[:3]
        sizes_txt = " ".join(f"{k:g}:{v}" for k, v in top_sizes) or "-"
        m = r["margins"]
        m_txt = "/".join(f"{v:.2f}" for v in m) if m else "（無文字層）"
        print(f"{i:>2}｜{paper}｜{m_txt}｜{sizes_txt}｜{'有' if r['page_no'] else '無'}｜{r['images']}")
        if paper != "A4":
            problems.append(f"第{i}頁不是 A4")
        if not r["page_no"]:
            problems.append(f"第{i}頁底端找不到頁碼（若頁碼是圖片或特殊格式，請目視確認）")
        is_exhibit = (i in exhibits) if exhibits else r["images"] > 0
        if m and min(m) < 2.4 and not is_exhibit:
            problems.append(f"第{i}頁正文邊界小於 2.5 公分：{m_txt}")
        small = sum(v for k, v in r["font_sizes"].items() if k < 14)
        total = sum(r["font_sizes"].values())
        if total and not is_exhibit and small / total > 0.2:
            problems.append(f"第{i}頁有 {small}/{total} 字小於 14 號")

    musts, forbids = list(args.must), list(args.forbid)
    if args.words:
        with open(args.words, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("!"):
                    forbids.append(line[1:])
                elif line:
                    musts.append(line)
    if musts or forbids:
        print("\n字詞檢查（已去除空白換行；找不到時請用 --render 目視，頁首或表格的抽取順序可能打亂文字）")
    for w in musts:
        pages = [str(i) for i, t in enumerate(texts, 1) if norm(w) in t]
        print(f"  必含  {'OK ' if pages else '缺少'}  {w}  {('第' + ','.join(pages) + '頁') if pages else ''}")
        if not pages:
            problems.append(f"缺少必含字詞：{w}")
    for w in forbids:
        pages = [str(i) for i, t in enumerate(texts, 1) if norm(w) in t]
        print(f"  禁止  {'出現' if pages else 'OK '}  {w}  {('第' + ','.join(pages) + '頁') if pages else ''}")
        if pages:
            problems.append(f"出現禁止字詞：{w}（第{','.join(pages)}頁）")

    if args.compare:
        other = fitz.open(args.compare)
        print(f"\n逐頁比對：{os.path.abspath(args.compare)}（{other.page_count} 頁）")
        diff = []
        for i in range(max(doc.page_count, other.page_count)):
            if i >= doc.page_count or i >= other.page_count:
                diff.append(i + 1)
                continue
            a = hashlib.md5(doc[i].get_pixmap(dpi=40).samples).hexdigest()
            b = hashlib.md5(other[i].get_pixmap(dpi=40).samples).hexdigest()
            if a != b:
                diff.append(i + 1)
        print("  畫面不同的頁：" + (",".join(map(str, diff)) if diff else "無，逐頁相同"))

    if args.render:
        os.makedirs(args.render, exist_ok=True)
        want = range(1, doc.page_count + 1) if args.pages == "all" else [int(p) for p in args.pages.split(",")]
        stem = os.path.splitext(os.path.basename(args.pdf))[0]
        for p in want:
            out = os.path.join(args.render, f"{stem}_p{p:02d}.png")
            doc[p - 1].get_pixmap(dpi=args.dpi).save(out)
            print(f"  已輸出 {out}")

    print("\n結論：" + ("未發現格式或字詞問題（行距、雙面列印、簽名欄仍需人工確認）" if not problems else f"{len(problems)} 項要處理"))
    for p in problems:
        print("  - " + p)


if __name__ == "__main__":
    main()
