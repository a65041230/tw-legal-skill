# 授權與第三方來源

## 本專案的授權

| 內容 | 授權 |
|---|---|
| `skills/tw-legal/` 的 SKILL.md、references/，以及 README、DISCLAIMER 等說明文件 | CC BY-NC-SA 4.0，全文見 [LICENSE](LICENSE) |
| `skills/tw-legal/scripts/` | MIT，全文見 [scripts/LICENSE](skills/tw-legal/scripts/LICENSE) |
| `skills/tw-legal/laws/` 的法條原文 | 法律不得為著作權之標的（著作權法第 9 條），本專案不主張權利；內容取自全國法規資料庫 |

著作權人：沈慶隆（Ken Shen）。

## 改寫自開源專案的部分

下列兩個專案都採 Apache License 2.0，全文見 [LICENSES/Apache-2.0.txt](LICENSES/Apache-2.0.txt)。改寫的地方都在檔案開頭註明出處與修改內容；原專案本身的內容仍依 Apache-2.0。

| 專案 | 版本 | 用在哪裡 | 改了什麼 |
|---|---|---|---|
| anthropics/claude-for-legal | commit 4a6c651（2026-07-23） | references/08 | 只取與法域無關的工作方法，改寫成台灣版；美國法不採用 |
| tern/taiwan-claude-legal | v1.1.0，commit 1edf508（2026-08-26） | references/10；`laws/` 快照與 `scripts/law_snapshot.py` 的做法 | 合約審查流程譯成繁體中文，條文逐條核對；快照改用本專案的腳本重抓，保留項、款分行，驗證 HTTPS 憑證，並多收 7 部程序法與特別法 |

## 選用套件（不隨附）

| 套件 | 授權 | 用在哪裡 |
|---|---|---|
| PyMuPDF | AGPL-3.0 或商業授權 | `scripts/pdf_check.py` |
| Pillow | MIT-CMU | `scripts/img_zoom.py` |

本專案不隨附這兩個套件，由使用者自行安裝。
