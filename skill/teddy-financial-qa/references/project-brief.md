# Teddy Cup B 项目简述（统一版）

## 1. 项目目标

泰迪杯 B 题《上市公司财报“智能问数”助手》，包含三条任务链路：

1. Task1：财报 PDF 结构化抽取与入库（四张财务表）
2. Task2：自然语言问数（受约束 NL2SQL）
3. Task3：研报增强问答与 references

当前工程优先级：先稳住 Task1 数据底座，再扩展 Task2/Task3。

## 2. Task1 当前默认技术栈

- 页面解析：`pdfplumber`（主） + `pypdf`（文本兜底）
- 表格抽取：`Camelot`（规则型）
- 复杂页增强：`MinerU`（可选，未配置时优雅降级）
- `Docling`：不再是 Task1 默认主路径（仅 optional/deprecated）

## 3. Task1 处理流程

1. parse pages
2. detect `doc_type`
3. classify `page_type`
4. route extractor
5. extract structured rows
6. normalize `report_period`
7. mapper -> cleaner -> validator -> loader

## 4. 文档类型与边界

`doc_type` 至少包括：
- `annual_summary`
- `quarterly_summary`
- `annual_report`
- `quarterly_report`
- `research_report`
- `other`

边界规则：
- 摘要财报优先抽核心指标。
- 完整财报优先走报表路径。
- `research_report` 不进入 Task1 四张财务表。

## 5. report_period 规则

- 年度：`YYYY-12-31`
- 季度：`YYYYQ1~Q4`
- 优先从表标题/列头/页内上下文提取，不优先依赖文件名披露日期。

## 6. 运行与依赖

```bash
pip install -r requirements.txt
```

样本 A：

```bash
python scripts/run_task1.py --pdf "B题-示例数据/示例数据/附件2：财务报告/reports-上交所/600080_20230428_FQ2V.pdf" --max-pages 12 --timeout 120
```

样本 B：

```bash
python scripts/run_task1.py --pdf "B题-示例数据/示例数据/附件2：财务报告/reports-深交所/华润三九：2022年年度报告.pdf" --max-pages 20 --timeout 120
```

Camelot 可能需要系统依赖；MinerU 未配置时不会阻断主链路。
