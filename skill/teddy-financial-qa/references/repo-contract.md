# 仓库约束与开发合同

## 1. 默认目录

```text
teddy-financial-qa/
  app/
    pipelines/
    services/
    prompts/
    schemas/
    storage/
    utils/
  data/
    raw/
    interim/
    processed/
  db/
  kb/
  result/
  tests/
  scripts/
  docs/
  streamlit_app.py
```

## 2. 放置规则

- `app/pipelines/`：任务一、任务二、任务三的主链路编排
- `app/services/`：文档解析、SQL 生成、图表生成、RAG 检索等服务
- `app/prompts/`：结构化意图、澄清、归因等提示词模板
- `app/schemas/`：Pydantic / SQLModel / JSON Schema
- `app/storage/`：数据库访问、向量库访问、文件存储逻辑
- `app/utils/`：通用工具
- `scripts/`：批量执行、初始化、导出、测试日一键运行
- `tests/`：单元测试和样例测试
- `docs/`：说明文档、流程图、答辩材料草稿
- `result/`：比赛要求的图片和 Excel 输出

## 3. 文件组织规则

- 不把核心逻辑写在 notebook
- 不把 SQL、Prompt、Schema 混在一个文件里
- 一类职责一个模块
- 每个 pipeline 都应有明确输入和输出

## 4. 分层原则

- **解析层**：负责 PDF / Excel → 中间结构
- **清洗层**：负责标准化和校验
- **数据层**：负责 SQLite / MySQL / Qdrant
- **推理层**：负责意图、SQL、RAG、归因
- **展示层**：负责 Streamlit 演示和结果导出

## 5. 输出契约

必须稳定支持：
- `result_2.xlsx`
- `result_3.xlsx`
- `result/` 图表图片
- JSON 响应结构
- references 字段

## 6. 版本与依赖原则

- 比赛期间固定依赖版本
- 测试日不升级依赖
- 先跑通小样本，再扩展全量
- 有替补方案的模块要保留 fallback 说明

## 7. 实现优先级

1. 任务一数据底座
2. 任务二稳定回答
3. 任务三归因增强
4. Streamlit 演示
