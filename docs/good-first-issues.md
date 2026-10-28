# Good First Issues（提议，需维护者复核）

> 已写好正文，发布仓库后到 Issues → New → 粘贴即可，记得打 `good first issue` + `help wanted` 标签。

---

## 1. 支持 C / C++ 方法级标识符提取
**标签**：`good first issue` `help wanted` `enhancement`
**描述**
`src/truemsg/diff.py` 的 `DECL_KEYWORDS` 目前用声明关键字（`struct`/`class`/`typedef` 等）捕获 C/C++ 标识符，
但漏掉没有关键字的普通函数定义，如 `int foo(int x) { ... }`。
请为 `c` / `cpp` 增加一条"无关键字函数签名"正则，并补测试。
**验收**
- 识别 `Type name(...) {` 形式的函数名
- 不影响已有 `struct/class/...` 识别
- 新增 `tests/fixtures` 与解析测试，`pytest -q` 全绿

## 2. 支持 pre-commit.com 钩子
**标签**：`good first issue` `help wanted`
**描述**
不少团队用 [pre-commit](https://pre-commit.com) 而非原生 git 钩子。
请新增 `.pre-commit-hooks.yaml` 与文档，让 truemsg 可作为 pre-commit 钩子运行。
**验收**
- 仓库根增加 `.pre-commit-hooks.yaml`
- README 增加「pre-commit 用法」小节
- 说明在 pre-commit 下 `check` 的 `--range` 取值方式（如暂存区）

## 3. `--glossary`：从历史提交学习团队术语表
**标签**：`good first issue` `help wanted` `feature`
**描述**
关键词匹配目前是通用词匹配。请增加一个可选开关：从仓库历史 commit 信息里抽取高频词作为"术语表"，
在匹配时给予更高权重，降低误报。默认关闭，纯标准库实现。
**验收**
- `analyze` 支持可选 `glossary` 列表
- CLI 增加 `--glossary [N]`（读取最近 N 条提交）
- 加测试

## 4. 扩充测试 fixtures 与多语言 CI 矩阵
**标签**：`good first issue` `help wanted` `tests`
**描述**
为更多真实 diff 场景补充 fixture（大型重构、仅注释、误报案例、多文件 feat、rename、binary），
为 CI 的 Python 3.11–3.13 任务补回归，不将配置存在视为实际通过，覆盖率 ≥ 90%。
**验收**
- `tests/fixtures/` 增加 ≥5 个真实风格 diff
- `pytest --cov` 覆盖率报告提升
- CI 矩阵无新增失败

## 5. `--embeddings` 可选本地语义匹配（默认关闭）
**标签**：`good first issue` `help wanted` `enhancement`
**描述**
当前关键词匹配是词面/词干匹配。请设计一个可选开关，允许接入本地句子向量模型做语义匹配，
但必须**默认关闭**且不引入强制依赖，保证零配置仍可离线运行。
**验收**
- 仅在显式开启时加载额外依赖
- 默认路径（无开关）不导入任何重量库
- 文档说明如何开启与权衡
