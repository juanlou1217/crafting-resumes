# Obsidian 原生 PDF 交付

本流程只把用户明确授权的 Markdown 内容按已授权的仓库 CSS 样式导出为 PDF。它不改写内容，也不代表经历、数字或其他候选人事实已经完成核验。

## 硬门

仅在以下条件全部满足后进入 PDF 流程：

1. 用户已明确选择内容门：正式投递 PDF 须确认事实快照和拟交付的逐字文案；仅供评价样式的版式预览可不核验事实，但须确认精确源 Markdown 和“逐字原样导出”，并始终标为 `layout_preview_unverified_content`，不得称为最终投递版。该标签只写入私密验收记录和交付说明，不注入 Markdown 或 PDF。`draft_under_review` 只有在用户明确请求这种版式预览时才能进入后一路径。
2. 用户已分别授权四个精确绝对路径：Markdown、现有 CSS snippet、`.obsidian/appearance.json` 和一个尚不存在的目标 PDF。不得扫描目录、猜测文件或扩大授权范围。
3. 三个输入均为非符号链接的普通文件；目标路径及悬空符号链接均不存在。
4. Obsidian 桌面版可用；一个含 `pypdf==6.10.0` 的绝对 Python 解释器和经过真实渲染 smoke test 的 Poppler `pdfinfo`、`pdftoppm` 已绑定。

任何硬门失败都阻断 PDF，但不阻断已经符合输出合同的 Markdown 简历和 ATS 纯文本交付。不得生成“替代 PDF”或把未验证文件称为 PDF 交付物。

## 路径与私密登记

以下名称均为通用占位符，执行时必须替换成用户逐项授权的精确绝对路径：

```text
<AUTHORIZED_MARKDOWN>
<AUTHORIZED_CSS>
<AUTHORIZED_APPEARANCE_JSON>
<NEW_TARGET_PDF>
<SKILL_ROOT>
<PYTHON>
<PDFINFO>
<PDFTOPPM>
```

在权限受限的任务登记中记录这四个规范化路径、三项输入 SHA-256、确认状态和本任务创建的临时路径。manifest、expectation 和 report 是任务私密控制文件，不是日志；不得把它们的路径、哈希、文本 marker 或内容复制到聊天、终端摘要或运行日志。运行日志只记录状态和计数，不记录姓名、联系方式、原文、文件名或路径。

## 严格流水线

### 1. 预检与哈希门

- 在用户确认内容和路径时记录 Markdown、CSS、appearance 三项 SHA-256；执行前重新计算并逐项精确比对。
- 确认 Markdown frontmatter 含指定 CSS stem 的 `cssclasses`，且 appearance 的 `enabledCssSnippets` 含同一 stem。
- 用 `lstat` 语义确认目标 PDF 没有任何目录项；普通存在检查不得忽略悬空符号链接。
- 任一输入哈希改变、路径不符、样式启用状态不符或目标已存在时停止。先重新取得确认，不得沿用旧基线。

### 2. 建立隔离任务目录

用 `mktemp -d` 在 `/private/tmp` 下创建本任务唯一的随机父目录，先设 `umask 077`，再确认父目录权限为 `0700`。不得复用已有目录。把以下路径登记为本任务专属路径：

```text
<TASK_ROOT>/isolated-vault
<TASK_ROOT>/prepare-manifest.json
<TASK_ROOT>/expectation.json
<TASK_ROOT>/verification-report.json
<TASK_ROOT>/page
```

`<TASK_ROOT>/isolated-vault` 必须尚不存在；由 preparer 创建并设置为 `0700`。任务父目录和 Vault 都不得位于主 Vault 内。

### 3. 绑定并实测工具链

不得假定裸 `python`、`python3` 或 PATH 中的 Poppler 可用。将 `<PYTHON>` 绑定为绝对解释器路径；Codex 桌面环境优先使用已加载的 workspace dependency Python。先运行版本门：

```bash
"<PYTHON>" -B -c 'import pypdf; assert pypdf.__version__ == "6.10.0"'
```

若没有满足版本门的解释器，可在 `<TASK_ROOT>/venv` 建立任务专用虚拟环境，并从 `<SKILL_ROOT>/requirements.txt` 安装；需要下载依赖时先取得相应权限。安装或版本检查失败就停止，不得用未验证解释器继续。

把 `<PDFINFO>` 和 `<PDFTOPPM>` 分别绑定为绝对可执行文件。创建 `<TASK_ROOT>/font-cache`（权限 `0700`）和一页空白 A4 的 `<TASK_ROOT>/poppler-smoke.pdf`：

```bash
mkdir -m 700 "<TASK_ROOT>/font-cache"
"<PYTHON>" -B -c 'import sys; from pypdf import PdfWriter; writer = PdfWriter(); writer.add_blank_page(width=595.2756, height=841.8898); writer.write(sys.argv[1])' "<TASK_ROOT>/poppler-smoke.pdf"
"<PDFINFO>" "<TASK_ROOT>/poppler-smoke.pdf"
env XDG_CACHE_HOME="<TASK_ROOT>/font-cache" \
  "<PDFTOPPM>" -f 1 -l 1 -singlefile -png -r 36 \
  "<TASK_ROOT>/poppler-smoke.pdf" \
  "<TASK_ROOT>/poppler-smoke"
```

通过执行工具给两条 Poppler 命令各设最多 30 秒时限，不能只检查 `command -v`。smoke 必须退出 `0` 且生成一个非空 `poppler-smoke.png`；超时、持续报错或无输出均视为不可用。

若本机 Poppler 需要 Fontconfig，只有在找到并验证可读的本机 `fonts.conf` 后，才把 `FONTCONFIG_FILE` 绑定到该精确绝对路径；`XDG_CACHE_HOME` 始终指向 `<TASK_ROOT>/font-cache`。禁止写入全局字体缓存。后续真实渲染必须复用 smoke 通过的同一组绝对工具路径和环境变量；无可用组合就停止。smoke PDF、PNG 和字体缓存均登记为本任务临时产物。

### 4. 运行 preparer

```bash
"<PYTHON>" -B "<SKILL_ROOT>/scripts/prepare_obsidian_export.py" \
  --markdown "<AUTHORIZED_MARKDOWN>" \
  --css "<AUTHORIZED_CSS>" \
  --appearance "<AUTHORIZED_APPEARANCE_JSON>" \
  --workspace "<TASK_ROOT>/isolated-vault" \
  --target-pdf "<NEW_TARGET_PDF>" \
  --manifest "<TASK_ROOT>/prepare-manifest.json"
```

preparer 的 manifest 必须只有本任务授权的信息，并包含：

- `workspace`：隔离 Vault；
- `copies.markdown|css|appearance.path` 和各自 `sha256`；
- `target_pdf`：精确目标路径；
- `suggested_temporary_pdf`：位于 `<TASK_ROOT>` 下、尚不存在且不同于目标的临时 PDF。

私下核对 manifest 中三个副本哈希分别等于预检哈希，所有路径均落在预期位置，`target_pdf` 精确匹配授权目标。任何不一致都停止。绝不把 manifest 输出到日志。

### 5. 只打开隔离 Vault

在 Obsidian 中把 manifest 的 `workspace` 打开为 Vault，并打开其中的 Markdown 副本。绝不打开主 Vault。若 Obsidian 把临时 Vault 写入应用级 Vault 列表，只登记该规范化临时绝对路径，供精确清理。

导出前必须人工确认：

- 当前是 **Reading View**，不是编辑视图或 Live Preview；
- **Properties 已隐藏**，页面中看不到 frontmatter；
- Settings → Appearance 中指定 CSS snippet 已启用；
- Markdown 的指定 `cssclasses` 已应用，预览中能看到该仓库样式的可辨识特征；
- 打开的文件和 Vault 路径均来自 manifest，而非主 Vault。

任一项无法确认都停止，不得靠导出结果猜测样式已生效。

### 6. Obsidian 原生导出到临时 PDF

只使用 Obsidian 自带的 **Export to PDF**，设置：

- A4；
- Portrait；
- 100%；
- 若原生对话框提供打印背景选项，则启用；
- 不额外叠加自建页边距或模板；
- 输出路径严格使用 manifest 的 `suggested_temporary_pdf`。

绝不直接导出到 `<NEW_TARGET_PDF>`。若 100% 产生裁切或分页问题，本轮判失败并报告页码；不得静默缩放、改 Markdown 或改 CSS。

### 7. 建立 verifier expectation

在 `<TASK_ROOT>/expectation.json` 写入经过确认的最小 marker 和页面范围，不在日志显示 marker：

```json
{
  "required_text": [
    "<CONFIRMED_REQUIRED_MARKER_1>",
    "<CONFIRMED_REQUIRED_MARKER_2>"
  ],
  "forbidden_text": [
    "cssclasses",
    "<FORBIDDEN_FRONTMATTER_KEY>",
    "<LOCAL_PATH_PREFIX>"
  ],
  "min_pages": 1,
  "max_pages": 3,
  "page_size": "A4",
  "orientation": "portrait"
}
```

required marker 应覆盖用户已授权从该源文件原样出现的身份/联系方式和主要栏目，但只保存在 `0700` 任务目录中；这里校验的是原样呈现，不是事实真实性。forbidden marker 应覆盖 Properties/frontmatter 字段和本机路径前缀。把示例中的 `3` 替换为本次确认的 JSON 整数，不能加引号；页数范围不得为通过检查而任意放宽。

### 8. 运行 verifier

```bash
"<PYTHON>" -B "<SKILL_ROOT>/scripts/verify_resume_pdf.py" \
  --pdf "<SUGGESTED_TEMPORARY_PDF>" \
  --expect "<TASK_ROOT>/expectation.json" \
  --report "<TASK_ROOT>/verification-report.json"
```

两个 CLI 的退出码合同：

| CLI | `0` | `1` | `2` |
| --- | --- | --- | --- |
| `prepare_obsidian_export.py` | 隔离 Vault 和 manifest 准备成功 | 内容或状态被安全拒绝，例如样式门、已有 workspace/目标或符号链接 | 参数无效或运行时错误 |
| `verify_resume_pdf.py` | 所有自动检查通过 | PDF 可检查，但至少一个验收项失败 | expectation/PDF 缺失或不可读、参数无效或运行时错误 |

verifier report 必须恰好有八个顶层键：

| 键 | 合同 |
| --- | --- |
| `status` | `pass`、`fail` 或 `error` |
| `pdf_sha256` | PDF SHA-256；不可取得时为 `null` |
| `page_count` | 页数；不可取得时为 `null` |
| `page_size` | 检出的页面尺寸状态；不可取得时为 `null` |
| `orientation` | 检出的方向状态；不可取得时为 `null` |
| `required_text` | `expected` 与 `missing` 计数 |
| `forbidden_text` | `expected` 与 `found` 计数 |
| `findings` | 仅含脱敏 finding code 的数组 |

只有退出码 `0`、`status: "pass"`、`findings: []`、缺失/命中计数均为 `0` 才能继续。report 和退出码矛盾时停止。控制台摘要只能包含状态和计数。

### 9. Poppler 与逐页原图检查

先对临时 PDF 运行：

```bash
"<PDFINFO>" "<SUGGESTED_TEMPORARY_PDF>"
env XDG_CACHE_HOME="<TASK_ROOT>/font-cache" \
  "<PDFTOPPM>" -png -r 180 \
  "<SUGGESTED_TEMPORARY_PDF>" \
  "<TASK_ROOT>/page"
```

若 smoke 使用了 `FONTCONFIG_FILE`，在上述 `env` 命令中原样加入同一个 `FONTCONFIG_FILE="<VERIFIED_FONTCONFIG_FILE>"`；不得临时换工具或环境。

`pdfinfo` 必须与 report 的页数、A4 和纵向结论一致。按 report 的 `page_count` 构造精确页文件清单，确认 PNG 数量完全一致，并以 **original detail** 逐页打开 180 DPI PNG；不得只看缩略图、拼图或抽样页。

每一页都检查：

- 指定仓库样式确实生效，Properties/frontmatter/本机路径没有出现；
- 中文字体无缺字、乱码或替换字符；
- 无裁切、重叠、越界、异常换行或空白页；
- 标题、列表、粗体、链接、日期和层级清楚；
- 无孤立页尾标题或明显破坏阅读的经历断裂。

**verifier 自动通过绝不能替代逐页视觉检查。** 任一页失败都不得发布；只报告脱敏页码、状态和问题计数。

### 10. 排他原子发布

只有自动检查、`pdfinfo` 和每一页视觉检查全部通过后：

1. 再次确认三项主输入 SHA-256 与预检基线一致。
2. 再以 `lstat` 语义确认目标没有任何目录项。
3. 确认临时 PDF 是普通文件、哈希等于 report 的 `pdf_sha256`，且临时文件与目标父目录的设备号相同。
4. 只用不覆盖的硬链接发布：

```bash
ln "<SUGGESTED_TEMPORARY_PDF>" "<NEW_TARGET_PDF>"
```

硬链接创建是对目标名称的排他原子操作。禁止 `ln -f`。任何失败都停止；特别是 `EXDEV`（不同文件系统）或并发创建导致的“目标已存在”，不得删除竞争目标、复制、移动、重命名或降级为覆盖发布。

### 11. 发布后检查

- 重新计算临时 PDF 与目标 PDF 的 SHA-256，必须完全一致；
- 对目标 PDF 再运行一次 `pdfinfo` 快速可读性检查，并核对页数；
- 运行日志只写发布状态、页数、finding 数和视觉检查页数，不写哈希、路径或候选人内容。

发布后检查异常时停止并报告，不得覆盖或悄悄替换已经创建的目标。

### 12. 精确清理

关闭隔离 Vault 后，只清理任务登记中由本次创建且规范化路径精确匹配的 Vault、虚拟环境（若创建）、Poppler smoke 文件、任务内字体缓存、临时 PDF、expectation、report、逐页 PNG、manifest 和 `<TASK_ROOT>`。不得用未解析变量、宽泛 glob 或 `/private/tmp` 父目录作为删除目标，不得触碰其他任务或退役方案的产物。

应用级 Vault 登记也只能删除与本任务隔离 Vault 规范化绝对路径精确相等的一项；若存在歧义或无法安全定位，就保留失效登记并只报告状态。失败诊断需要保留临时产物时，维持 `0700` 权限并取得用户决定。

## 绝对禁止的替代链路

不得使用 Playwright、Pandoc、自建 HTML/CSS、浏览器打印、云端转换、Modern Minimal、Classic Professional、Creative Clean、任何退役主题或任何其他 renderer。不得为“先交付”伪造 PDF。

Obsidian 或 Poppler 不可用、原生导出失败、snippet 未生效或任何自动/视觉检查失败时：停止 PDF 流程，继续交付合格的 Markdown/ATS 文本，并明确 PDF 因原生链路不可用或未通过验收而未生成。
