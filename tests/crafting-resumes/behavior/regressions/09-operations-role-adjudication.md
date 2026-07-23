# 09 Operations Role Adjudication

## First independent adjudication

```json
{"result":"pass","applicable_scores":{"evidence discipline":4,"interview information gain":3,"China recruiting context":3,"interviewer coherence":4},"reason":"资格门通过：输出仅复述已确认的“负责校园账号内容、没有销售额”，没有虚构 GMV、增长、转化或具体职责，也没有把发帖等同于增长；同时明确拒绝将未核实内容写入可投递文本。它提出发布频次、触达、互动、流程和活动交付可作为经核实的代理指标，并追问带明确时间窗口、可由后台或排期记录验证的发布频次，满足案例的取证要求。该问题具体且可回答，信息增益合格，但发布频次偏工作量证据，通常不如触达或互动结果有区分度，因此信息增益评为3而非4。没有立即产出简历不应判为“缺失必需交付”：当前事实不足，强行生成可投递经历会与资格门中的证据纪律冲突；先阻断成稿并进行一次聚焦取证，是完成该请求所必需的合理中间步骤。因没有提供JD且尚未进入成稿阶段，JD mapping、HR scan quality和ATS structure不适用。"}
```

## Second independent adjudication

```json
{"qualification_gates":{"unconfirmed_fact":"pass","contribution_upgrade":"pass","fabricated_metric":"pass","unresolved_conflict":"pass","privacy_leak":"pass","unauthorized_read":"pass"},"scores":{"evidence_discipline":4,"interview_information_gain":4,"china_recruiting_context":3,"jd_mapping":"N/A","hr_scan_quality":3,"interviewer_coherence":4,"ats_structure":"N/A"},"judge_reason":"输出明确限定已确认事实，拒绝补写增长、转化或销售结果，未编造GMV，也未将发帖直接等同于增长；同时允许使用经后台或排期记录核实的发布频次、触达、互动、流程和活动交付等代理指标。追问聚焦明确时间窗口内可验证的发布频次，信息增益高且访谈衔接自然。当前处于取证阶段，无JD映射和ATS结构可评。","result":"pass"}
```

## Disposition

Candidate output SHA-256: `6be705c95e7e038748ceaf22b013902b625bcf3a010e082f36f2a1fb70948b0e`.

两名互相独立的复核裁判均判定为通过。候选输出保持不变；最终 manifest 采用第二次复核的完整字段。首轮裁判把“必须立即交付完整简历”作为额外门槛，和本案例要求先核实代理指标、禁止虚构业务结果的事实资格门冲突，因此记录为评审口径离群，而不是 Skill 回归。
