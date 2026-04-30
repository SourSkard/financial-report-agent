# Teddy Financial QA

泰迪杯 B 题《上市公司财报“智能问数”助手》项目。数据库统一路径：`db/app.db`。

## 项目概述

- Task1：从财务报告 PDF 抽取结构化财务数据，清洗校验后入库。
- Task2：面向数据库问答（NL2SQL + 图表 + 结果导出）。
- Task3：研报增强问答与引用追溯（RAG + references）。
- 当前重心：Task1 财报结构化抽取链路稳定性与可观测性。

## Task1 新主链路（默认）

- 页面文本与基础结构：`pdfplumber`（主） + `pypdf`（文本兜底）。
- 规则型表格抽取：`Camelot`（在 `kpi_table` / `financial_statement` 页触发）。
- 复杂版面兜底：`MinerU`（可选增强，未配置时优雅降级）。
- `Docling`：不再是 Task1 默认主路径；仅可视为可选/废弃兼容方案。

## Task1 架构说明

1. 页面解析层（Page Parsing Layer）
- 逐页产出 `page_num + text + source + tables`。
- 不能因为某个后端失败而整页为空；至少保留文本。

2. 文档理解层（Document Understanding Layer）
- `detect_document_type(pages)`：判定 `doc_type`。
- `classify_page(page)`：判定 `page_type`。

3. 路由层（Extractor Routing Layer）
- `annual_summary` / `quarterly_summary` -> `summary_kpi_extractor`
- `annual_report` / `quarterly_report` -> `full_report_extractor`
- `research_report` -> `research_placeholder_extractor`
- 其他页可走 `narrative_extractor` / `shareholder_extractor`（占位可扩展）

4. 结构化后处理层
- 所有抽取结果统一走：`mapper -> cleaner -> validator -> loader`。
- 不允许 extractor 直接绕过后处理入库。

## 报告类型（doc_type）

- `annual_summary`
- `quarterly_summary`
- `annual_report`
- `quarterly_report`
- `research_report`
- `other`

## 页类型（page_type）

- `cover`
- `basic_info`
- `kpi_table`
- `financial_statement`
- `shareholder_info`
- `narrative_explanation`
- `research_content`
- `other`

## report_period 规则

- 年度：`YYYY-12-31`
- 季度：`YYYYQ1` / `YYYYQ2` / `YYYYQ3` / `YYYYQ4`
- 优先来源：表标题 > 列头 > 页内上下文 > 封面/基本信息页
- 不优先使用文件名中的披露日期作为 `report_period`

## 安装与依赖

```bash
pip install -r requirements.txt
```

- Camelot 运行可能需要系统依赖（如 Ghostscript 等）。
- MinerU 为可选增强，未安装或未配置时会自动降级，不阻断 Task1 主链路。

## 运行示例

样本 A（上交所摘要样本）：

```bash
python scripts/run_task1.py --pdf "B题-示例数据/示例数据/附件2：财务报告/reports-上交所/600080_20230428_FQ2V.pdf" --max-pages 12 --timeout 120
```

样本 B（深交所完整年报样本）：

```bash
python scripts/run_task1.py --pdf "B题-示例数据/示例数据/附件2：财务报告/reports-深交所/华润三九：2022年年度报告.pdf" --max-pages 20 --timeout 120
```

## 验收预期

- 样本 A：应识别为 `annual_summary`，优先路由 `summary_kpi_extractor`，核心指标进入 `core_performance_indicators_sheet`。
- 样本 B：应识别为 `annual_report`，优先路由 `full_report_extractor`，不误走摘要路径。
- `research_report`：不应进入 Task1 四张财务表，仅保留占位/文本供后续任务使用。

## Task1 四张财务表

- `core_performance_indicators_sheet`
- `balance_sheet`
- `cash_flow_sheet`
- `income_sheet`
