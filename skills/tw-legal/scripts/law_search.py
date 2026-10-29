# tw-legal 權利資訊｜著作人：沈慶隆（Ken Shen）｜授權：MIT｜官方來源：https://github.com/a65041230/tw-legal-skill｜識別碼：TWL-KS-20261029
"""在本地法規快照（laws/）用關鍵字找條號。找到後，一律用 law_fetch.py 抓官方原文再引用。

用法（一律用 python -I 執行）：
  python -I law_search.py 違約金
  python -I law_search.py 競業禁止 --law labor-standards-act
  python -I law_search.py 定型化契約 顯失公平        # 多個關鍵字：同一條都要出現

輸出每筆：法規、條號、所在章節、命中處前後文，以及給 law_fetch.py 的「代碼:條號」。
"""
import argparse
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "laws")


def load(folder):
    with open(os.path.join(ROOT, folder, "articles.md"), encoding="utf-8") as f:
        text = f.read()
    name = text.splitlines()[0][2:]
    pcode = re.search(r"- 法規代碼：(\w+)", text).group(1)
    chapter, arts = "", []
    for block in re.split(r"\n(?=## |### )", text):
        if block.startswith("### "):
            no, _, body = block[4:].partition("\n")
            arts.append((no.strip(), chapter, body.strip()))
        elif block.startswith("## "):
            chapter = block[3:].strip()
    return name, pcode, arts


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keywords", nargs="+", help="關鍵字；多個時同一條都要出現")
    ap.add_argument("--law", help="只搜這個目錄，例如 civil-code")
    ap.add_argument("--max", type=int, default=30, help="最多列幾筆")
    args = ap.parse_args()

    folders = [args.law] if args.law else sorted(
        d for d in os.listdir(ROOT) if os.path.isfile(os.path.join(ROOT, d, "articles.md")))
    keys = [re.sub(r"\s+", "", k) for k in args.keywords]
    hits = []
    for folder in folders:
        name, pcode, arts = load(folder)
        for no, chapter, body in arts:
            flat = re.sub(r"\s+", "", body)
            if all(k in flat for k in keys):
                i = flat.find(keys[0])
                flno = re.sub(r"[第條\s]", "", no)
                hits.append(f"{name} {no}｜{chapter}｜…{flat[max(0, i - 30):i + 50]}…｜law_fetch {pcode}:{flno}")
    for h in hits[:args.max]:
        print(h)
    if len(hits) > args.max:
        print(f"（另有 {len(hits) - args.max} 筆沒列出，用 --max 或加關鍵字縮小範圍）")
    if not hits:
        print("快照中查無；換同義詞再查，或到全國法規資料庫全文檢索。查無不代表法律沒有規定。")
    print("※ 快照只用來找條號；引用前用 law_fetch.py 抓官方原文，並確認項、款。")


if __name__ == "__main__":
    main()
