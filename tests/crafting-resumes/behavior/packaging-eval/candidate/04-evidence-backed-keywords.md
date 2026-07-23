状态：`draft_under_review`

披露范围：`private_review_draft`（公开投递前需确认公开或脱敏边界）

## 关键词证据映射

| keyword | source | candidate_evidence | match_strength | allowed_surface | status |
| --- | --- | --- | --- | --- | --- |
| 发布流程改造 | 用户原话：“我负责发布流程改造” | 负责发布流程改造 | direct | 简历 bullet | include |
| 跨团队协调 | 岗位通用词；用户原话：“协调开发、测试和运维确定方案与切换窗口” | 协调开发、测试和运维确定方案与切换窗口 | semantic_equivalent | 简历 bullet | include |
| 方案与切换窗口 | 用户原话：“协调开发、测试和运维确定方案与切换窗口” | 与开发、测试和运维共同确定方案与切换窗口 | direct | 简历 bullet | include |
| 正式采用 | 用户原话：“新流程已被团队正式采用” | 新流程已被团队正式采用 | direct | 简历 bullet | include |
| 发布周期优化 | 岗位通用词；用户原话：“发布周期从平均 2 天降到 4 小时”，并确认统计口径 | 同类版本从提测完成到生产发布的平均时间由 2 天缩短至 4 小时 | semantic_equivalent | 简历 bullet | include |
| 推动 | 岗位通用词 | 已确认负责流程改造、协调相关团队并获正式采用，但未确认识别并解除具体阻碍 | adjacent | 仅风险说明 | do_not_force |
| 主导 | 岗位通用词 | 已确认“负责”及协调动作，但未确认关键方案取舍的决策责任、推进节奏和结果责任 | adjacent | 仅风险说明 | do_not_force |
| 提升或降低 | 岗位通用结果词 | 已确认同口径周期变化，但未确认该变化可归因于个人动作 | adjacent | 仅风险说明；bullet 只陈述变化 | do_not_force |

## 简历 bullet

- 负责发布流程改造，协调开发、测试和运维确定方案与切换窗口；新流程已被团队正式采用；按同类版本从提测完成到生产发布的平均时间统计，发布周期由 2 天缩短至 4 小时。
