<!-- tw-legal 權利資訊｜著作人：沈慶隆（Ken Shen）｜授權：CC BY-NC-ND 4.0｜官方來源：https://github.com/a65041230/tw-legal-skill｜識別碼：TWL-KS-20261029｜請勿移除（著作權法第80條之1） -->

# 給其他 AI 助手的使用說明（AGENTS.md）

本專案主要為 Claude 設計，但技能包是一般的 Markdown 和 Python，其他 AI 助手（例如 Codex）也能用。本檔說明怎麼用，以及和 Claude 版不同的地方。

## 這是什麼

- 台灣法律事務的工作方法與查證工具：先查證、再分析、最後給建議。
- 主檔：`skills/tw-legal/SKILL.md`。參考檔在 `skills/tw-legal/references/`，腳本在 `skills/tw-legal/scripts/`，法條快照在 `skills/tw-legal/laws/`。

## 如果你是 AI 助手

使用者問到台灣的法律或法規時：

1. 先讀 `skills/tw-legal/SKILL.md`，照它的六條底線和作業流程做。
2. 依 SKILL.md 末尾的索引，只讀需要的參考檔，不要一次全讀。
3. 條文、裁判字號、引文、期限、金額，只能來自這次實際打開的官方原文；查不到就說查不到，不要補。
4. 回覆用繁體中文（台灣用語），每個重要陳述標上來源類別，例如【官方原文】【推論】【未核實】。
5. 只準備草稿。寄出、遞狀、繳費、和解都由使用者自己決定。

在本 repo 裡修改檔案時：

- 不要放任何個案資料（姓名、案號、帳號、地址、證物）。
- 不要移除各檔案開頭的「tw-legal 權利資訊」。
- 改完檔案要重算 `MANIFEST.sha256`。

## 安裝

| 工具 | 做法 |
|---|---|
| Claude Code | 見 README 的「安裝」 |
| Codex | 把 `skills/tw-legal` 整個資料夾複製到 `~/.codex/skills/tw-legal`（Windows：`C:\Users\你的帳號\.codex\skills\tw-legal`） |
| 其他支援 AGENTS.md 的工具 | 在本 repo 資料夾開啟工具，它會讀到本檔；或在對話中要它先讀 `skills/tw-legal/SKILL.md` |

## 和 Claude 版不同的地方

| 功能 | Claude | 其他 AI 助手 |
|---|---|---|
| 抓現行條文（`law_fetch.py`）、找條號（`law_search.py`） | 可用 | 可用：只需要 Python 3，Mac、Linux 用 `python3` |
| PDF 檢查、圖片放大 | 可用 | 可用：另外安裝 `pip install pymupdf pillow` |
| 裁判核對（`fjud_verify.js`） | 在內建瀏覽器的司法院頁面執行 | 需要能在網頁內執行 JavaScript 的瀏覽器工具；沒有的話，請使用者自己打開司法院裁判書系統核對 |
| TLR 法律檢索 | 用 Claude 的連接器接 MCP | 依該工具的 MCP 設定方式自行連接；不接也能用，改用官方系統搜尋 |
| 腳本路徑 | SKILL.md 寫的 `~/.claude/skills/tw-legal/scripts` | 改成你放技能包的位置，例如 `~/.codex/skills/tw-legal/scripts` |

SKILL.md 裡提到的「內建瀏覽器」「連接器」是 Claude 的工具名稱；用其他工具時，換成功能相同的工具，沒有就請使用者手動核對，不能略過核對。

## 驗證狀態

- **Claude Code：**技能包與外掛格式驗證通過；腳本實測可執行。
- **Codex 與其他工具：**尚未測試。作者電腦上的 Codex 讀取 `~/.codex/skills` 底下格式相同的技能包，但 tw-legal 本身還沒在 Codex 實際跑過。

## 授權與界線

- 文件採 CC BY-NC-ND 4.0，腳本採 MIT。只限個人自救與教育使用，不得用於商業及工作室。
- 可以為了自己使用而修改，例如改腳本路徑，但不能把改過的版本分享出去。
- 本專案不是法律意見，作者也不是律師。完整內容見 [DISCLAIMER.md](DISCLAIMER.md)。
