# Neutral Resume Skill Rename and Packaging Design

**Status:** Awaiting written-spec review  
**Date:** 2026-07-23

## Context

The Skill currently exposes `crafting-china-resumes` in its repository name, install path, invocation name, display name, documentation, tests, and CI. Its capability is broader than the brand suggests: it mines evidence, packages verified experience, maps JDs, reviews resume quality, prepares interview evidence, and optionally delivers a native Obsidian PDF.

The public identity should be neutral while the internal guidance may still state that the Skill understands Chinese-mainland recruiting conventions. The Skill must also distinguish factual fabrication from legitimate professional packaging: it rejects invented facts while actively improving language, value framing, and evidence-backed keywords.

## Goals

1. Rename every public identity surface to `crafting-resumes` without retaining a second callable alias.
2. Replace the current README with a detailed, outward-facing product introduction and usage guide.
3. Make reasonable language packaging and high-value keyword optimization explicit first-class behavior.
4. Preserve strict gates against invented metrics, scope, ownership, tools, outcomes, and private information.
5. Migrate the installed Skill, local checkout, GitHub repository, tests, CI, and documentation without an ambiguous mixed-name state.

## Non-goals

- Removing Chinese recruiting expertise from the Skill.
- Rewriting real candidate material or regenerating a resume PDF.
- Adding a second renderer, web application, or hosted service.
- Keeping `crafting-china-resumes` as a compatibility alias after the new installation passes.

## Naming contract

| Surface | New value |
|---|---|
| GitHub repository | `juanlou1217/crafting-resumes` |
| Repository directory | `crafting-resumes` |
| Installable Skill directory | `skills/crafting-resumes` |
| Skill frontmatter name | `crafting-resumes` |
| Invocation | `$crafting-resumes` |
| Skill heading | `Crafting Resumes` |
| Display name | `求职简历教练` |
| Installed path | `~/.codex/skills/crafting-resumes` |
| Test root | `tests/crafting-resumes` |

The description may mention Chinese-mainland recruiting as a supported context, but the repository name, Skill name, title, invocation, and display name must not use a geographic qualifier.

## README information architecture

The README is a public product page first and a maintainer reference second.

### Hero

Use the title `Crafting Resumes` and the promise:

> 把普通经历，变成可信、有说服力、经得住面试追问的求职简历。

The opening paragraph explains that the Skill starts from verifiable evidence and covers experience mining, JD tailoring, recruiter/interviewer/ATS review, interview consistency, and optional PDF delivery.

### Public sections

1. **它解决什么问题** — ordinary experience, unclear contribution, weak JD fit, interview-risk wording, and fear of AI fabrication.
2. **核心能力** — one-question interviews, evidence ledger, contribution separation, value framing, JD mapping, keyword optimization, multi-perspective review, and PDF delivery.
3. **为什么它不只是“润色”** — explain evidence gates, information gain, role translation, and resume/interview consistency.
4. **快速开始** — GitHub installation, manual installation, explicit invocation, and implicit discovery.
5. **典型工作流** — start from zero, resume-only, JD-only, resume plus JD, review, and final PDF.
6. **输出内容** — evidence ledger, experience cards, draft and tailored resumes, ATS text, interview-risk questions, outreach material, and PDF.
7. **合理包装与真实性边界** — show allowed transformations and prohibited claims with before/after examples.
8. **高价值关键词如何使用** — explain JD-first mapping, role lexicon supplementation, evidence requirements, placement, and anti-stuffing rules.
9. **PDF 交付** — native Obsidian workflow and prerequisites.
10. **隐私与权限** — explicit path authorization, minimal disclosure, and repository data boundary.
11. **安装、更新与卸载** — commands use only the new name and avoid silent overwrite.
12. **开发与验证** — repository layout, dependencies, test commands, CI, and deterministic Skill hash.
13. **FAQ and License** — common usage questions, limitations, and third-party notices.

## Reasonable packaging contract

The public principle is:

> We reject factual fabrication, not professional packaging.

Packaging is expected when it changes expression without changing the underlying claim.

### Allowed transformations

1. **Professional compression** — turn fragmented conversation into concise action-and-value language.
2. **Responsibility clarification** — replace vague participation language with `负责`, `协同`, or `支持` only when the evidence establishes that level.
3. **Role-language translation** — translate concrete work into the vocabulary of the target role without adding tools, scope, or outcomes.
4. **Value framing** — connect verified work to delivery, quality, efficiency, stability, growth, user experience, cost, or risk when that relationship is supported.
5. **Structure improvement** — order bullets by relevance and use action, object, method, and result/deliverable structure.
6. **Keyword alignment** — add a JD or role keyword only when the candidate evidence is semantically equivalent.

### High-risk wording gates

| Wording | Minimum evidence |
|---|---|
| `负责` | Direct ownership of the named task or deliverable |
| `推动` | Concrete cross-person or cross-team actions that advanced the work |
| `主导` | Decision authority plus coordination and accountability |
| `从 0 到 1` | A genuinely new capability and meaningful end-to-end ownership |
| `落地` | The output was delivered, adopted, launched, or put into use |
| `优化` | A specific before/after change or a clearly improved mechanism |
| `提升` / `降低` | Confirmed comparison and metric definition; numbers remain exact |

If the evidence does not meet a gate, use a lower-risk accurate verb or ask one blocking question. Do not quietly upgrade the claim.

## Keyword strategy

Use a hybrid strategy in this order:

1. **JD keywords first** — responsibilities, hard skills, deliverables, business context, ATS terms, and interview themes.
2. **Role lexicon second** — action, ownership, method, deliverable, business-value, quality, and risk vocabulary appropriate to the target role.
3. **Evidence mapping before insertion** — record `keyword`, `source`, `candidate_evidence`, `match_strength`, `allowed_surface`, and `status`.
4. **Placement by purpose** — summary for positioning, skills for searchable hard skills, bullets for evidence-backed application, and interview notes for unverified gaps.
5. **No keyword stuffing** — one precise term with evidence is stronger than several adjacent buzzwords. Repeated or unsupported terms are removed.

Unverified JD terms remain `gap` or `next_question`; they do not enter a deliverable resume.

## Implementation surfaces

The rename updates directories, Python path constants, manifest `raw_output_path` fields, workflow commands, README examples, architecture documentation, ignore rules, Skill metadata, and all exact-name package assertions. Content references to Chinese recruiting remain only where they describe capability or context.

The packaging behavior updates the main router plus the evidence, interview, JD mapping, resume writing, review, output-contract, and relevant role-reference files. New concise examples show raw wording, permitted polished wording, evidence used, and wording that remains prohibited.

## Migration sequence

1. Add failing repository and Skill-contract tests for the new name and packaging behavior.
2. Rename `skills/` and `tests/` subdirectories and update every path reference.
3. Implement the packaging matrix, keyword-evidence map, high-risk wording gates, README, and documentation.
4. Run unit, behavior, package, privacy, hash, and fresh invocation verification.
5. Fast-forward the validated branch to `main` and push it while the old repository URL still exists.
6. Rename the GitHub repository to `crafting-resumes`, update the SSH remote, and verify visibility/default branch/CI.
7. Remove the temporary worktree, rename the primary local checkout directory, and verify the new clone path and remote.
8. Stage and validate `~/.codex/skills/crafting-resumes`; install atomically only if the target is absent.
9. Run explicit and implicit fresh discovery against the new installed name.
10. Remove the old installed directory only after the new installation passes and its source tree hash matches.

GitHub's old repository URL may redirect, but no README, installation command, local remote, or active Skill alias will continue advertising the old name.

## Test design

- Repository identity tests verify the neutral repository/Skill/display names and absence of the old callable name from active surfaces.
- Package tests continue enforcing the 500-word router limit, exact frontmatter, routed references, provenance, licenses, and generated-artifact policy.
- Packaging contract tests require allowed transformations, high-risk wording gates, keyword-evidence mapping, and anti-stuffing rules.
- Focused fresh-agent cases cover an ordinary project, an overclaim request, a JD keyword gap, and a complete tailored delivery.
- Full unit tests, all twelve frozen behavior cases and twenty-four manifests, deterministic tree hashing, source/install diff, explicit invocation, implicit discovery, and GitHub Actions must pass.

## Failure handling and rollback

- Stop if the neutral GitHub repository name or installed target becomes occupied.
- Do not remove or overwrite the old installation before the new name passes validation and discovery.
- Do not rename the GitHub repository until the new-name commit is on `main` and CI is green.
- If remote rename verification fails, keep the local repository and installed Skill unchanged and use GitHub's redirect while diagnosing.
- If a packaging test fails, retain the stronger truth gate; never weaken evidence requirements merely to insert a desirable keyword.
