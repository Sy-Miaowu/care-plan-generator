# Care Plan 自动生成系统 Design Doc

## 1. 背景

CVS 的医疗工作者在开药或处理药房订单时，需要为患者生成 care plan。当前流程由药剂师人工查看患者病史、诊断、用药历史和患者记录后撰写，单个患者通常需要 20-40 分钟。

该流程是合规和报销所需，影响 Medicare 与 pharma 报告。由于人手不足，人工生成 care plan 已造成积压。

本系统面向 CVS 内部医疗工作者使用，患者不会直接接触系统。医疗工作者生成 care plan 后，会下载、打印或上传到现有系统，并可导出报告用于 pharma reporting。

## 2. 目标

系统需要提供一个端到端可运行的 Web 工具，支持医疗助理录入患者、Provider、订单和患者记录信息，并自动生成可下载的 care plan。

核心目标：

- 通过结构化表单收集 care plan 所需输入
- 对所有输入字段进行严格校验
- 检测患者、订单和 Provider 的重复或冲突情况
- 调用 LLM 根据临床信息生成 care plan
- 支持 care plan 文本文件下载
- 支持导出 pharma reporting 所需数据
- 保证关键一致性规则不可绕过
- 代码模块化、可测试、可本地端到端运行

## 3. 非目标

以下内容不在当前版本范围内：

- 患者自助访问或患者门户
- 自动写回 CVS 现有内部系统
- 自动提交 Medicare 或 pharma 报销材料
- 完整 EHR 集成
- 复杂权限体系和多组织租户隔离
- 对 LLM 输出进行医疗合规最终判定

care plan 仍应由医疗工作者在实际使用前审阅。

## 4. 用户与使用场景

主要用户是 CVS 的医疗工作者，包括医疗助理和药剂师。

典型流程：

1. 医疗工作者打开 Web 表单
2. 输入患者基本信息、Provider 信息、诊断、药物、用药历史和患者记录
3. 系统执行字段校验和重复检测
4. 如果存在阻断性错误，用户必须修正后才能继续
5. 如果存在 warning，用户可确认后继续
6. 系统调用 LLM 生成 care plan
7. 用户下载 care plan 文本文件
8. 用户按需导出 reporting 文件

## 5. 关键业务规则

### 5.1 Care Plan 规则

- 一个 care plan 对应一个订单
- 一个订单对应一种药物
- care plan 输出必须包含以下部分：
  - Problem list
  - Goals
  - Pharmacist interventions
  - Monitoring plan

### 5.2 重复检测规则

| 场景 | 处理方式 | 原因 |
| --- | --- | --- |
| 同一患者 + 同一药物 + 同一天 | ERROR，必须阻止 | 高置信度重复提交 |
| 同一患者 + 同一药物 + 不同天 | WARNING，可确认继续 | 可能是续方 |
| MRN 相同 + 名字或 DOB 不同 | WARNING，可确认继续 | 可能是录入错误 |
| 名字 + DOB 相同 + MRN 不同 | WARNING，可确认继续 | 可能是同一患者 |
| NPI 相同 + Provider 名字不同 | ERROR，必须修正 | NPI 是 Provider 唯一标识 |

### 5.3 Provider 规则

- Provider 应只在系统中录入一次
- NPI 是 Provider 的唯一业务标识
- 同一个 NPI 不允许绑定不同 Provider 名字
- 新订单引用已有 Provider 时，应复用已有 Provider 记录

## 6. 输入字段

### 6.1 Patient

| 字段 | 类型 | 校验 |
| --- | --- | --- |
| First Name | string | 必填，非空 |
| Last Name | string | 必填，非空 |
| Date of Birth | date | 必填，不能是未来日期 |
| MRN | string | 必填，唯一 6 位数字 |
| Primary Diagnosis | string | 必填，ICD-10 格式 |
| Additional Diagnosis | list<string> | 可为空，每项必须是 ICD-10 格式 |

### 6.2 Provider

| 字段 | 类型 | 校验 |
| --- | --- | --- |
| Referring Provider | string | 必填，非空 |
| Referring Provider NPI | string | 必填，10 位数字 |

### 6.3 Order / Medication

| 字段 | 类型 | 校验 |
| --- | --- | --- |
| Medication Name | string | 必填，非空 |
| Order Date | date | 必填，默认当天 |
| Medication History | list<string> | 可为空，每项非空 |

### 6.4 Patient Records

| 字段 | 类型 | 校验 |
| --- | --- | --- |
| Patient Records | string 或 PDF | 必填，必须能被系统读取 |

PDF 文档需要被提取为文本后再传给 care plan 生成模块。

## 7. 数据模型

建议的核心实体：

### Patient

- id
- first_name
- last_name
- date_of_birth
- mrn
- primary_diagnosis
- additional_diagnoses
- created_at
- updated_at

唯一性约束：

- mrn 唯一

辅助索引：

- first_name + last_name + date_of_birth

### Provider

- id
- name
- npi
- created_at
- updated_at

唯一性约束：

- npi 唯一

### Order

- id
- patient_id
- provider_id
- medication_name
- medication_history
- order_date
- patient_record_text
- created_at
- updated_at

唯一性和重复检测：

- patient_id + normalized_medication_name + order_date 用于阻断同日重复订单
- patient_id + normalized_medication_name 用于检测不同日期的潜在续方

### CarePlan

- id
- order_id
- content
- llm_model
- generation_status
- generated_at
- created_at
- updated_at

约束：

- 一个 order 最多对应一个 active care plan

## 8. 系统架构

建议按以下模块组织：

- Web Form UI：负责用户输入、前端基础校验、展示 error/warning、下载文件和导出报告
- API Layer：负责接收请求、返回结构化错误、协调业务流程
- Validation Module：负责字段格式校验
- Integrity Rules Module：负责跨实体一致性和重复检测
- Provider Service：负责 Provider 创建、查找和复用
- Patient Service：负责 Patient 创建、查找和冲突检测
- Order Service：负责订单创建和重复检测
- Care Plan Generator：负责组装 prompt、调用 LLM、校验输出结构
- Export Service：负责生成 reporting 文件
- Persistence Layer：负责数据库读写

## 9. 核心流程设计

### 9.1 创建订单并生成 Care Plan

1. 用户提交表单
2. API 执行字段级校验
3. 系统查找或创建 Provider
4. 系统查找或创建 Patient
5. 系统执行患者和订单重复检测
6. 如果存在 ERROR，返回错误并阻止创建
7. 如果存在 WARNING，返回 warning，要求用户确认
8. 用户确认后再次提交
9. 系统创建 Order
10. 系统提取或整理 patient records
11. 系统调用 LLM 生成 care plan
12. 系统校验 LLM 输出是否包含必需 section
13. 系统保存 CarePlan
14. 用户下载文本文件

### 9.2 Warning 确认机制

对于可继续的 warning，API 应返回明确的 warning code 和 message。用户确认后，前端再次提交请求，并附带 confirmed_warning_codes。

后端必须重新执行完整校验，不能只相信前端状态。只有请求中确认过的 warning 才允许继续。

### 9.3 Reporting 导出

导出报告应支持按时间范围筛选，至少包含：

- Patient MRN
- Patient name
- DOB
- Provider name
- Provider NPI
- Medication name
- Primary diagnosis
- Additional diagnoses
- Order date
- Care plan generated timestamp

导出格式建议优先支持 CSV，后续可扩展 XLSX。

## 10. LLM 生成设计

### 10.1 输入

LLM prompt 应包含：

- 患者姓名
- DOB
- MRN
- Primary diagnosis
- Additional diagnoses
- Medication name
- Medication history
- Patient record text
- 固定输出结构要求

### 10.2 输出结构

LLM 输出必须是可读文本，并包含：

```text
Problem list
Goals
Pharmacist interventions
Monitoring plan
```

### 10.3 安全和质量控制

- 不允许 LLM 修改原始结构化输入
- patient records 中提取的内容应作为上下文，不作为数据库事实自动覆盖字段
- LLM 输出缺少必需 section 时，应返回生成失败或触发重试
- 错误信息不能暴露敏感内部 prompt、API key 或 stack trace
- care plan 应标记为由系统生成，并由医疗工作者审阅

## 11. 错误与 Warning 设计

### Error

Error 表示请求不能继续，用户必须修改输入。

示例：

- INVALID_NPI
- INVALID_MRN
- INVALID_ICD10_CODE
- DUPLICATE_ORDER_SAME_DAY
- PROVIDER_NPI_NAME_CONFLICT
- PATIENT_RECORD_UNREADABLE

### Warning

Warning 表示存在风险，但用户确认后可以继续。

示例：

- POSSIBLE_REFILL_ORDER
- MRN_MATCH_NAME_OR_DOB_MISMATCH
- NAME_DOB_MATCH_MRN_MISMATCH

所有错误和 warning 都应包含：

- code
- field，可选
- message
- severity
- blocking

## 12. API 草案

### POST /orders/validate

校验表单输入并返回 errors / warnings，不创建订单。

### POST /orders

创建订单并生成 care plan。

请求可包含 confirmed_warning_codes。

### GET /care-plans/{id}/download

下载 care plan 文本文件。

### GET /reports/pharma-export

按时间范围导出 pharma reporting 文件。

### GET /providers/search

按 NPI 或名字搜索 Provider，减少重复录入。

## 13. 测试策略

必须覆盖：

- 字段格式校验
- ICD-10、MRN、NPI 校验
- Provider NPI 冲突
- 同日同患者同药物重复订单阻断
- 不同日期同患者同药物 warning
- MRN 相同但姓名或 DOB 不同 warning
- 姓名和 DOB 相同但 MRN 不同 warning
- warning 确认后可以继续
- 未确认 warning 时不能继续创建
- LLM 输出缺少必需 section 时失败或重试
- pharma report 导出字段完整性

建议测试层级：

- Unit tests：Validation 和 Integrity Rules
- Integration tests：创建订单、生成 care plan、导出报告
- End-to-end smoke test：项目启动后可完成一次完整 care plan 生成流程

## 14. 生产就绪要求

系统上线前必须满足：

- 所有输入都有后端校验
- 关键一致性规则在后端强制执行
- 数据库唯一约束保护 Provider NPI 和 Patient MRN
- 错误清晰、安全、不会泄漏内部实现
- 代码模块边界清楚，业务规则集中管理
- 关键逻辑有自动化测试
- 本地环境可一键启动
- 项目具备基础 seed 或示例数据
- 端到端流程可通过 README 复现

## 15. 风险与待确认问题

### 风险

- LLM 可能生成不完整或不准确的 care plan
- PDF 文本提取质量可能影响生成结果
- ICD-10 格式校验不能等同于医学合理性校验
- 现有 CVS 工作流和外部系统格式可能对导出字段有额外要求
- PHI 数据处理需要符合内部安全和合规要求

### 待确认问题

- care plan 文本文件是否需要固定模板或品牌格式
- pharma reporting 的最终字段和文件格式
- 是否需要记录用户确认 warning 的审计日志
- 是否需要区分医疗助理和药剂师权限
- 是否需要保存 LLM prompt 和响应用于审计
- 是否需要支持重新生成 care plan
- 是否需要支持同一个 order 多版本 care plan

