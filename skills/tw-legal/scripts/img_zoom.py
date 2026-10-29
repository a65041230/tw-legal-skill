# tw-legal 權利資訊｜著作人：沈慶隆（Ken Shen）｜授權：MIT｜官方來源：https://github.com/a65041230/tw-legal-skill｜識別碼：TWL-KS-20261029
"""截圖、照片、掃描或 PDF 頁面的局部放大，讓日期、金額、案號、姓名等關鍵欄位逐字精讀。

用法（用 -E -P 執行；不要 cd 到證物資料夾）：
  python -E -P img_zoom.py 收據.jpg --grid 2x3 --out zoom_dir           # 切成 2 欄 3 列，每格放大
  python -E -P img_zoom.py 收據.jpg --box 0.10,0.40,0.60,0.55 --out zoom_dir   # 只放大一塊
  python -E -P img_zoom.py 證物.pdf --page 14 --box 0,0,1,0.15 --out zoom_dir  # PDF 第14頁頁首
  python -E -P img_zoom.py 收據.jpg --grid 1x4 --enhance --out zoom_dir  # 灰階＋自動對比，看淡字

--box 用 0～1 的比例（左,上,右,下），不必先知道像素大小。
格子之間預設重疊 8%，避免一行字剛好被切在邊界而漏讀。
"""
import argparse
import os
import sys

from PIL import Image, ImageFilter, ImageOps

MAX_SIDE = 1800  # 單張輸出最長邊；太大反而不利閱讀


def load(path, page, dpi):
    if path.lower().endswith(".pdf"):
        import fitz  # PyMuPDF

        doc = fitz.open(path)
        pix = doc[page - 1].get_pixmap(dpi=dpi)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # 手機照片依 EXIF 轉正
    return img.convert("RGB")


def save_crop(img, box, scale, enhance, out_path):
    w, h = img.size
    l, t, r, b = box
    crop = img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    cw, ch = crop.size
    k = min(scale, MAX_SIDE / max(cw, ch)) if max(cw, ch) * scale > MAX_SIDE else scale
    if k != 1:
        crop = crop.resize((max(1, int(cw * k)), max(1, int(ch * k))), Image.LANCZOS)
    if enhance:
        crop = ImageOps.autocontrast(ImageOps.grayscale(crop), cutoff=1).filter(ImageFilter.SHARPEN)
    crop.save(out_path)
    return crop.size


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--out", required=True, help="輸出資料夾")
    ap.add_argument("--page", type=int, default=1, help="PDF 頁碼（從 1 起算）")
    ap.add_argument("--dpi", type=int, default=200, help="PDF 轉圖解析度")
    ap.add_argument("--box", help="左,上,右,下（0～1 比例）")
    ap.add_argument("--grid", help="欄x列，例如 2x3")
    ap.add_argument("--overlap", type=float, default=0.08, help="格子重疊比例")
    ap.add_argument("--scale", type=float, default=2.5, help="放大倍率")
    ap.add_argument("--enhance", action="store_true", help="灰階＋自動對比＋銳利化")
    args = ap.parse_args()

    img = load(args.src, args.page, args.dpi)
    os.makedirs(args.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.src))[0]
    if stem and args.src.lower().endswith(".pdf"):
        stem += f"_p{args.page}"
    print(f"來源：{os.path.abspath(args.src)}（{img.size[0]}x{img.size[1]} px）")

    boxes = []
    if args.box:
        boxes.append(("box", tuple(float(v) for v in args.box.split(","))))
    if args.grid:
        cols, rows = (int(v) for v in args.grid.lower().split("x"))
        ov = args.overlap
        for r in range(rows):
            for c in range(cols):
                l = max(0.0, c / cols - ov / 2)
                t = max(0.0, r / rows - ov / 2)
                rr = min(1.0, (c + 1) / cols + ov / 2)
                bb = min(1.0, (r + 1) / rows + ov / 2)
                boxes.append((f"r{r + 1}c{c + 1}", (l, t, rr, bb)))
    if not boxes:
        boxes.append(("full", (0.0, 0.0, 1.0, 1.0)))

    for name, box in boxes:
        out = os.path.join(args.out, f"{stem}_{name}{'_enh' if args.enhance else ''}.png")
        size = save_crop(img, box, args.scale, args.enhance, out)
        print(f"  {name}  區塊 {','.join(f'{v:.2f}' for v in box)} → {out}（{size[0]}x{size[1]}）")
    print("讀法：每格逐行讀兩次；看不清的字標〔?〕，不要用上下文補。")


if __name__ == "__main__":
    main()
