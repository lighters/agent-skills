# Scope to Evidence：需求与实现对照审查

面向产品、交付、研发与验收协作，把需求／方案与代码、测试、部署和验收证据逐项对齐。无需额外 Python 依赖或固定办公平台。

## 使用

将本目录安装到所用 Agent 的 skills 目录，或让 Agent 读取本目录 `SKILL.md`。

示例请求：

> 使用 scope-to-evidence，对照 docs/requirements.md 审查当前仓库的导出能力。只读检查，不修改实现。输出需求证据矩阵，区分源码支持、真实运行、部署和验收，把报告保存到 docs/reviews/export-review.md。

也可以提供方案、测试报告和验收记录，不必一定提供完整仓库。无法访问的部分会保留为未知。复杂 Word／PDF 等材料由环境已有的读取能力解析，本 skill 不提供格式转换器。

## 交付

- 可定位到原始需求与证据的矩阵。
- 已实现／部分实现／缺失／无法验证的明确判断。
- 来源冲突、验证边界和下一步通过条件。

主流程见 [SKILL.md](SKILL.md)，示例见 [examples/review-report.md](examples/review-report.md)，行为评测方法见 [evals/README.md](evals/README.md)。本 skill 不自动修代码、提交、发布或代替客户验收。
