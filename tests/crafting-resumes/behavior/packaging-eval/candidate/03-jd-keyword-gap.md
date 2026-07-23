状态：`draft_under_review`

结论：当前不能把 Kubernetes 或 K8s 写入技能、个人概况、项目经历、工作经历或 ATS 隐藏词；“了解 Kubernetes”也没有学习证据支撑。React 可以保留，但不能被包装成 Kubernetes、容器编排或集群部署经验。

## JD 证据映射

| jd_original | requirement_type | weight | candidate_evidence | source | status | reason | resume_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kubernetes 为必备技能 | hard_requirement | high（JD 明确列为必备） | 无 | 用户明确确认没有 Kubernetes 学习、项目或工作证据 | gap | React 页面开发与 Kubernetes 不属于语义等价经验，不能替代该硬性要求 | omit |

## keyword_evidence_map

| keyword | source | candidate_evidence | match_strength | allowed_surface | status |
| --- | --- | --- | --- | --- | --- |
| Kubernetes | 目标 JD 的必备技能；用户明确确认无相关证据 | 无 | none | 仅用于内部缺口与求职风险说明，不进入简历正文或隐藏关键词 | gap |
| React | 用户原话：“有 React 页面开发经历” | React 页面开发经历 | direct | 核心技能；对应真实经历中的页面开发表述 | include |

## 可采用的关键词写法

核心技能：

`React（页面开发）`

经历中的安全表达可选：

- `React 页面开发`
- `前端页面开发（React）`

不要补写“熟练掌握 Kubernetes”“了解 Kubernetes”“Kubernetes 实战”“容器编排”“集群部署”等表述。由于 Kubernetes 是必备项，这仍是可能触发筛选的高权重缺口，关键词优化无法替代真实证据。
