# 學術論文分類與摘要系統 — 設計紀錄

> 本文件記錄系統從需求討論到實作的完整設計過程。

---

## 一、專案目標

設計一個以 LangGraph + Python 為基礎的 agent，能夠：

1. **批次讀取**資料夾內的學術論文（PDF 格式）
2. 依照預設的 7 項評分標準，**自動分類**論文為 A1、A2、A3 三個等級
3. 將論文**移動**至對應的資料夾
4. 依照指定格式，**生成摘要**並寫入 .md 文件
5. 支援**增量處理**，避免重複處理已完成的論文

核心價值：讓 agent 先做粗篩，使用者再根據分類結果決定閱讀順序，從最高價值的論文開始細讀。

---

## 二、系統設定

| 項目     | 決定                         |
| -------- | ---------------------------- |
| 主要 LLM | OpenAI gpt-5.3-chat-latest   |
| 備用 LLM | Anthropic Claude             |
| 程式語言 | Python 3.12                  |
| 核心框架 | LangGraph                    |
| PDF 解析 | PyMuPDF（fitz）              |
| 研究領域 | 科技教學、社會科學、教育遊戲 |

---

## 三、論文分類標準

Agent 依照以下 7 項標準評估每篇論文，每項回答「是」或「否」：

| 編號   | 標準                                                         |
| ------ | ------------------------------------------------------------ |
| 標準 1 | 論文採用量化研究方法（問卷調查），非回顧性、概念性或質性論文 |
| 標準 2 | 論文有提出研究假設和研究模型（如 TAM、TPB 等）               |
| 標準 3 | 論文有說明問卷來源或測量工具的依據（引用來源或自行開發）     |
| 標準 4 | 論文有解釋研究構面的定義                                     |
| 標準 5 | 論文有說明研究對象、樣本數量及抽樣方式                       |
| 標準 6 | 論文有進行統計分析（如迴歸、SEM、路徑分析、ANOVA 等）        |
| 標準 7 | 論文有提出具體的實務建議或未來研究方向                       |

### 分類對應邏輯

| 符合標準數 | 分類 | 說明             |
| ---------- | ---- | ---------------- |
| 6 - 7 項   | A1   | 高價值，優先細讀 |
| 4 - 5 項   | A2   | 中等，可參考     |
| 0 - 3 項   | A3   | 較低，暫緩或略過 |

---

## 四、摘要輸出格式

每篇論文的個別摘要包含以下欄位：

| 欄位       | 說明                                          |
| ---------- | --------------------------------------------- |
| 論文標題   | 原始標題，英文保留英文                        |
| APA 7 引用 | 依格式自動生成                                |
| 分類結果   | A1 / A2 / A3                                  |
| 評分依據   | 固定 ✅/❌ 單行格式，對應 7 項標準            |
| 研究目的   | 100 字以內                                    |
| 研究方法   | 100 字以內，說明資料收集與分析方式            |
| 研究模型   | 50 字以內，說明採用的理論模型，如無則填「無」 |
| 主要發現   | 150 字以內                                    |
| 研究貢獻   | 80 字以內，說明對領域的新知識或新發現         |
| 研究限制   | 80 字以內                                     |

### 評分依據格式

```
評分依據: ✅/❌量化研究方法 ✅/❌研究假設或模型 ✅/❌問卷或測量工具 ✅/❌構面定義 ✅/❌對象樣本及抽樣方式 ✅/❌統計分析 ✅/❌實務或未來建議
```

### 總表格式

每個等級（A1、A2、A3）各有一份總表（`summary_AX.md`），欄位為：

- 論文標題
- 評分依據
- 主要發現

總表在每次程式啟動時自動重建，確保內容不重複。

---

## 五、資料夾結構

**專案目錄（程式本體，不儲存任何資料）：**

```
2026-03-PDFagent/
│
├── main.py                       # 主程式入口
├── pa-start.bat                  # 啟動環境（啟動 venv 並設定 pa-init、pa-run、pa-list、pa-redo、pa-exit 別名）
├── .env                          # API Key（不可分享）
├── .env.example                  # 環境變數範本（可分享）
│
├── core/                         # 核心 pipeline 邏輯
│   ├── orchestrator.py           # Graph 建立、錯誤路由、dead letter、重建總表
│   ├── state.py                  # PaperState TypedDict 定義
│   └── scan.py                   # 掃描待處理論文
│
├── agents/                       # 各 Agent 模組
│   ├── extractor.py              # PDF 文字擷取
│   ├── classifier.py             # 論文分類
│   └── summarizer.py             # 摘要生成
│
├── tools/                        # 工具腳本（使用者手動執行）
│   ├── init.py                   # 初始化工作目錄的資料夾結構
│   ├── rerun.py                  # 重跑指定論文
│   └── list_papers.py            # 顯示已處理論文清單
│
├── prompts/                      # Prompt 檔案（與程式碼分離）
│   ├── classify.md               # 分類用 prompt（繁體中文版）
│   ├── classify_en.md            # 分類用 prompt（英文版，目前使用）
│   ├── summarize.md              # 摘要用 prompt（繁體中文版）
│   └── summarize_en.md           # 摘要用 prompt（英文版，目前使用）
│
├── docs/                         # 設計文件
│   └── design.md
│
└── venv/                         # 虛擬環境
```

**工作目錄（使用者的論文資料夾，由程式自動建立）：**

```
工作目錄/（使用者 cd 到此處後執行 pa-run）
│
├── input/                        # 放待處理的 PDF
│
├── output/
│   ├── A1/
│   │   ├── pdf/                  # A1 論文 PDF
│   │   ├── summary/              # A1 個別摘要 .md
│   │   └── json/                 # A1 總表重建用 .json
│   ├── A2/
│   │   ├── pdf/
│   │   ├── summary/
│   │   └── json/
│   ├── A3/
│   │   ├── pdf/
│   │   ├── summary/
│   │   └── json/
│   ├── error/                    # 無法處理的 PDF
│   ├── summary_A1.md             # A1 總表（自動重建）
│   ├── summary_A2.md             # A2 總表（自動重建）
│   └── summary_A3.md             # A3 總表（自動重建）
│
├── logs/
│   ├── dead_letter.md            # 超過重試上限的論文紀錄
│   └── rebuild_warnings.md       # 總表重建時 JSON 損壞的警告紀錄
│
├── processed_papers.md           # 已處理論文的 log（含日期標題）
└── error_papers.md               # 錯誤論文的 log（含日期標題）
```

---

## 六、增量處理邏輯

每次執行前，agent 讀取 `processed_papers.md`，確認哪些 PDF 已處理過：

```
## 2026-03-17

- paper_001.pdf
- smith_2023_gamification.pdf
```

- **已在 log 中**：跳過，不重複處理
- **不在 log 中**：視為新論文，進行分類與摘要

使用 **PDF 檔名**（而非論文標題）作為識別鍵，確保比對穩定可靠。

### 重新處理論文

若需重新處理某篇論文，使用 `rerun.py` 工具自動完成準備步驟：

```bash
python rerun.py
```

啟動後輸入論文檔名（一行一篇，空白行結束）：

```
請輸入論文檔名（一行一篇，輸入空白行結束）：
> 2024-AI in education.pdf
> 2021-A Holistic Approach...pdf
>

正在處理：2024-AI in education.pdf... 完成 ✅
正在處理：2021-A Holistic Approach...pdf... 完成 ✅

完成！成功 2 篇 / 失敗 0 篇
請執行 python main.py 開始重新處理。
```

`rerun.py` 會自動：

1. 在 `output/A1/pdf`、`output/A2/pdf`、`output/A3/pdf` 中尋找該 PDF
2. 將 PDF 移回 `input/`
3. 從 `processed_papers.md` 刪除該筆紀錄

若找不到指定檔名，該篇跳過並顯示錯誤，不影響其他篇的處理。

重新執行 `python main.py` 後，`save_results` 會自動清除其他分類資料夾中的同名舊檔案（`.md` 與 `.json`），再寫入新結果。總表會在啟動時自動重建。

---

## 七、錯誤處理機制

### 錯誤分類與處理方式

| 錯誤情境                                | 處理方式                                   | PDF 去向                  |
| --------------------------------------- | ------------------------------------------ | ------------------------- |
| 加密或損壞的 PDF                        | 記錄至 error_papers.md，跳過               | 移至 output/error/        |
| 純圖片 PDF（文字過短）                  | 記錄至 error_papers.md，跳過               | 移至 output/error/        |
| LLM 無回覆（網路/API 問題）             | 重試 3 次，仍失敗則記錄跳過                | 留在 input/，等待下次重試 |
| LLM 回覆欄位不完整                      | 以空字串填入，不影響程式執行               | 正常處理                  |
| save_results 找不到 PDF（上次執行中斷） | 印出警告，記錄至 error_papers.md，略過繼續 | 不移動                    |

### LLM 重試機制

遇到任何 LLM 呼叫失敗時，自動等待 10 秒後重試，最多重試 3 次：

```
第1次失敗 → 等 10 秒 → 重試
第2次失敗 → 等 10 秒 → 重試
第3次失敗 → 記錄錯誤，跳過這篇
```

### 錯誤 log 格式

```
## 2026-03-17

- paper1.pdf（file has not been decrypted）
- paper2.pdf（無法擷取文字，可能為純圖片 PDF）
- paper3.pdf（LLM 無回覆：ConnectionError）
```

---

## 八、啟動時檢查

程式啟動時依序執行以下檢查，任一失敗即停止並顯示明確錯誤訊息：

1. 確保所有必要資料夾存在（自動建立）
2. 確認 `prompts/classify_en.md` 與 `prompts/summarize_en.md` 存在
3. 確認 `OPENAI_API_KEY` 已設定
4. 重建三份總表（`summary_A1.md`、`summary_A2.md`、`summary_A3.md`）

---

## 九、LangGraph 架構

### 整體架構

系統分為兩層：

| 層              | 檔案                                                                  | 職責                                                       |
| --------------- | --------------------------------------------------------------------- | ---------------------------------------------------------- |
| Orchestrator 層 | `orchestrator.py`                                                     | Graph 建立、任務初始化（thread_id）、錯誤路由、dead letter |
| Pipeline 層     | `agents/extractor.py`、`agents/classifier.py`、`agents/summarizer.py` | 各自負責單一處理步驟                                       |

### 流程圖

```
開始
  ↓
啟動檢查（資料夾、prompt 檔案、API Key）
掃描待處理論文（scan.py）
重建總表（orchestrator.py）
  ↓
[init_paper]
  產生 thread_id（格式：20260318-143022-paper_A）
  重置 retry_count、failed_node、error_message
  ↓
[run_extractor]
  用 PyMuPDF 擷取 PDF 文字（限制 35,000 字）
  ├─ 失敗 → failed_node = "extractor" → handle_error
  └─ 正常 ↓
[run_classifier]
  LLM 評估 7 項標準 → 決定 A1 / A2 / A3
  ├─ 失敗 → failed_node = "classifier" → handle_error
  └─ 正常 ↓
[run_summarizer]
  LLM 生成結構化摘要
  ├─ 失敗 → failed_node = "summarizer" → handle_error
  └─ 正常 ↓
[save_results]
  儲存個別 .md、儲存 .json、移動 PDF、更新 log
  ↓
還有未處理的論文？
  ├─ 是 → 回到 init_paper
  └─ 否 → 結束

[handle_error]
  retry_count + 1
  ├─ retry_count < 3 → 回到 failed_node 對應的節點重試
  └─ retry_count >= 3 → write_dead_letter → 下一篇或結束
```

### State 設計

Agent 各節點之間透過 `PaperState`（TypedDict，定義於 `state.py`）傳遞共享資料：

| 欄位                  | 說明                                                  |
| --------------------- | ----------------------------------------------------- |
| `papers_to_process`   | 待處理的 PDF 檔名清單                                 |
| `current_paper`       | 目前正在處理的 PDF                                    |
| `thread_id`           | 任務識別碼（時間戳記 + 檔名）                         |
| `extracted_text`      | 從 PDF 擷取的文字內容                                 |
| `classification`      | 分類結果（A1 / A2 / A3）                              |
| `criteria_met`        | 符合的標準清單                                        |
| `summary`             | 摘要各欄位內容                                        |
| `processed_count`     | 已處理論文數量                                        |
| `error_count`         | 累計錯誤數量                                          |
| `total_input_tokens`  | 累計輸入 token 數                                     |
| `total_output_tokens` | 累計輸出 token 數                                     |
| `paper_input_tokens`  | 本篇輸入 token 數                                     |
| `paper_output_tokens` | 本篇輸出 token 數                                     |
| `retry_count`         | 目前重試次數                                          |
| `failed_node`         | 失敗的節點名稱（extractor / classifier / summarizer） |
| `error_message`       | 失敗原因                                              |

---

## 十、Token 用量追蹤

每篇論文處理完畢後，程式會顯示：

```
本篇 Token：輸入 4,231 / 輸出 623 / 費用約 $0.0169
```

全部完成後顯示總計：

```
總 Token：輸入 4,231 / 輸出 623
總費用約：$0.0169 USD
```

費用計算基準（GPT-4o）：

- 輸入：$2.5 / 1M tokens
- 輸出：$10.0 / 1M tokens

---

## 十一、安裝與執行

### 環境需求

- Python 3.12+
- OpenAI API Key（需有餘額）

### 安裝步驟

```bash
# 建立虛擬環境
python -m venv venv
venv\Scripts\activate

# 安裝套件
pip install langgraph langchain-openai langchain-anthropic pymupdf python-dotenv
```

### 設定 API Key

編輯 `.env` 檔案：

```
OPENAI_API_KEY=你的金鑰
ANTHROPIC_API_KEY=你的金鑰
```

### 執行

```bash
python main.py
```

將 PDF 放入 `input/` 資料夾後執行即可。

---

## 十二、設計決策紀錄

| 問題                                                           | 決定                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 原因                                                                                                                                                                                                                                                                                                                                                                                     |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 增量處理的識別方式                                             | 使用 PDF 檔名寫入 log                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | 比論文標題更穩定，不受 LLM 抽取差異影響                                                                                                                                                                                                                                                                                                                                                  |
| PDF 文字長度限制                                               | 30,000 字                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | 平衡內容完整性與 API 速率限制，避免頻繁觸發 TPM 上限                                                                                                                                                                                                                                                                                                                                     |
| PDF 處理方式                                                   | 移動（而非複製）                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | 節省儲存空間，input 資料夾保持整潔                                                                                                                                                                                                                                                                                                                                                       |
| 總表欄位                                                       | 僅含標題、評分依據、主要發現                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | 欄位過多會降低閱讀效率                                                                                                                                                                                                                                                                                                                                                                   |
| 模型切換方式                                                   | 由 pa-init 互動式詢問並寫入 .env（OPENAI_MODEL），main.py 從環境變數讀取                                                                                                                                                                                                                                                                                                                                                                                                                                 | 使用者在初始化時選擇模型，不需要手動編輯程式碼；模型清單集中定義於 tools/init.py 的 MODELS 常數                                                                                                                                                                                                                                                                                          |
| Prompt 管理方式                                                | 獨立為 prompts/ 資料夾的 .md 檔案                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | 資料與程式碼分離，調整標準或格式不需動程式碼                                                                                                                                                                                                                                                                                                                                             |
| 分類標準數量                                                   | 從 6 項擴充為 7 項                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 新增「實務建議或未來研究方向」，提升論文實用性的鑑別度                                                                                                                                                                                                                                                                                                                                   |
| 評分依據格式                                                   | 固定 ✅/❌ 單行格式                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | 多行格式導致解析失敗，改為單行確保程式正確讀取                                                                                                                                                                                                                                                                                                                                           |
| 摘要欄位調整                                                   | 新增研究貢獻、拆開研究模型                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | 研究假設/模型與研究方法邊界不清，拆開後定義更明確；研究貢獻補充學術價值維度                                                                                                                                                                                                                                                                                                              |
| 評分依據一致性                                                 | summarize prompt 傳入 criteria_met 與對照表                                                                                                                                                                                                                                                                                                                                                                                                                                                              | 避免 GPT 重新評分，確保摘要的評分依據與分類結果一致                                                                                                                                                                                                                                                                                                                                      |
| 錯誤 PDF 處理                                                  | 移至 output/error/，記錄至 error_papers.md                                                                                                                                                                                                                                                                                                                                                                                                                                                               | 與正常論文分離，方便事後查看；log 保持乾淨                                                                                                                                                                                                                                                                                                                                               |
| LLM 失敗處理                                                   | PDF 留在 input/，等待下次重試                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | LLM 問題是外部服務問題，非 PDF 本身問題，不應移走                                                                                                                                                                                                                                                                                                                                        |
| 總表重複寫入問題                                               | 每次啟動重建總表，資料來源改為 .json                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 從 processed_papers.md 刪除紀錄重跑時，總表不會累積重複內容                                                                                                                                                                                                                                                                                                                              |
| 輸出資料夾結構                                                 | A1/A2/A3 各自細分 pdf/summary/json 子資料夾                                                                                                                                                                                                                                                                                                                                                                                                                                                              | 不同類型檔案分開存放，結構清晰易於管理                                                                                                                                                                                                                                                                                                                                                   |
| log 日期標題重複問題                                           | 寫入前檢查今日日期是否已存在於 log                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 同一天多次執行會各自寫入日期標題，改為先比對避免重複                                                                                                                                                                                                                                                                                                                                     |
| 重跑論文舊檔案殘留                                             | save_results 寫入前清除其他分類資料夾的同名舊檔案                                                                                                                                                                                                                                                                                                                                                                                                                                                        | 重跑後分類可能改變，不清除會導致多個分類資料夾都有同篇論文                                                                                                                                                                                                                                                                                                                               |
| 重跑工具設計                                                   | 獨立的 rerun.py，採互動式輸入                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | 論文檔名含括號等特殊字元，命令列參數傳遞不穩定，改為 input() 讀取避免解析問題                                                                                                                                                                                                                                                                                                            |
| 評分依據全不符合                                               | summarize prompt 加入「若皆不符合則填入：無符合標準」規則                                                                                                                                                                                                                                                                                                                                                                                                                                                | 全部不符合時原本回傳空字串，識別度低，不易與 LLM 漏回覆區分                                                                                                                                                                                                                                                                                                                              |
| Prompt 改為英文版                                              | 新增 classify_en.md 與 summarize_en.md，main.py 改為載入英文版                                                                                                                                                                                                                                                                                                                                                                                                                                           | 英文 prompt 對 LLM 理解更直接，輸出格式更穩定；原中文版保留備用                                                                                                                                                                                                                                                                                                                          |
| 分類完成後顯示使用模型                                         | classify_paper 取得回覆後印出 response_metadata 的 model_name                                                                                                                                                                                                                                                                                                                                                                                                                                            | 方便確認實際使用的模型，model_name fallback 至 llm.model_name                                                                                                                                                                                                                                                                                                                            |
| 分類完成後顯示符合標準清單                                     | print 改為顯示「符合 N 項標準（Criterion 1, Criterion 3, ...）」                                                                                                                                                                                                                                                                                                                                                                                                                                         | 方便即時核對 LLM 評分結果是否合理                                                                                                                                                                                                                                                                                                                                                        |
| save_results 路徑防護                                          | classification 不在 A1/A2/A3 時自動 fallback 到 A3                                                                                                                                                                                                                                                                                                                                                                                                                                                       | LLM 失敗導致 classification 為空字串時，路徑會拼成 output\summary\ 造成 FileNotFoundError                                                                                                                                                                                                                                                                                                |
| temperature 參數                                               | 不設定（使用模型預設值 1）                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | gpt-5.3-chat-latest 不支援修改 temperature，強制設為 0 會導致 API 400 錯誤                                                                                                                                                                                                                                                                                                               |
| save_results PDF 找不到錯誤                                    | 加入 try/except FileNotFoundError，印出警告並記錄至 error_papers.md                                                                                                                                                                                                                                                                                                                                                                                                                                      | 上次執行中斷時 PDF 可能已移動但 log 未寫入，下次執行會重新處理但找不到檔案，應跳過而非中斷整個程式                                                                                                                                                                                                                                                                                       |
| Prompt 結構重整                                                | classify 與 summarize 的 prompt 加入區塊標題、推理要求、正確/錯誤範例                                                                                                                                                                                                                                                                                                                                                                                                                                    | 讓 LLM 更清楚區分各區塊，推理要求提升判斷準確度，範例減少 ✅/❌ 混用錯誤                                                                                                                                                                                                                                                                                                                 |
| 標準 1 定義收窄                                                | 從「有實驗結果」改為「採用量化研究方法（問卷調查），非回顧性、概念性或質性論文」                                                                                                                                                                                                                                                                                                                                                                                                                         | 更符合研究目標：篩選量化問卷研究，明確排除質性論文                                                                                                                                                                                                                                                                                                                                       |
| summarize 評分依據一致性強化                                   | 推理要求加入第3條：輸出前確認評分依據的 ✅ 項目與已符合的標準完全一致                                                                                                                                                                                                                                                                                                                                                                                                                                    | 避免 LLM 自行重新評分，確保摘要與分類結果一致                                                                                                                                                                                                                                                                                                                                            |
| 未使用的 import 清除                                           | 移除 ChatAnthropic 與 RateLimitError                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 兩者皆未實際使用，保留會造成誤解並增加不必要的相依性                                                                                                                                                                                                                                                                                                                                     |
| LOG_FILE 讀寫順序修正                                          | 先讀取 LOG_FILE 內容，再開啟寫入                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | 檔案已以 "a" 模式開啟後又用 read_text() 讀取，邏輯不穩定，改為先讀後寫                                                                                                                                                                                                                                                                                                                   |
| 本篇 token 費用計算修正                                        | AgentState 新增 paper_input_tokens 與 paper_output_tokens 記錄本篇用量                                                                                                                                                                                                                                                                                                                                                                                                                                   | 原本使用累計 token 計算本篇費用，導致顯示數字不正確                                                                                                                                                                                                                                                                                                                                      |
| 錯誤 log 寫入邏輯重構                                          | 抽出 log_error() 函式，取代四處重複的寫入邏輯                                                                                                                                                                                                                                                                                                                                                                                                                                                            | 相同邏輯重複四次，不易維護，集中管理後修改只需動一處                                                                                                                                                                                                                                                                                                                                     |
| rebuild_summaries 寫入方式統一                                 | 改為先收集所有內容再一次性 write_text 寫入                                                                                                                                                                                                                                                                                                                                                                                                                                                               | 原本混用 write_text 清空與 open("a") 附加，改為統一方式邏輯更清晰                                                                                                                                                                                                                                                                                                                        |
| 新增 list_papers.py 工具腳本                                   | 整合查詢選單，可查看已處理論文清單與錯誤論文清單，輸入空白行結束                                                                                                                                                                                                                                                                                                                                                                                                                                         | 兩個功能性質相同，整合後減少腳本數量，結構更乾淨                                                                                                                                                                                                                                                                                                                                         |
| 工作目錄改為 Path.cwd()                                        | 移除詢問邏輯，直接以執行指令時所在的資料夾為工作目錄                                                                                                                                                                                                                                                                                                                                                                                                                                                     | 使用者先 cd 到工作資料夾再執行，比詢問更直覺；三個腳本（main.py、list_papers.py、rerun.py）皆採用此方式                                                                                                                                                                                                                                                                                  |
| PROMPTS_DIR 改為絕對路徑                                       | 使用 Path(**file**).parent / "prompts" 取代相對路徑                                                                                                                                                                                                                                                                                                                                                                                                                                                      | 在其他資料夾執行時，相對路徑會指向錯誤位置，改為絕對路徑確保永遠指向專案目錄                                                                                                                                                                                                                                                                                                             |
| 改用 pa-start.bat + doskey                                     | 建立 pa-start.bat，用 doskey 設定 pa-run、pa-list、pa-redo 別名，cmd /k 保持視窗                                                                                                                                                                                                                                                                                                                                                                                                                         | 獨立 .bat 開新視窗導致結果消失，改用 doskey 在同一視窗執行；刪除 pa-run.bat、pa-list.bat、pa-rerun.bat                                                                                                                                                                                                                                                                                   |
| pa-rerun 改名為 pa-redo                                        | doskey 別名從 pa-rerun 改為 pa-redo                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | pa-rerun 與 cmd 內建名稱衝突，導致指令無法執行                                                                                                                                                                                                                                                                                                                                           |
| 新增 pa-exit 指令                                              | doskey pa-exit=deactivate，退出虛擬環境                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | 原本只能關閉 cmd 視窗才能退出，改用 pa-exit 可在同一視窗退出                                                                                                                                                                                                                                                                                                                             |
| 新增 pa-init 指令                                              | 新建 init.py，建立工作目錄下的資料夾結構；pa-run 保留容錯                                                                                                                                                                                                                                                                                                                                                                                                                                                | 讓使用者可在放入 PDF 前先確認資料夾結構；pa-run 保留自動建立，避免忘記執行 pa-init 時出錯                                                                                                                                                                                                                                                                                                |
| 專案目錄與資料分離                                             | 移除專案目錄內的 input/、output/、processed_papers.md、error_papers.md                                                                                                                                                                                                                                                                                                                                                                                                                                   | 專案目錄只放程式本體，資料由程式在使用者的工作目錄自動建立，保持專案乾淨                                                                                                                                                                                                                                                                                                                 |
| State 型別安全                                                 | 新增 `state.py`，以 `TypedDict` 定義 `PaperState`；`StateGraph(dict)` 改為 `StateGraph(PaperState)`；所有 node 函數簽名改為 `PaperState`                                                                                                                                                                                                                                                                                                                                                                 | 補上型別標注後，欄位打錯字可在執行前被 IDE 或型別檢查工具（mypy）發現，降低 KeyError 的風險                                                                                                                                                                                                                                                                                              |
| 重構為 Orchestrator + Pipeline 架構                            | 新增 agents/（extractor、classifier、summarizer）、orchestrator.py、scan.py；main.py 精簡為入口                                                                                                                                                                                                                                                                                                                                                                                                          | 原本 main.py 承擔所有邏輯，重構後各模組職責單一，易於維護與擴充                                                                                                                                                                                                                                                                                                                          |
| save_results 保留在 orchestrator.py                            | 不另立 agents/saver.py                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | save_results 只做確定性的 I/O 操作（寫檔、移動 PDF、更新 log），不涉及任何判斷或推理，性質與 extractor/classifier/summarizer 不同；搬移只會增加檔案數量而無實質好處，也會讓 agents/ 資料夾的定位變模糊                                                                                                                                                                                   |
| 禁止 silent catch                                              | save_results 的 FileNotFoundError 改為寫入 state["failed_node"] 與 state["error_message"]，取代原本只有 print 的寫法                                                                                                                                                                                                                                                                                                                                                                                     | 所有未處理的例外必須往上拋或寫入 state.error，確保錯誤不被靜默略過；原本的寫法會讓找不到 PDF 的論文被當成成功處理並寫入 log                                                                                                                                                                                                                                                              |
| classifier LLM 回傳值驗證                                      | 解析後驗證 classification 是否在 ("A1", "A2", "A3") 內，不通過則寫入 state["failed_node"] 與 state["error_message"]                                                                                                                                                                                                                                                                                                                                                                                      | LLM 回傳不在清單的值時必須觸發重試，禁止直接寫入 state 或靜默 fallback 為預設值（如 "A3"）；原本以 else 兜底的寫法會讓無效值被當成合法結果處理                                                                                                                                                                                                                                           |
| 兩層重試架構不採用                                             | 維持現有單層重試（invoke_with_retry + handle_error），不引入 tenacity 或獨立的 utils/retry.py                                                                                                                                                                                                                                                                                                                                                                                                            | 兩層獨立計數會讓實際重試次數相乘（最多 9 次），行為不直觀且難以追蹤；引入 tenacity 只是替換現有運作正常的機制，增加外部相依性而無實質好處；系統規模不需要對不同錯誤類型分別設定重試策略，現有一層重試已足夠                                                                                                                                                                              |
| 專案資料夾重組                                                 | 新增 core/（orchestrator.py、state.py、scan.py）與 tools/（init.py、rerun.py、list_papers.py）；main.py 保留在根目錄                                                                                                                                                                                                                                                                                                                                                                                     | 根目錄原本有 7 個 Python 檔案過於雜亂；core/ 集中放程式執行必要的核心邏輯，tools/ 集中放使用者手動執行的輔助腳本，分類明確易於維護                                                                                                                                                                                                                                                       |
| .env 自動建立                                                  | pa-init 互動式詢問 API Key 與模型，由程式寫入 .env；若 .env 已存在則詢問是否覆蓋                                                                                                                                                                                                                                                                                                                                                                                                                         | 原本需要使用者手動複製 .env.example 並填入內容，改為由 init.py 引導建立，降低設定門檻；覆蓋確認避免誤覆蓋已設定好的 Key                                                                                                                                                                                                                                                                  |
| LLM 初始化時機                                                 | llm 與 invoke_with_retry 移入 if **name** == "**main**" 區塊，放在 .env 驗證之後                                                                                                                                                                                                                                                                                                                                                                                                                         | 原本 llm 在 module 層級初始化，.env 缺失時會在 import 階段崩潰，友善錯誤訊息不會執行；移入驗證後才初始化，確保錯誤訊息一定能顯示                                                                                                                                                                                                                                                         |
| save_results 無限迴圈修正                                      | FileNotFoundError 時從 papers_to_process 移除當前論文並清除 failed_node                                                                                                                                                                                                                                                                                                                                                                                                                                  | save_results 出口接的是 should_continue 而非 handle_error；原本失敗時論文不會被消耗，導致 should_continue 不斷選到同一篇造成無限迴圈                                                                                                                                                                                                                                                     |
| extractor 重試邏輯修正                                         | PDF 損壞等 Exception 不移動檔案，進重試流程；純圖片 PDF 直接跳過，不進重試流程                                                                                                                                                                                                                                                                                                                                                                                                                           | 原本兩種情況都移動 PDF 後進重試，導致後兩次重試因找不到檔案而覆蓋原始錯誤訊息；現在依錯誤是否可恢復分開處理                                                                                                                                                                                                                                                                              |
| error_papers.md 實作                                           | extractor 跳過純圖片 PDF 時、write_dead_letter 時，分別寫入 error_papers.md                                                                                                                                                                                                                                                                                                                                                                                                                              | 原本 error_papers.md 在 state 中存在也被 list_papers.py 查詢，但 pipeline 從未實際寫入，導致查詢結果永遠為空                                                                                                                                                                                                                                                                             |
| error_papers.md 與 dead_letter.md 職責分離                     | error_papers.md 給使用者看（簡短描述）；dead_letter.md 給開發者看（thread_id、節點、重試次數、完整錯誤）                                                                                                                                                                                                                                                                                                                                                                                                 | 兩份 log 原本職責重疊；分開後使用者查詢錯誤論文清單只需看 error_papers.md，開發者除錯看 dead_letter.md                                                                                                                                                                                                                                                                                   |
| 總表即時重建                                                   | save_results 完成後立即呼叫 rebuild_summaries                                                                                                                                                                                                                                                                                                                                                                                                                                                            | 原本總表只在程式啟動時重建一次，本輪新處理的論文要等下次執行才會出現在總表，使用者容易誤判沒有寫入                                                                                                                                                                                                                                                                                       |
| rebuild_summaries 錯誤處理                                     | JSON 讀取改為 try/except，失敗時印出警告、跳過該檔案，並寫入 `logs/rebuild_warnings.md`                                                                                                                                                                                                                                                                                                                                                                                                                  | 原本 JSON 格式錯誤或缺少欄位只有 console print，執行視窗關閉後無從追查；損壞的 JSON 會讓該篇從總表靜默消失，但不進 error_papers.md 或 dead_letter.md，屬於資料可見性風險；改為寫入獨立的 rebuild_warnings.md，與 pipeline 錯誤（error_papers.md）和重試超限（dead_letter.md）性質不同，分開記錄更清晰；記錄格式含分類路徑（如 A1/json/paper.json）與實際錯誤訊息，方便使用者定位損壞檔案 |
| extractor 永久性錯誤分流                                       | fitz.FileDataError（損壞、加密）改為直接跳過，不進重試流程；其他 Exception 維持進重試流程                                                                                                                                                                                                                                                                                                                                                                                                                | 原本所有 fitz 例外都走重試流程，導致損壞或加密的 PDF 被無意義重試 3 次；依錯誤是否可恢復分流後，永久性錯誤移至 output/error/ 並寫入 error_papers.md                                                                                                                                                                                                                                      |
| save_results json_path 一致性修正                              | json_path 改為使用 cls_folder（與 md_path 一致）                                                                                                                                                                                                                                                                                                                                                                                                                                                         | 原本 md_path 有 fallback 到 A3，json_path 直接使用 classification，兩條路徑行為不一致，容易造成維護混淆                                                                                                                                                                                                                                                                                  |
| summarizer LLM 回傳驗證                                        | 解析後若 summary 為空 dict，寫入 failed_node 觸發重試                                                                                                                                                                                                                                                                                                                                                                                                                                                    | 原本 LLM 回傳空白或格式異常時 summary 為空 dict，直接寫入 state 產生全空白摘要，不觸發重試也不提示錯誤                                                                                                                                                                                                                                                                                   |
| main.py 移除未使用 import                                      | 移除 import json                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | json 只在 orchestrator.py 使用，main.py 不需要 import                                                                                                                                                                                                                                                                                                                                    |
| save_results 寫入順序調整                                      | 先搬移 PDF，成功後才清除舊檔、寫入 md/json                                                                                                                                                                                                                                                                                                                                                                                                                                                               | 原本寫完 md/json 才搬移 PDF，搬移失敗會留下「摘要存在但 PDF 未入庫且 processed log 未記錄」的半完成狀態；調整順序後失敗時不留任何檔案殘留                                                                                                                                                                                                                                                |
| error_papers.md 錯誤描述依 failed_node 區分                    | write_dead_letter 改為根據 failed_node 產生對應描述（PDF 讀取失敗／論文分類失敗／摘要生成失敗）                                                                                                                                                                                                                                                                                                                                                                                                          | 原本一律寫死「LLM 呼叫失敗，已超過重試上限」，若實際失敗點是 extractor，訊息會誤導使用者排查方向                                                                                                                                                                                                                                                                                         |
| extractor shutil.move 加保護                                   | fitz.FileDataError 與純圖片 PDF 兩條路徑的 shutil.move 加上 try/except                                                                                                                                                                                                                                                                                                                                                                                                                                   | 原本搬移失敗（如 error 資料夾不存在）會直接中斷流程；加保護後印出警告並繼續，不影響後續論文的處理                                                                                                                                                                                                                                                                                        |
| 錯誤處理職責分離                                               | 新增 PaperState.permanent_error 欄位與 handle_permanent_error 節點；extractor 移除所有 I/O，只回報 failed_node 與 permanent_error；永久性錯誤由 orchestrator 統一處理（移動 PDF、寫 error log、跳過）                                                                                                                                                                                                                                                                                                    | 原本 extractor 自行處理永久性錯誤，等於另一套獨立的錯誤處理系統，與 orchestrator 的統一路由設計不一致；重構後 agent 只負責回報，orchestrator 負責所有錯誤收尾                                                                                                                                                                                                                            |
| save_results 全面加入 rollback 機制                            | 執行順序改為：寫 md → 寫 json → 搬移 PDF → 寫 processed_papers.md；用旗標追蹤每一步是否完成；FileNotFoundError（PDF 消失）：rollback md/json，回傳 `permanent_error=True` 路由到 handle_permanent_error；其他 Exception（I/O 暫時性錯誤）：rollback 所有已完成步驟（含把 PDF 搬回 input/），回傳 `permanent_error=False` 路由到 handle_error 進重試；route_after_save 新增 failed_node 路由到 handle_error；handle_error 的邊加入 save_results；write_dead_letter 的 node_descriptions 加入 save_results | 原本 PDF 搬移後的所有 I/O 操作無保護，任一失敗會讓程式崩潰，留下「PDF 已移走但 md/json/log 不完整」的半成功狀態且無法恢復；調整順序後，PDF 搬移前任何失敗都能 rollback，不留殘留；搬移後的 processed_papers.md 寫入失敗影響最小（md/json 與 PDF 均已完成），是最後一步                                                                                                                   |
| save_results 舊檔刪除移至成功路徑                              | 清除其他分類舊檔的邏輯從 try 區塊開頭移至所有步驟成功後；當前分類改為跳過（write_text 直接覆蓋，不需刪除）                                                                                                                                                                                                                                                                                                                                                                                               | 原本舊檔刪除在 try 區塊最前面，刪除後若後續步驟失敗，rollback 只能清除新寫的檔案，無法恢復已刪掉的舊有效輸出；rerun 一次失敗就可能讓原本正常的歷史摘要永久消失；移至成功路徑後，失敗時舊檔案完好，rollback 只清理本次新寫的殘留                                                                                                                                                          |
| write_dead_letter error_papers.md 補入實際錯誤訊息             | 格式從固定描述改為 `{節點泛化描述}：{state["error_message"]}`                                                                                                                                                                                                                                                                                                                                                                                                                                            | 原本 error_papers.md 只顯示「論文分類失敗，已超過重試上限」等固定字串，使用者看不到真正原因（如 LLM 回傳無效值、API 錯誤）；dead_letter.md 已有完整錯誤，error_papers.md 也應提供足夠資訊讓使用者判斷下一步                                                                                                                                                                              |
| handle_permanent_error 先寫 log 再搬移，依搬移結果決定是否結案 | 執行順序：先寫 error_papers.md → 再嘗試 shutil.move → 依結果分流。搬移成功：移除 papers_to_process、error_count+1、清空狀態（正式結案）。搬移失敗：補寫一筆技術錯誤至 error_papers.md、移除 papers_to_process（避免同一次執行無限迴圈）、但不增加 error_count（此篇未結案）、PDF 保留在 input/，下次 scan_papers 自然撿到重試                                                                                                                                                                            | 原本先搬移再寫 log，搬移失敗時 log 未寫入；且無論成功失敗都計入 error_count，等於把「搬移失敗、下次重試」的論文當成已結案處理。先寫 log 確保錯誤一定有記錄；以搬移結果決定是否結案，讓 error_count 真實反映已完成收尾的論文數；搬移失敗時的重複 log 代表重試次數，是預期行為                                                                                                             |
| init_paper 重置 permanent_error                                | init_paper 回傳加入 `"permanent_error": False`                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 原本 init_paper 只重置 retry_count、failed_node、error_message，沒有明確重置 permanent_error；雖然正常流程中前一篇的 handle_permanent_error 會將其設回 False，但此為隱性依賴；在 init_paper 明確重置，確保每篇論文開始時狀態乾淨                                                                                                                                                         |
| classifier 與 summarizer 錯誤回傳補齊 permanent_error          | LLM 例外處理的回傳 dict 加入 `"permanent_error": False`                                                                                                                                                                                                                                                                                                                                                                                                                                                  | 原本 classifier 和 summarizer 的例外回傳缺少 permanent_error，依賴 `**state` spread 的現有值；雖然正常流程中值為 False，但明確設定避免隱性依賴，與 extractor 的錯誤回傳格式一致                                                                                                                                                                                                          |
| 共用 append_log 工具函式                                       | 新增 `append_log(path, entry)` 函式，統一處理日期標題檢查與 append 邏輯；原本分散在 handle_permanent_error、write_dead_letter、rebuild_summaries、save_results 共 6 處的重複寫入邏輯全部改用此函式；日期標題格式統一為 `\n## {today}\n\n`；函式內建 `mkdir(parents=True, exist_ok=True)` 防禦                                                                                                                                                                                                            | 日期標題與 append 的 4 行邏輯重複出現多處，不同地方格式略有不一致；集中後只需維護一處，格式一致；save_results 的 processed_papers.md 原本只在第一篇論文時寫日期標題，改用 append_log 後每次都正確檢查，同時修正跨午夜執行時後續論文缺少日期標題的邊緣問題                                                                                                                                |
| rerun.py shutil.move 加錯誤處理                                | PDF 移回 input/ 的 shutil.move 加入 try/except，失敗時顯示友善訊息並回傳 False，不更新 processed_papers.md                                                                                                                                                                                                                                                                                                                                                                                               | 原本移動失敗會直接拋出 Python traceback，沒有友善提示；加保護後失敗訊息清楚，且 processed_papers.md 不會被錯誤清除                                                                                                                                                                                                                                                                       |
| main.py 移除重複 glob                                          | 改用單次 `sorted(INPUT_DIR.glob("*.pdf"))` 結果同時計算總數與傳入 scan_papers                                                                                                                                                                                                                                                                                                                                                                                                                            | 原本 scan_papers 掃一次、print 又呼叫 glob 掃一次，重複操作；統一為同一次掃描結果                                                                                                                                                                                                                                                                                                        |
| save_results markdown table pipe 字元跳脫 | 寫入 md 前先對所有 summary 欄位值執行 `.replace("\|", "\\|")`，同樣處理 `title`；使用 `s = {k: str(v).replace(...) for k, v in summary.items()}` 預處理，f-string 改用 `s.get(...)` | 若 LLM 回傳的摘要欄位（尤其 APA7 引用、主要發現）含有 `\|` 字元，直接插入 markdown table 會讓該列多出額外欄分隔符，格式靜默錯位；使用者若不看 raw markdown 難以察覺；跳脫後 `\|` 在 markdown 渲染為字面 pipe，不影響表格結構 |
| save_results 成功路徑明確重置 permanent_error | 成功 return 加入 `"permanent_error": False` | 原本成功路徑用 `{**state, ...}` spread，`permanent_error` 沿用 state 現有值；`route_after_save` 第一個判斷為 `if state["permanent_error"]`，若值為 True 會誤路由到 `handle_permanent_error`；目前安全（`init_paper` 保證為 False），但屬隱性依賴，未來若修改 `init_paper` 可能引入靜默誤判；明確設定後邏輯自文其義，與 `failed_node` / `error_message` 的清除模式一致 |
| rerun.py 執行後刪除舊 json/summary，確保總表即時一致 | 追蹤搜尋時命中的分類資料夾（`found_cls`）；成功移動 PDF 並清除 `processed_papers.md` 後，額外刪除 `output/{found_cls}/json/{stem}.json` 與 `output/{found_cls}/summary/{stem}.md`（`unlink(missing_ok=True)`，失敗只印警告）；僅限從 A1/A2/A3 找到的情況（`is_error=False`），`output/error/` 與 `input/` 不適用 | 原本 rerun 只移動 PDF 與清除 log，json/summary 殘留；`main.py` 啟動時呼叫 `rebuild_summaries`，殘留的 json 會讓已被 rerun 的論文繼續出現在 `summary_A*.md` 中，直到 main.py 執行完才消失；刪除後 rebuild 結果立即正確，使用者不會在重跑期間看到過期的總表條目 |
| rerun.py 一律同時清除兩份 log | 移除 `is_error` 分支邏輯；無論論文來自 A1/A2/A3、output/error/ 或 input/，一律同時嘗試清除 `processed_papers.md` 與 `error_filenames.md`；`found_cls` 判斷僅保留用於 json/summary 檔案刪除；同步移除未使用的 `ERROR_LOG` 變數（dead code） | 原本依 `is_error` 只清除單一 log；當 `save_results` rollback 失敗導致 PDF 卡在 `output/A1/pdf/`，且重試超限後 `write_dead_letter` 誤寫了 `error_filenames.md`，rerun 找到 A1/pdf/ 時走 `is_error=False` 路徑，只清 `processed_papers.md`，`error_filenames.md` 殘留，下次 `scan_papers` 仍排除該論文，使用者無法靠工具修復；改為一律雙清後，任何 log 狀態組合都能正確重置 |
| 費用定價改為可設定常數 | 在 `orchestrator.py` 頂端定義 `PRICE_INPUT_PER_M` 與 `PRICE_OUTPUT_PER_M`，預設值為目前模型定價，可在 `.env` 設定 `PRICE_INPUT` / `PRICE_OUTPUT` 覆寫；`save_results` 與 `main.py` 的費用計算改用這兩個常數；`main.py` import 這兩個常數，確保單篇與總計使用同一組定價 | 原本兩處費用計算均寫死 `* 2.5` 與 `* 10.0`；使用者在 `.env` 改用其他模型後，顯示費用可能嚴重失準；集中定義後只需調整一處（或在 `.env` 覆寫），且 import 保證兩處數字永遠一致 |
| 節點層級重試                                                   | 失敗時記錄 failed_node，orchestrator 路由回該節點重試，上限 3 次                                                                                                                                                                                                                                                                                                                                                                                                                                         | 節點重試比整篇重跑省時省 token，Extractor 成功的結果不需重跑                                                                                                                                                                                                                                                                                                                             |
| Dead Letter 機制                                               | 超過重試上限的論文寫入 logs/dead_letter.md，記錄 thread_id、failed_node、reason、retries                                                                                                                                                                                                                                                                                                                                                                                                                 | 與一般錯誤 log 分開，方便事後手動處理無法自動恢復的論文                                                                                                                                                                                                                                                                                                                                  |
| thread_id 設計                                                 | 格式：時間戳記-檔名（20260318-143022-paper_A）                                                                                                                                                                                                                                                                                                                                                                                                                                                           | 每篇論文任務唯一識別，方便追蹤處理紀錄                                                                                                                                                                                                                                                                                                                                                   |
| LLM 注入方式                                                   | classifier 與 summarizer 透過參數接收 llm_invoke，不在 agent 內建立 LLM                                                                                                                                                                                                                                                                                                                                                                                                                                  | LLM 設定集中在 main.py 管理，agent 本身不依賴具體模型                                                                                                                                                                                                                                                                                                                                    |
