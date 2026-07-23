# Architecture

## Objective

Crafting Resumes（`crafting-resumes`）将求职简历制作拆为路由、证据、专业包装、岗位语境、写作审查和交付职责。主入口只负责资格门与渐进路由；较重的规则和岗位知识按当前阶段加载。中国大陆等地区招聘经验是可选语境，不进入品牌名称，也不构成候选人事实。

## Layers

1. **Router** — `SKILL.md` 定义触发范围、真实性与隐私门禁、引用顺序和最终交付门禁。
2. **Evidence core** — 状态机、证据台账、冲突处理、隐私边界和逐问访谈共同决定哪些 claim 可以进入候选表达。
3. **Packaging reference** — `references/professional-packaging-and-keywords.md` 位于证据层和写作层之间，把已确认 claim 转换为证据允许的最高强度表达；它定义六类合理转换、高风险措辞证据门、强而真实的降级和完整关键词证据映射。
4. **Recruiting and JD context** — 地区招聘流程、JD 映射以及技术、产品、运营、商业、校招和转型岗位打法提供选材、提问和排序方向，不提供候选人事实，也不能越过 packaging 证据门。
5. **Writing, review, and output contracts** — 写作规则、审查量表与输出合同共同约束定向简历、ATS 文本、招聘沟通、面试证据图、版本差异和风险报告；只有当前输入适用的产物才会出现。
6. **PDF delivery** — 两个确定性 Python 工具只负责准备隔离 Obsidian Vault 和验证导出的 PDF；Obsidian 桌面端是唯一渲染器，自动检查后仍须逐页视觉验收。

## Shared keyword interface

六字段 `keyword_evidence_map` 是 JD 映射、写作、审查和输出合同共享的接口：

```text
keyword
source
candidate_evidence
match_strength
allowed_surface
status
```

JD 映射负责给出关键词来源、权重和候选证据关系；packaging reference 负责匹配强度、允许表面和高风险措辞资格；写作只消费 `include` 或证据允许的降级项；审查检查职责强度、相邻经验冒充和关键词堆砌；输出合同保证六个字段完整保留。没有证据的词仍进入接口，但必须标为 `gap`、`do_not_force` 或必要时的 `next_question`，不能悄悄写进简历。

## Data flow

```text
用户材料或 JD
  → 输入模式识别
  → 证据台账、冲突与隐私范围
  → 单问题经历访谈（仅在关键信息阻塞时）
  → packaging reference（六类转换与高风险措辞证据门）
  → JD / 岗位映射与六字段 keyword_evidence_map
  → 草稿、审查、输出选择与面试风险
  → 用户确认事实快照和拟交付文字
  → 可投递文本或经验证的原生 Obsidian PDF
```

## Qualification gates

真实性与隐私是资格门禁，而不是可由文笔抵消的评分项。未确认事实、贡献升级、虚构指标、未解决冲突、隐私泄漏和未授权读取任一失败时，受影响的最终交付必须停止。普通 `weak` 或 `gap` 不阻断强而真实的降级版本。

## Progressive loading

经历深挖通常只需要状态机、证据和访谈引用；专业包装在任何写作、关键词优化或 JD 语言翻译之前加载；地区与岗位语境、JD、写作、审查及 PDF 模块只在对应阶段加载。这使入口保持简短，也避免无关参考覆盖当前证据边界。

## Repository boundary

仓库只保存通用 Skill、确定性工具、匿名或合成行为样例和测试。真实候选人简历、联系方式、候选人文件路径、真实导出 PDF、浏览器或 Obsidian 状态、本机安装 manifest 与本地真实验收记录必须保留在仓库之外。

## Verification

- 单元测试验证 PDF 准备器、PDF 验证器、行为资产合约、公开 README 合同、包结构、第三方许可和确定性树哈希。
- 十二个冻结行为场景覆盖普通项目、过度包装压力、冲突与隐私、JD/简历单边输入、多 JD、转型和多类岗位。
- 四个 focused packaging 场景验证合理表达、高风险动词、无证据 JD 词和有证据关键词。
- 候选行为不得相对无 Skill 基线产生资格门禁回归。
