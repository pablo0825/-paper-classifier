<!-- SPECTRA:START v1.0.1 -->

# Spectra Instructions

This project uses Spectra for Spec-Driven Development(SDD). Specs live in `openspec/specs/`, change proposals in `openspec/changes/`.

## Use `/spectra:*` skills when:

- A discussion needs structure before coding → `/spectra:discuss`
- User wants to plan, propose, or design a change → `/spectra:propose`
- Tasks are ready to implement → `/spectra:apply`
- There's an in-progress change to continue → `/spectra:ingest`
- User asks about specs or how something works → `/spectra:ask`
- Implementation is done → `/spectra:archive`

## Workflow

discuss? → propose → apply ⇄ ingest → archive

- `discuss` is optional — skip if requirements are clear
- Requirements change mid-work? Plan mode → `ingest` → resume `apply`

## Parked Changes

Changes can be parked（暫存）— temporarily moved out of `openspec/changes/`. Parked changes won't appear in `spectra list` but can be found with `spectra list --parked`. To restore: `spectra unpark <name>`. The `/spectra:apply` and `/spectra:ingest` skills handle parked changes automatically.

<!-- SPECTRA:END -->

## Commit Message 規範

依文章生命週期使用對應的 prefix：

| 階段 | 格式 | 說明 |
|------|------|------|
| 草稿 | `draft: 文章標題` | 第一次建立或初稿寫入 |
| 定稿 | `final: 文章標題` | 討論完成、準備發布 |
| 發布 | `publish: 文章標題` | 已發布到 Medium |
| 修改 | `revise: 文章標題` | 發布後的內容更動 |
| 維護 | `chore: 說明` | 專案設定、規範或非文章檔案的變更 |

commit 訊息的說明一律使用**繁體中文**。

## 協作規則

1. **逐段處理**：一次處理一段，展現思考過程，確認後再繼續
2. **禁止捏造**：數據、發現與引用必須來自文章或提供網址中明確記載的內容；若不確定，直接說不知道
3. **一問一答**：遇到需要討論多個問題時，改用一問一答模式，確認後再繼續，避免資訊量過多導致回答品質下降
4. **一步步思考**：在回答前先展示思考過程，確保每一步的推論都清楚可見
5. **主動釐清**：若 prompt 不清楚、不明確或模糊空間大，應要求說明，或透過持續討論明確使用者的意圖與目的，再開始執行
