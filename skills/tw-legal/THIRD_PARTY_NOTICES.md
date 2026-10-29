# 第三方來源與授權

本 skill 有部分內容改寫自下列開源專案，兩者都採 Apache License 2.0。改寫的地方都在檔案開頭註明出處與修改內容。

要把本 skill 分享給別人時，請一併附上 Apache-2.0 授權全文（https://www.apache.org/licenses/LICENSE-2.0）與本檔。

| 專案 | 版本 | 用在哪裡 | 改了什麼 |
|---|---|---|---|
| anthropics/claude-for-legal | commit 4a6c651（2026-07-23） | references/08 | 只取與法域無關的工作方法，改寫成台灣版；美國法不採用 |
| tern/taiwan-claude-legal | v1.1.0，commit 1edf508（2026-08-26） | references/10；`laws/` 快照與 `scripts/law_snapshot.py` 的做法 | 合約審查流程譯成繁體中文，條文逐條核對；快照改用本 skill 的腳本重抓，保留項、款分行，驗證 HTTPS 憑證，並多收 7 部程序法與特別法 |

法規條文不得為著作權之標的（著作權法9）；`laws/` 快照的內容取自全國法規資料庫。
