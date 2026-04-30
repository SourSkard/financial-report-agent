---
name: teddy-financial-qa
description: Guide Codex/ChatGPT to build and maintain the Teddy Cup B financial QA project with consistent architecture, deliverables, and coding constraints.
---

# Teddy Financial QA Skill

## Scope

本 Skill 用于统一项目实现口径，避免任务链路和技术栈漂移。当前规则以 Task1 新主链路为准。

## Current Stack Baseline

### Task1（默认主链路）
- `pdfplumber`：逐页文本与基础版面信息。
- `pypdf`：文本兜底。
- `Camelot`：规则型财务表格抽取。
- `MinerU`（optional）：复杂表格/复杂版面兜底增强。
- `Docling`：不再是 Task1 默认主路径（deprecated/optional only）。

### Task2 / Task3（保持现状）
- Task2：结构化意图 -> 受约束 SQL -> 查询 -> 图表/导出。
- Task3：研报检索增强与 references 生成。

## Task1 Pipeline Contract

1. `parse pages`
- 输出页结构：`page_num`, `text`, `source`, `tables`（可选）。

2. `detect document type`
- 输出 `doc_type`：`annual_summary`, `quarterly_summary`, `annual_report`, `quarterly_report`, `research_report`, `other`。

3. `classify page`
- 输出 `page_type`：`cover`, `basic_info`, `kpi_table`, `financial_statement`, `shareholder_info`, `narrative_explanation`, `research_content`, `other`。

4. `route extractor`
- `summary_kpi_extractor`
- `full_report_extractor`
- `research_placeholder_extractor`
- `narrative_extractor`（可占位）
- `shareholder_extractor`（可占位）

5. `extract structured rows`
- 统一产出 RowDict 风格字段，禁止绕过后处理直接入库。

6. `normalize report period`
- `report_period` 规则：年度 `YYYY-12-31`；季度 `YYYYQ1~Q4`。

7. `cleaner / validator / loader`
- 所有数据统一进入 `mapper -> cleaner -> validator -> loader`。

## Extractor Responsibilities

- `summary_kpi_extractor`
  - 面向摘要财报（annual/quarterly summary）
  - 优先抽取核心指标并落表 `core_performance_indicators_sheet`

- `full_report_extractor`
  - 面向完整财报（annual/quarterly report）
  - 优先处理 `financial_statement` 页面
  - 接口需可扩展到三大报表

- `research_placeholder_extractor`
  - 识别到 `research_report` 时触发
  - 不写入 Task1 四张财务表

- `narrative_extractor` / `shareholder_extractor`
  - 可先占位，作为后续扩展点

## Boundaries

- 财报摘要：优先走 `summary_kpi_extractor`。
- 完整财报：优先走 `full_report_extractor`。
- 研报：不进入四张财务表。
- 不允许依赖文件名/公司名/股票代码/固定页号做核心分支判断。

## Deprecated Notes

以下描述已废弃，不应再作为默认实现：
- “Task1 默认走旧版可插拔解析器”
- “DocumentStream 是主通道”
- “某单一解析器是默认主链路”

## Consistent Terms

文档与代码统一使用以下术语：
- `doc_type`
- `page_type`
- `summary_kpi_extractor`
- `full_report_extractor`
- `research_report`
- `report_period`

## Minimal Run Commands

```bash
pip install -r requirements.txt
python scripts/run_task1.py --pdf "B题-示例数据/示例数据/附件2：财务报告/reports-上交所/600080_20230428_FQ2V.pdf" --max-pages 12 --timeout 120
python scripts/run_task1.py --pdf "B题-示例数据/示例数据/附件2：财务报告/reports-深交所/华润三九：2022年年度报告.pdf" --max-pages 20 --timeout 120
```
