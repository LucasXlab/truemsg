# truemsg launch drafts

**Drafts only — nothing has been submitted or posted.** The proposed source destination is [LucasXlab/truemsg](https://github.com/LucasXlab/truemsg); verify that it is live and that final privacy/release checks passed before using these drafts. Source version: `0.2.0`, not a package-registry release. CI is prepared; no remote success or Star count is asserted. The code was developed with AI assistance. Human maintainers should review the wording, disclose their actual involvement, and be available to discuss it; these drafts invent no personal origin story or user testimonials.

## GitHub metadata

Description (194 characters):

> Offline lexical signals between commit messages and Git diffs. Inspect mismatched claims, get deterministic drafts, and preserve existing hooks. For human review, not semantic proof. Python CLI.

Topics (exactly 10):

```text
python cli git developer-tools code-review commit-messages conventional-commits pull-requests offline git-hooks
```

## Show HN — internal planning examples only

**Do not submit the generated title or comment below.** The [official HN guidelines](https://news.ycombinator.com/newsguidelines.html) prohibit generated submission text and generated or AI-edited comments. These examples only preserve the requested internal planning material. A human author must independently write any submission from their actual work and experience, without using this AI copy or an AI-edited rewrite. AI-code disclosure does not make generated post text acceptable.

Internal title example (not for submission):

> Show HN: truemsg – Offline message–diff signals for code review

Internal first-comment example (not for submission):

truemsg is a small Python CLI for a narrow review problem: a commit title can look plausible even when the changed files suggest a different scope.

It reads local Git changes and reports explainable lexical signals. For example, a synthetic commit saying “feat: add payment gateway” while adding only a test file triggers a rule. That is a reason to inspect the claim, not proof that the message is false. PASS is equally limited: it means no rule conflict, never verified semantic consistency. Chinese/no-keyword input is explicitly marked as insufficient evidence.

The source includes a disposable demo, structured JSON, deterministic message drafts, an optional ownership-safe pre-push hook, and a local-source GitHub Action. Runtime needs Python 3.11+, Git and Rich; no model, account or API key. Installation may download dependencies; analysis is offline. Development used AI assistance. Automated tests cover Git input boundaries, special filenames, configuration failures and hook preservation; no real-world PR precision/recall benchmark is claimed.

Source after release: https://github.com/LucasXlab/truemsg

Which small, reproducible counterexamples would make the rules more useful or expose a false positive? Please use synthetic diffs rather than private code.

Factual brief for a human author's independent preparation: local Python CLI; selected Git diff; limited lexical rules; synthetic source demo; deterministic drafts; optional hook; no semantic verification or precision benchmark; AI-assisted code development. The [Show HN guidelines](https://news.ycombinator.com/showhn.html) also require a project people can try and an author who can discuss the work. Eligibility and genuine author participation still need human review; this brief supplies no personal motivation or development history.

## Reddit candidate 1 — r/Python monthly showcase comment

Placement: a comment in the **then-current monthly showcase or appropriate daily thread**, not an independent showcase submission. Use English. The [official rules](https://www.reddit.com/r/Python/about/rules.json) route showcases into those threads and request useful project context; recheck at posting time.

### What My Project Does

truemsg is an AI-assisted, MIT-licensed Python CLI that compares commit/PR wording with observable Git paths, declarations and limited ASCII lexical signals. It can flag a feature claim accompanying a tests-only diff, generate a deterministic draft, and return explicit insufficient-evidence warnings. It never verifies semantic truth. The real synthetic demo and JSON/cast provenance are included in source.

### Target Audience

Developers who want a small, explainable reminder before review or an optional local hook. It is not an authorization system or a substitute for code review. Human-facing finding prose currently includes Chinese; JSON field names and rule IDs are stable English identifiers. Message overlap is ASCII-limited, with no-keyword cases called out instead of silently approved.

### Comparison

A format-only commit linter checks wording structure; truemsg also uses the selected diff. A model-generated PR summary can offer broader prose; this tool uses local, inspectable rules and makes a narrower claim. No detection-quality superiority has been measured. Python 3.11+, Git and Rich are required; no API key or model is used.

Source after release: https://github.com/LucasXlab/truemsg

Feedback on reproducible synthetic cases is welcome; do not paste private diffs or credentials.

## Reddit candidate 2 — r/SideProject technical feedback draft

Proposed title:

> [truemsg] - Offline commit-message and diff signals for reviewers

Body draft:

truemsg is a small AI-assisted Python side project for a specific review habit: checking what a commit *claims* against the files and declarations that actually changed.

The included synthetic demo shows three outcomes: a lexical match, a feature claim on a tests-only change, and a Chinese/no-keyword message where the tool admits that evidence is insufficient. Every outcome still has `semantic_verified: false`. There is also a deterministic draft command and an optional pre-push hook that refuses to overwrite an existing hook.

It runs from a source checkout with Python 3.11+, Git and Rich. No account, model or API key. MIT licensed. This is a limited heuristic with false positives and false negatives, not a claim that software can judge whether a developer is honest. Some human-readable findings are currently Chinese; localization and real-world evaluation remain work to do.

After release: https://github.com/LucasXlab/truemsg

Would this be useful as a local reminder, or would the current rules create more noise than value? Synthetic examples are more helpful than private repository data.

Placement note: the [official sidebar](https://old.reddit.com/r/SideProject/) welcomes project feedback and gives the project-name/short-description title format. The [rules endpoint](https://www.reddit.com/r/SideProject/about/rules.json) returned no subreddit rule entries on review; this is not approval. Recheck the sidebar and pinned posts, avoid any human-only/No-AI thread, edit the text personally, and respect participation/spam rules before posting. No engagement, traction or user experience is invented here.

## r/commandline — excluded for this generated draft

The [official rules](https://www.reddit.com/r/commandline/about/rules.json) prohibit AI-generated titles/post text and impose project-age and substantive-history requirements. Do not post this generated copy there. Reading/accepting the community rules is also a separate posting prerequisite. If a human maintainer later considers that community, they must independently write their own text, verify eligibility and disclose the actual AI-code involvement. There is no ready-to-post title or body for this target.

Internal factual brief only: Python CLI; deterministic lexical hints from selected Git diffs; source installation; optional hook; no semantic verification; no precision benchmark. This brief is not an eligibility judgment.

## X / Twitter — five-post thread

1. truemsg compares commit wording with selected Git changes using offline lexical rules. A reminder for code reviewers, not a truth detector. The code was developed with AI assistance; the source includes a reproducible synthetic demo.

2. A commit can say “add payment gateway” while changing only a test file. truemsg can flag that pattern. It cannot prove the claim false: paths and keywords are evidence to inspect, not a semantic explanation.

3. No supported keywords? The tool says evidence is insufficient. Chinese input is shown as WARN in the demo. PASS never means verified semantics; JSON keeps semantic_verified=false. No accuracy benchmark is claimed.

4. It also drafts deterministic messages and offers an optional pre-push hook. Existing hooks are preserved. Invalid refs and broken policy files fail clearly. Runtime: Python 3.11+, Git and Rich; no model or API key.

5. Source after release: https://github.com/LucasXlab/truemsg — MIT, source installation, real cast + unmodified CLI results. Feedback on synthetic counterexamples is useful. Please keep private diffs and credentials out of public reports.

## 掘金 — 技术稿草案

标题：提交标题写得像功能，diff 却只有测试：一个离线词法提醒工具

提交说明符合 conventional commits，不代表它解释了真实改动。truemsg 处理一个较窄的问题：把说明里的词与选定 Git diff 的文件路径、声明和有限词法信号放在一起，让审阅者更容易发现需要追问的地方。

仓库中的合成例子把标题写为“feat: add payment gateway”，实际只增加测试文件；规则会报警。但这不是“证明提交造假”。反过来，PASS 也只是规则没有发现冲突。中文或没有受支持 ASCII 关键词的输入会明确提示证据不足，JSON 始终保留 `semantic_verified: false`。

工程上，它读取本地 Git 对象，提供 JSON、确定性的消息草稿、可选且尊重已有钩子的 pre-push 集成和安装本地源码的 Action。参数、配置及读取失败返回明确错误，不把失败当成空 diff。代码使用 AI 辅助开发，公开演示全部来自可重复的合成仓库，原始 CLI 输出和 cast 可核对。

运行需要 Python 3.11+、Git 和 Rich；无需模型、API Key 或账号。它不做语义正确性判断，尚无真实 PR 精度/召回率结论。欢迎用合成反例讨论误报和遗漏，避免公开私人代码或凭据。

发布后源码：https://github.com/LucasXlab/truemsg 。安装以源码 checkout 为准，不声称已在 PyPI 发行。

## V2EX — 分享稿草案

标题：[分享] truemsg：用本地 diff 给提交说明做有限词法提醒

truemsg 是一个 AI 辅助开发的小型 Python CLI。它把提交/PR 消息与选定 diff 的路径、声明和关键词对照，输出可解释的提醒；不是“鉴定提交真假”。PASS 只表示规则未报警，中文/无关键词时会提示证据不足。

仓库提供可重复的合成演示、完整原始输出、确定性消息草稿及可选 pre-push hook。原有 hook 不会被覆盖。运行需要 Python 3.11+、Git、Rich，没有服务、模型或 API Key。MIT 许可，使用源码安装；真实 PR 的误报率仍待评估。

发布后链接：https://github.com/LucasXlab/truemsg 。想听听这类提醒是否值得接进个人工作流，以及有哪些小型合成反例。请不要粘贴真实私有 diff 或凭据。发帖节点和社区规则须由维护者发布前重新核对。

## 即刻 — 短稿草案

提交写“新增支付网关”，diff 却只加测试，值得再看一眼。

truemsg 用本地路径、声明和有限词法线索做这个提醒。它不证明说明真假；PASS 也不等于语义正确，中文/无关键词会坦白证据不足。代码由 AI 辅助开发，GIF 来自真实 CLI 跑合成仓库，完整输出可核对。Python + Git，无模型或 API Key。

发布后源码：https://github.com/LucasXlab/truemsg 。欢迎合成反例，别公开私人代码。配图建议：`assets/demo.gif`；其中停留时间为阅读调整，原 cast 保留真实时间。

## Product Hunt

Tagline:

> Offline commit-message signals for code reviewers

Description draft:

truemsg compares commit/PR wording with selected Git changes using inspectable lexical rules. Review mismatched scope claims, see insufficient-evidence warnings, draft deterministic messages, and optionally use a hook that preserves existing hooks. No model or API key. Source installation, Python 3.11+, Git and Rich. AI-assisted development, MIT licensed. PASS is not semantic proof; no real-world accuracy or traction is claimed.

Before publishing any channel: verify the final public source, human ownership/involvement, current platform rules, actual source-install commands and the final privacy clearance. These are drafts, not evidence of publication.
