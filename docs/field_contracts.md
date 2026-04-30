# 字段契约扩展方案（占位说明）

目的：为后续接入附件 3 的正式字段字典留出结构化入口，而不在代码中写死字段。

## 放置位置
- 规范描述：`docs/field_contracts.md`（当前文件）用于记录约定和版本说明。
- 配置入口：`app/schemas/field_map.py` 维护「解析字段 → 标准字段」的映射配置；后续可从外部 YAML/JSON 载入。

## 映射机制
1. 解析层（Docling/Marker 适配器）输出统一的原始字段键，如表名、行标题、值、单位、报告期等。
2. `table_mapper.map_tables()` 读取 `field_map.TABLE_FIELD_MAP`：按表名选择字段映射，将解析键转换为标准字段键（如 item → item_std），默认回退到最小字段集。
3. 新增正式字段时，只需在 `field_map.py`（或未来外部配置）补充映射，不必改核心逻辑。

## 迁移策略（最小 → 正式）
- 当前最小字段：`company`, `report_period`, `item`, `value`, `unit`, `source_path`, `created_at`
- 当引入正式字段：在 `field_map.py` 中为每张表定义字段字典（含必填/可选），映射函数会将缺失字段填 None，并保留最小字段以维持兼容。

## 解析适配器
- `pdf_parser.PdfParser` 可注入 backend（DoclingBackend/MarkerBackend），统一返回「表行」结构。
- 后续接入真实解析时，仅需实现 backend.parse(pdf_path) 返回标准原始行，不改管线。

## 校验扩展
- `validator.py` 支持注册规则钩子 `register_rule(callable)`，每条规则输入清洗后的记录，输出错误列表。
- 正式字段到位后，可逐步添加字段级/跨表一致性规则，无需修改现有最小校验。

## 待补资料
- 附件 3 字段字典（表名、字段英文/中文、数据类型、必填/可选、单位/币种规则、层级/节标题）。
- 真实样例 PDF/抽取结果，用于验证映射与校验。
