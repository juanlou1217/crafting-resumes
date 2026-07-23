# Crafting China Resumes

面向中国大陆求职场景的 Codex Skill。它从可核验事实出发，逐步完成经历挖掘、JD 映射、简历写作、HR/面试官视角审查，以及可选的 Obsidian 原生 PDF 交付。

## 核心原则

- 只有已确认事实才能进入可投递简历。
- 不编造数字，不升级个人贡献，不把团队结果写成个人结果。
- 原始经历信息不足时，一次只问一个信息增益最高的问题。
- 先建立证据台账，再形成简历表达与面试叙事。
- 未经明确授权，不扫描工作区、知识库或主目录。

## 仓库结构

```text
skills/crafting-china-resumes/   可安装 Skill
tests/crafting-china-resumes/    单元测试、匿名行为评测与 PDF 合约测试
docs/architecture.md             架构与隐私边界
.github/workflows/validate.yml   持续验证
```

## 安装

在 Codex 中调用 Skill Installer：

```text
$skill-installer 从 GitHub 仓库 juanlou1217/crafting-china-resumes 的
skills/crafting-china-resumes 子目录安装
```

也可以手动安装到一个不存在的目标目录：

```bash
git clone git@github.com:juanlou1217/crafting-china-resumes.git
test ! -e "$HOME/.codex/skills/crafting-china-resumes"
cp -R crafting-china-resumes/skills/crafting-china-resumes \
  "$HOME/.codex/skills/crafting-china-resumes"
```

## 调用

```text
$crafting-china-resumes 我想从零挖掘一段经历。一次只问一个关键问题，先建立证据台账，不要直接写最终简历。
```

当请求清楚地涉及中国求职、经历挖掘、JD 分析、简历审查或 ATS 友好 PDF 时，也支持隐式发现。

## 验证

```bash
python3 -m pip install -r requirements-dev.txt
python3 -B -m unittest discover -s tests/crafting-china-resumes -p 'test_*.py'
python3 -B tests/crafting-china-resumes/behavior/validate_eval_assets.py
python3 -B tests/crafting-china-resumes/hash_skill_tree.py \
  skills/crafting-china-resumes
```

测试资产全部使用匿名或合成数据。真实候选人简历、PDF、本机路径和安装记录不属于本仓库。

## PDF 说明

PDF 交付使用用户明确授权的 Markdown、CSS 与 Obsidian 配置，在隔离 Vault 中通过 Obsidian 原生导出完成。仓库不包含真实简历，也不提供 Playwright、Pandoc 或自定义 HTML 渲染回退。

## License

项目源码采用 MIT License。第三方改编来源及完整许可文本见 `skills/crafting-china-resumes/THIRD_PARTY_NOTICES.md`。
