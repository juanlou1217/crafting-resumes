# 多岗位方向版

状态：`draft_under_review`

披露范围：`private_review_draft`。以下内容仅用于当前会话私下审阅；公开投递前需确认可公开范围或脱敏口径。

你提供的是两个岗位名称，而不是完整 JD，因此以下为“岗位方向版”，不是 JD 定制版。`jd_mapping` 与 JD 匹配分均为 `N/A：未提供完整 JD`。

## 共同事实台账

| claim | source | status | time_window | personal_action | team_result | attribution | metric_definition | confidentiality | allowed_outputs | next_question |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 做过 SaaS 后台需求访谈 | 用户原话“做过SaaS后台需求访谈” | `confirmed` | 未知 | 做过 SaaS 后台需求访谈 | 未提供 | 仅确认做过该事项；职责强度、决策权及结果未知 | 未提供 | `needs_redaction` | `private_review_draft` | `null` |
| 做过 SQL 看板 | 用户原话“SQL看板” | `confirmed` | 未知 | 做过 SQL 看板 | 未提供 | 仅确认做过该事项；制作、维护或使用方式及结果未知 | 未提供 | `needs_redaction` | `private_review_draft` | `null` |
| 做过客户续费跟进 | 用户原话“客户续费跟进” | `confirmed` | 未知 | 做过客户续费跟进 | 未提供 | 仅确认做过跟进；不代表拥有续费目标、决策权或续费结果 | 未提供 | `needs_redaction` | `private_review_draft` | `null` |

## 产品经理方向证据映射

`jd_mapping`：`N/A：未提供完整 JD`

`keyword_evidence_map`：

| keyword | source | candidate_evidence | match_strength | allowed_surface | status |
| --- | --- | --- | --- | --- | --- |
| 需求访谈 | 产品经理岗位方向通用词；候选证据来源为用户原话 | 做过 SaaS 后台需求访谈 | `direct` | 相关经历首条 | `include` |
| SaaS 后台 | 候选证据来源为用户原话 | 做过 SaaS 后台需求访谈 | `direct` | 需求访谈所在 bullet | `include` |
| 客户续费跟进 | 候选证据来源为用户原话 | 做过客户续费跟进 | `direct` | 相关经历第二条 | `include` |
| SQL 看板 | 候选证据来源为用户原话 | 做过 SQL 看板 | `adjacent` | 相关经历第三条 | `deprioritize` |
| PRD、原型、需求优先级、产品决策 | 产品经理岗位方向通用词 | 无 | `none` | 仅列为缺口，不写入方向版 | `do_not_force` |
| 研发协作、验收、上线 | 产品经理岗位方向通用词 | 无 | `none` | 仅列为缺口，不写入方向版 | `gap` |

## 产品经理方向版

状态：`draft_under_review`

### 求职目标

产品经理

### 相关经历

- 做过 SaaS 后台需求访谈。
- 做过客户续费跟进。
- 做过 SQL 看板。

## 产品经理方向 weak/gap

- `weak`：需求访谈与产品方向直接相关，但目标用户、业务问题、本人职责、访谈方法及产出均未提供。
- `weak`：客户续费跟进可体现客户侧接触，但不能扩写为客户成功、续费所有权或业务闭环。
- `weak`：SQL 看板可作为相邻证据保留，但不能扩写为指标体系、产品决策或业务效果。
- `gap`：当前没有 PRD、原型、优先级取舍、研发协作、验收、上线及结果证据，不强行补写。

## 数据分析师方向证据映射

`jd_mapping`：`N/A：未提供完整 JD`

`keyword_evidence_map`：

| keyword | source | candidate_evidence | match_strength | allowed_surface | status |
| --- | --- | --- | --- | --- | --- |
| SQL 看板 | 数据分析师岗位方向通用词；候选证据来源为用户原话 | 做过 SQL 看板 | `direct` | 相关经历首条 | `include` |
| 需求访谈 | 候选证据来源为用户原话 | 做过 SaaS 后台需求访谈 | `adjacent` | 相关经历第二条 | `deprioritize` |
| 客户续费跟进 | 候选证据来源为用户原话 | 做过客户续费跟进 | `adjacent` | 相关经历第三条 | `deprioritize` |
| 指标定义、数据来源、数据清洗、查询方法、分析结论 | 数据分析师岗位方向通用词 | 无 | `none` | 仅列为缺口，不写入方向版 | `gap` |
| Python、BI 工具 | 数据分析师岗位方向通用词 | 无 | `none` | 仅列为缺口，不写入技能或经历 | `do_not_force` |
| 增长效果、决策效果 | 数据分析师岗位方向通用词 | 无 | `none` | 仅列为风险，不写入方向版 | `do_not_force` |

## 数据分析师方向版

状态：`draft_under_review`

### 求职目标

数据分析师

### 相关经历

- 做过 SQL 看板。
- 做过 SaaS 后台需求访谈。
- 做过客户续费跟进。

## 数据分析师方向 weak/gap

- `weak`：SQL 看板与数据方向直接相关，但不能据此推断是制作、维护还是使用，也不能补写指标口径、数据来源、分析方法或结论。
- `weak`：需求访谈可作为理解业务问题的相邻证据，但不能改写为数据需求分析。
- `weak`：客户续费跟进可作为业务场景相邻证据，但不能改写为续费数据分析或客户经营分析。
- `gap`：当前没有指标定义、数据清洗、查询方法、分析结论、建议采用及效果证据，不强行补写。
- `do_not_force`：未提供 Python 或具体 BI 工具，不能写入技能栏。

## 版本差异

| 事实 claim | 产品经理方向版：保留/顺序/措辞及原因 | 数据分析师方向版：保留/顺序/措辞及原因 | 不变的事实边界 |
| --- | --- | --- | --- |
| 做过 SaaS 后台需求访谈 | 首条保留，突出与产品需求场景的直接相关性；沿用“做过” | 第二条保留，作为业务问题理解的相邻证据；沿用“做过” | 不补参与、负责、推动或主导；不补 PRD、原型、决策、产出或结果 |
| 做过 SQL 看板 | 第三条保留，作为相邻的数据证据；沿用“做过” | 首条保留，突出与数据方向的直接相关性；沿用“做过” | 不解释为制作、维护或使用；不补指标体系、分析结论、Python、BI 或业务效果 |
| 做过客户续费跟进 | 第二条保留，突出客户侧接触；沿用“做过” | 第三条保留，作为业务场景相邻证据；沿用“做过” | 不补续费所有权、客户成功职责、续费结果或数据分析结论 |

## 风险与冲突

| type | affected_claim | source/status | impact | safe_action | blocking_scope |
| --- | --- | --- | --- | --- | --- |
| 信息缺口 | 全部三项事实 | 用户原话 / `confirmed` | 无公司、日期、正式岗位、具体方法及结果，当前只能形成简短方向版 | 省略未知字段，只保留原词事实 | 不阻断当前诚实方向版；阻断更强职责与结果表达 |
| 隐私边界 | 全部三项事实 | 用户原话 / `needs_redaction` | 未确认公开权限或脱敏口径 | 当前仅作 `private_review_draft` | 阻断最终公开简历、招聘沟通及正式投递 PDF |
| JD 缺失 | 两个岗位方向 | 仅提供岗位名称 | 无法做逐条 JD 映射、关键词覆盖或匹配评分 | 明确标为岗位方向版 | 阻断声称 JD 定制或给出 JD 匹配分 |
