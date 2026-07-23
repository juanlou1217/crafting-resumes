# Crafting Resumes

> 把普通经历，变成可信、有说服力、经得住面试追问的求职简历。

Crafting Resumes 是一个以可核验事实为基础的 Codex Skill。它不会替你编造一段更漂亮的人生，而是通过逐问访谈、证据台账、岗位价值翻译和 JD 关键词映射，把真实经历中尚未表达出来的价值写清楚。

它支持包括中国大陆招聘流程在内的多种招聘语境，但品牌和 Skill 名称不绑定地区。不同地区、行业与岗位的经验用于选择更合适的提问、审查和表达方式，不能被当作候选人事实。

## 它解决什么问题

很多简历的问题并不是“经历不够好”，而是事实散落、职责边界不清、岗位语言没有对齐，或者为了显得有分量而越过了真实性边界。常见表现包括：

- 只写“做了什么”，没有说明对象、方法、交付物和岗位价值；
- 原始经历很普通或没有漂亮数字，不知道还能深挖什么；
- 面对 JD 时只会机械复制关键词，既不自然，也经不起追问；
- 把团队结果写成个人结果，或把参与、负责、推动和主导混为一谈；
- 同一份简历投多个岗位，内容没有侧重，事实却在版本间悄悄变化；
- 文案看起来流畅，但 ATS、HR 快速扫描和业务面试三关无法同时成立；
- 想保留自己的 Markdown、CSS 和 Obsidian 设置，却缺少可靠的 PDF 验收流程。

Crafting Resumes 先确定事实，再决定怎样表达。信息不足时，它会一次只问一个信息增益最高的问题；证据足够时，它直接推进，不用无意义的追问拖慢交付。

## 核心能力

- **经历深挖**：把模糊叙述拆成动作、对象、方法、协作、交付、变化和归因，以逐问访谈补齐真正影响下一步的证据。
- **事实台账**：记录每个 claim 的来源、确认状态、时间窗、个人动作、团队结果、指标口径、保密范围与允许输出，保证各版本共用同一事实底座。
- **JD 映射**：拆解岗位要求、权重与硬门槛，将候选人证据标为已覆盖、较弱、缺口或不应强写。
- **证据支持的专业包装**：在不改变事实、职责强度和结果归因的前提下，提高表达密度，翻译为目标岗位能识别的语言。
- **多视角审查**：分别从 ATS 命中、HR 快速扫描、业务面试追问、可信度、相关性和风险角度检查简历。
- **招聘沟通**：在用户明确请求且证据足够时，起草招聘平台开场白、猎头摘要、申请邮件或求职信；不会代替用户发送。
- **面试证据图**：把简历 claim 连接到来源、个人所有权、方法、取舍、指标与风险，帮助候选人准备真实可答的追问。
- **Obsidian 原生 PDF 验证交付**：沿用用户授权的 Markdown、CSS 与 Obsidian 设置，在隔离 Vault 中原生导出，并验证文本、链接、页数与逐页布局。

## 为什么它不只是“润色”

普通润色通常从一句现成文案出发，换词、缩句或增强语气。Crafting Resumes 从 claim 的资格开始判断：这件事是否发生、是谁做的、做到什么范围、结果属于个人还是团队、数字采用什么口径、可以披露到哪里。写作只发生在这些问题有了可追溯答案之后。

```text
用户材料
  → 事实原子与证据台账
  → 专业包装与高风险措辞证据门
  → JD / 关键词证据映射
  → 定向写作
  → ATS、HR、业务面试视角审查
  → 用户确认事实与拟交付文字
  → 文本交付或可选的原生 Obsidian PDF
```

这条链路让每个有分量的词都能回到证据。它也意味着“更专业”不等于“更夸张”：当证据只支持协作或参与时，系统会给出强而真实的表达，而不是把措辞升级成主导。

## 快速开始

安装并重启 Codex 后，可以显式调用：

```text
$crafting-resumes 我想从零深挖一段项目经历。请一次只问一个关键问题，先建立事实台账。
```

也可以带上现有材料和目标：

```text
$crafting-resumes 请诊断我明确提供的这份简历，并针对这份 JD 做证据映射。没有证据的关键词请标为 gap，不要强写。
```

如果已经确认了事实与披露范围，可以直接指定当前需要的产物：

```text
$crafting-resumes 基于这份已确认事实台账，生成产品岗位方向的私下可审阅稿、ATS 纯文本版和版本修改说明。
```

Skill 也能在请求明确涉及经历挖掘、简历诊断、JD 定制、招聘沟通、面试证据或 ATS 友好 PDF 时被隐式发现。显式调用更适合希望锁定工作方式和输出范围的场景。

## 典型工作流

### 从零深挖经历

提供一段自然叙述即可。Skill 先识别已知与未知，逐轮只问一个真正阻塞下一步的问题，建立证据台账后再形成候选表达，不会用占位符提前拼出一份假简历。

### 现有简历诊断

提供简历文本或明确授权的精确文件路径。Skill 检查时间线、职责强度、数字口径、重复信息、可读性和面试风险，并按当前证据给出修改优先级；没有 JD 时不会伪造匹配分。

### 单 JD 定制

提供一份 JD 和候选人材料。Skill 提取要求与权重，形成 JD 证据映射和完整关键词证据表，再按证据强弱决定保留、前置、降级或不写的内容。

### 多 JD 版本

多份 JD 共用一份事实台账，每个岗位分别映射、写作和审查。版本差异只改变选材、顺序与证据支持的措辞，不改变历史事实、贡献强度或数字口径。

### 招聘沟通与面试准备

在用户点名请求时，Skill 可以基于已确认事实起草沟通文案，并输出面试证据图。沟通草稿不会被当作已经发送的消息，面试图也不会替候选人编造答案。

### PDF 交付

先完成事实确认和拟交付文字确认，再按用户明确授权的 Markdown、CSS 与 Obsidian 设置准备隔离 Vault、执行原生导出和验收。只想评估逐字原稿布局时，可以走明确标记的未验证内容预览例外。

## 输出内容

输出由输入条件和用户目标决定，不为了“看起来完整”生成空壳栏目。

| 输入与目标 | 可能输出 |
| --- | --- |
| 原始经历或零散材料 | 事实台账、当前唯一问题、风险与冲突、候选表达 |
| 现有简历 | 结构与可信度诊断、修改优先级、私下可审阅稿 |
| 完整 JD + 候选证据 | JD 分析、JD 证据映射、`keyword_evidence_map`、定向简历、ATS 纯文本版 |
| 多份 JD | 共同事实台账、逐岗位映射与版本、版本差异表 |
| 完整交付请求 | 定向简历、ATS 版、修改说明、六维审查、面试证据图 |
| 明确点名的招聘沟通 | 招聘平台开场白、猎头摘要、申请邮件或求职信草稿 |
| 通过确认门且请求 PDF | 经原生 Obsidian 导出与自动/逐页验证的 PDF，或清楚说明未通过的原因 |

缺少 JD 时，Skill 可以做经历深挖、结构诊断和岗位方向表达，但不会冒充 JD 定制。只有 JD、没有候选人材料时，它可以拆解岗位和建议素材方向，但不会虚构候选人匹配结论。

## 合理包装与真实性边界

核心原则是：**反对事实造假，不反对专业包装**。专业包装可以改变信息密度、顺序、岗位语言和价值呈现，不能改变动作、时间线、工具、职责强度、数字、结果或归因。

允许的六类转换是：

1. **专业压缩**：把多个碎片事实压缩成一条清晰表达，不新增动作或结果。
2. **职责澄清**：根据本人动作、交付物和责任边界选择贡献动词，不自动升级职责。
3. **岗位语言翻译**：将同一动作、对象或方法翻译成目标岗位通用术语，不把相邻经验冒充直接经验。
4. **价值框架**：把已确认交付或变化连接到效率、质量、稳定性、体验、增长、成本或风险，不做无证据因果归因。
5. **结构优化**：按相关性组织动作、对象、方法与结果，不改写时间线。
6. **关键词对齐**：只插入与已确认 claim 直接匹配或语义等价的岗位词，不做隐藏词或堆词。

高价值措辞必须通过相应证据门：

| 措辞 | 最低证据 | 证据不足时的强而真实降级 |
| --- | --- | --- |
| `负责` | 直接承担清晰模块或交付物，并对计划、执行与交付负责 | `承担`、`参与`、`支持` |
| `推动` | 在负责基础上，有具体协调对象、解除阻碍的动作和实际进展 | `负责`、`协调`、`跟进` |
| `主导` | 在推动基础上，拥有关键决策权、推进节奏和结果责任 | `负责`、`推动`、`参与` |
| `从 0 到 1` | 确为新能力，并有关键阶段的端到端所有权和决策责任 | `参与搭建`、`负责其中环节` |
| `落地` | 已确认交付、采用、上线或投入使用的状态 | `完成`、`交付`、`试点` |
| `优化` | 有明确改善机制或共同口径的前后变化 | `改造`、`调整`、`完善` |
| `提升` / `降低` | 有指标定义、基线/对比、时间窗、来源和个人归因 | 只陈述已确认变化，不追加个人因果 |

证据不足时，Skill 不会停在一句“不能这样写”。它会逐项指出不能使用的 claim，给出只含已确认事实的有竞争力替代，并说明若要升级措辞还缺哪类证据。

### 示例一

- **已确认事实（before）**：本人对 3 个前端页面及其交互实现的计划、执行与交付负责，并与后端协作定位和修复接口缺陷；没有提供框架、流量、上线状态或效果数字。
- **专业表达（after）**：负责 3 个前端页面及交互实现，并与后端协作定位、修复接口相关缺陷。
- **插入关键词**：`前端页面`、`交互实现`、`接口协作`，它们分别直接对应交付物和已确认协作动作。
- **明确没有添加的信息**：没有补写 React/Vue、用户规模、性能提升、正式上线、团队领导或业务结果。

### 示例二

- **已确认事实（before）**：本人在项目组范围内调整既有构建脚本和发布检查清单；同一统计口径和时间窗内，发布流程的处理时间由约 2 天变为约 4 小时，记录确认该时间变化来自上述调整，但没有公司级推广或主导权证据。
- **专业表达（after）**：调整项目组构建脚本与发布检查清单，优化既有发布流程，将同口径处理时间从约 2 天缩短至约 4 小时。
- **插入关键词**：`发布流程优化`、`构建脚本`、`发布检查`；时间变化只用于已确认的项目组范围。
- **明确没有添加的信息**：没有写“主导”“从 0 到 1”“公司级平台”“全公司提效”，也没有把项目组变化扩大为组织级结果。

## 高价值关键词如何使用

选择顺序是：**JD 关键词优先，岗位词库补充，完成证据映射后再插入**。岗位词库只能帮助提问、选材与翻译，不能证明候选人做过相应工作。**禁止关键词堆砌**，同一个词优先放在证据最强、最自然的一处。

每次关键词优化都使用完整的六字段 `keyword_evidence_map`，它既记录为什么能写，也记录为什么不能写：

| 字段 | 含义 |
| --- | --- |
| `keyword` | JD 原词优先；无 JD 时才使用岗位通用词 |
| `source` | 关键词来源和候选证据的精确来源 |
| `candidate_evidence` | 对应的已确认 claim；没有证据时明确写“无” |
| `match_strength` | `direct`、`semantic_equivalent`、`adjacent` 或 `none` |
| `allowed_surface` | 可以出现的简历栏目、bullet，或只能进入风险/提问 |
| `status` | `include`、`deprioritize`、`gap`、`do_not_force` 或 `next_question` |

无证据的 JD 词必须标为 `gap` 或 `do_not_force`，必要且真正阻塞下一步时才标为 `next_question`。相邻经验不能伪装成直接经验；即使语义等价，职责和结果强度仍要单独过证据门。

## PDF 交付

PDF 是一个有门禁的可选交付阶段，不是收到简历后自动执行的一键转换。

1. 用户先明确授权要沿用的 Markdown、CSS 和 Obsidian 设置，以及允许读取和写入的精确路径。
2. 只有用户确认事实快照与拟交付文字后，才进入正式 PDF 流程。
3. Skill 在隔离 Vault 中准备内容，通过 Obsidian 自带的 **Export to PDF** 原生导出。
4. 导出后验证页数、A4/方向、必需与禁用文本、链接、中文字体和布局，并以原始清晰度逐页检查裁切、重叠、异常换行与空白页。
5. 自动检查或逐页检查任一失败，就不发布 PDF；合格的 Markdown 和 ATS 文本仍可继续交付。

唯一例外是用户明确要求把既有 Markdown 逐字原样导出，只用于评价样式。此时内容不能被编辑，必须标记为 `layout_preview_unverified_content`，也不能称为最终版或可投递版。

整个流程不使用第二套 Playwright、Pandoc、自建 HTML/CSS、浏览器打印或其他 renderer 兜底。仓库提供隔离准备与验证工具，但实际原生导出依赖用户本机已配置的 Obsidian 与验收环境，因此不会承诺在所有环境中自动生成 PDF。

## 隐私与权限

- 默认不扫描工作区、主目录、知识库、Obsidian Vault 或其他仓库。
- 只有用户明确授权的精确路径才可以读取；“你看看我的文件”不等于授权整个目录。
- 候选人材料按最小披露原则进入当前产物，私下审阅许可不自动升级为公开投递许可。
- 真实姓名、联系方式、简历、JD 私密副本、导出 PDF 和临时验收记录不应提交到本仓库。
- 本仓库只保存通用 Skill、匿名或合成测试资产和确定性工具；不包含真实简历、真实 PDF 验收产物或本机安装 manifest。

仓库架构和边界说明见 [docs/architecture.md](docs/architecture.md)。

## 安装、更新与卸载

公开仓库地址：[github.com/juanlou1217/crafting-resumes](https://github.com/juanlou1217/crafting-resumes)。

### 使用 Skill Installer 安装

在 Codex 中调用 Skill Installer，并明确仓库与 Skill 子目录：

```text
$skill-installer 从 GitHub 仓库 juanlou1217/crafting-resumes 的 skills/crafting-resumes 子目录安装
```

安装完成后重启 Codex，使其重新发现 Skill。

### 通过 SSH 手动安装

下面的命令把 Skill 安装到 `~/.codex/skills/crafting-resumes`。两个 absence guard 会同时拒绝已存在的目录和悬空符号链接，因此不会覆盖现有安装：

```bash
set -euo pipefail
SKILLS_ROOT="$HOME/.codex/skills"
SKILL_DIR="$SKILLS_ROOT/crafting-resumes"
test ! -e "$SKILL_DIR"
test ! -L "$SKILL_DIR"
git clone git@github.com:juanlou1217/crafting-resumes.git
mkdir -p "$SKILLS_ROOT"
cp -R crafting-resumes/skills/crafting-resumes "$SKILL_DIR"
```

### 更新

更新手动安装版本时，先更新源码，再用 `diff -qr` 比较 source 与 installed。先阅读差异；`diff` 返回 1 代表发现差异，并不代表文件损坏。

```bash
git -C crafting-resumes pull --ff-only
SKILLS_ROOT="$HOME/.codex/skills"
SKILL_DIR="$SKILLS_ROOT/crafting-resumes"
SOURCE_SKILL="$PWD/crafting-resumes/skills/crafting-resumes"
test -d "$SOURCE_SKILL"
test -d "$SKILL_DIR"
test ! -L "$SKILL_DIR"
diff -qr "$SOURCE_SKILL" "$SKILL_DIR"
```

确认差异符合预期后，再运行安全替换。命令先复制到不存在的暂存目录并逐文件验证，再把旧安装移动到不存在的备份目录；如果启用新目录失败，会尝试恢复旧安装。它不会静默覆盖已有暂存或备份：

```bash
set -euo pipefail
SKILLS_ROOT="$HOME/.codex/skills"
SKILL_DIR="$SKILLS_ROOT/crafting-resumes"
SOURCE_SKILL="$PWD/crafting-resumes/skills/crafting-resumes"
STAGED_DIR="$SKILLS_ROOT/.crafting-resumes.update"
BACKUP_DIR="$SKILLS_ROOT/.crafting-resumes.backup"
test "$(dirname "$SKILL_DIR")" = "$SKILLS_ROOT"
test "$(basename "$SKILL_DIR")" = "crafting-resumes"
test -d "$SOURCE_SKILL"
test -d "$SKILL_DIR"
test ! -L "$SKILL_DIR"
test ! -e "$STAGED_DIR"
test ! -L "$STAGED_DIR"
test ! -e "$BACKUP_DIR"
test ! -L "$BACKUP_DIR"
cp -R "$SOURCE_SKILL" "$STAGED_DIR"
diff -qr "$SOURCE_SKILL" "$STAGED_DIR"
mv "$SKILL_DIR" "$BACKUP_DIR"
if ! mv "$STAGED_DIR" "$SKILL_DIR"; then
  mv "$BACKUP_DIR" "$SKILL_DIR"
  exit 1
fi
```

确认新版本正常后再自行处理备份目录。更新完成后重启 Codex，使其重新发现新版本。

### 卸载

下面的命令只删除经过父目录、目录名、目录类型和非符号链接四重检查的安装目录。请先确认没有需要保留的本地修改；这是卸载示例，不会由本仓库自动执行。

```bash
set -euo pipefail
SKILLS_ROOT="$HOME/.codex/skills"
SKILL_DIR="$SKILLS_ROOT/crafting-resumes"
test "$(dirname "$SKILL_DIR")" = "$SKILLS_ROOT"
test "$(basename "$SKILL_DIR")" = "crafting-resumes"
test -d "$SKILL_DIR"
test ! -L "$SKILL_DIR"
rm -rf -- "$SKILL_DIR"
```

卸载后重启 Codex，使已移除的 Skill 不再出现在发现结果中。

## 开发与验证

开发命令都从仓库根目录运行。先创建隔离环境并安装开发依赖：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

运行全量单元测试：

```bash
.venv/bin/python -B -m unittest discover \
  -s tests/crafting-resumes \
  -p 'test_*.py'
```

运行 focused packaging validator。expected SHA 必须从冻结文件读取并显式传给 `--expected-skill-commit`：

```bash
EXPECTED_SKILL_COMMIT="$(
  tr -d '\n' \
    < tests/crafting-resumes/behavior/packaging-eval/expected-skill-commit.txt
)"
.venv/bin/python -B \
  tests/crafting-resumes/behavior/validate_packaging_eval.py \
  --expected-skill-commit "$EXPECTED_SKILL_COMMIT"
```

运行旧的完整行为资产 validator：

```bash
.venv/bin/python -B \
  tests/crafting-resumes/behavior/validate_eval_assets.py
```

计算可复现的 Skill tree hash：

```bash
.venv/bin/python -B \
  tests/crafting-resumes/hash_skill_tree.py \
  skills/crafting-resumes
```

运行 Codex system skill creator 的 `quick_validate.py`：

```bash
SKILL_CREATOR_ROOT="$HOME/.codex/skills/.system/skill-creator"
.venv/bin/python -B \
  "$SKILL_CREATOR_ROOT/scripts/quick_validate.py" \
  skills/crafting-resumes
```

`SKILL_CREATOR_ROOT` 不是本仓库路径；不同 Codex 安装可能位于其他位置。请把它改为本机 Codex system skill creator 的实际路径后再运行。

持续集成配置见 [.github/workflows/validate.yml](.github/workflows/validate.yml)。测试资产全部使用匿名或合成数据。

## FAQ

### 它会不会为了让简历好看而造假？

不会。只有已确认事实能进入拟交付简历；未确认事实、冲突、贡献升级、虚构指标和越权隐私都会阻断受影响的正式产物。它会继续提供证据支持的替代表达，而不是用夸张措辞绕过门禁。

### 没有数字，还能写出有价值的经历吗？

可以。数字不是价值的唯一证据。明确的交付物、复杂度、约束、协作对象、质量机制、风险处理、使用状态和决策取舍都可能形成有说服力的表达。没有可靠口径时不补数字，也不写示例数字占位。

### 必须提供 JD 吗？

不必须。没有 JD 时仍可做经历深挖、事实台账、结构诊断、通用岗位方向表达和面试证据准备；只是不会声称完成了 JD 定制或给出虚假的匹配分。

### 为什么一次只问一个问题？

一次一个高信息增益问题能降低回忆负担，也便于把新答案准确写回证据台账。只有缺口、冲突或隐私不确定性真正阻塞下一步时才提问；事实足够时不会机械追问。

### 它会自动生成 PDF 吗？

不会默认自动生成。正式 PDF 需要用户点名请求、授权精确路径、确认事实与拟交付文字，并具备本机 Obsidian 原生导出和验证环境。任一验收项失败都会停止发布，而不是切换到另一套渲染器。

### 支持哪些招聘语境和岗位？

核心流程不绑定地区，能够结合不同地区招聘语境；仓库内对中国大陆的 ATS、HR、业务面试和招聘沟通阶段提供了明确支持。岗位参考覆盖技术与数据、产品与交付、运营与商业、校招与实习、社招和转型场景。岗位参考只指导提问与选材，不会替用户生成经历。

### 能保留我自己的 Markdown、CSS 和 Obsidian 样式吗？

可以，但必须由你明确授权具体 Markdown、CSS、Obsidian 设置和精确路径。PDF 流程沿用这些输入，在隔离 Vault 中通过 Obsidian 原生导出；不会偷偷换成另一套主题或 HTML renderer。

## License

项目源码采用 [MIT License](LICENSE)。第三方改编来源及完整许可文本见 [THIRD_PARTY_NOTICES.md](skills/crafting-resumes/THIRD_PARTY_NOTICES.md)。
