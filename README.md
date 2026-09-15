# 🤖 Agent Skills Hub (`agent-skills`)

> 通用 AI Agent 技能仓库，面向 Google Antigravity、Claude Code 及主流自动化智能体框架，提供生产级、开箱即用的专业工作流与自动化扩展技能。

---

## 📦 技能目录 (Skill Catalog)

| 技能名称 (Skill) | 目录路径 | 描述说明 | 依赖环境 |
| :--- | :--- | :--- | :--- |
| **`weekly-report-generator`** | [`skills/weekly-report-generator`](./skills/weekly-report-generator) | **企业高保真周报生成器**：1:1 复刻高管汇报级 PPT 排版，支持端到端 Timeline 甘特图自动排版、交付物红黄绿健康度跟踪、本周工作卡片、多企业主题适配及 16:9 矢量 PDF 邮件导出。 | Python 3.8+ / Google Chrome (可选) |

---

## 🚀 快速安装指南 (Installation)

### 方式一：安装至 Google Antigravity 全局技能库 (推荐)
在当前机器上的所有项目与会话中均可直接激活：

```bash
# 克隆仓库
git clone https://github.com/lighters/agent-skills.git ~/.gemini/agent-skills

# 软链接技能至 Antigravity 全局 skills 目录
mkdir -p ~/.gemini/antigravity-cli/skills/
ln -s ~/.gemini/agent-skills/skills/weekly-report-generator ~/.gemini/antigravity-cli/skills/weekly-report-generator
```

### 方式二：安装至指定项目工作区 (`.agents/skills`)
仅对当前项目团队生效，适合随项目代码库一同版本管理：

```bash
cd your-project/
mkdir -p .agents/skills/
cp -R /path/to/agent-skills/skills/weekly-report-generator .agents/skills/
```

---

## 🛠️ 技能详解：`weekly-report-generator`

### 1. 核心能力
1. **PPT 样式高保真还原**：
   - **Slide 1 封面页**：企业 Branding、项目编号、周期、汇报人、机密标识。
   - **Slide 2 整体项目计划 (Timeline)**：端到端甘特图、跨多周任务条带映射、春节等节假日金色高亮列、关键里程碑红星（★）、`We are here` 动态当前周指针。
   - **Slide 3 交付物及状态**：成果物完成度标签、红黄绿风险状态（`High Risk` / `Caution` / `No Risk`）。
   - **Slide 4 本周工作**：完全复刻 PPT 第 4 页双列卡片 + 右上角状态徽标卡 + 底部三色状态图例。
2. **多企业风格定义 (Theme System)**：
   - 基于 CSS Custom Properties，内置 6 款预设企业主题：`classic-navy`（阿斯利康蓝）、`tech-blue`（科技蓝）、`corporate-crimson`（华为/联想红）、`emerald-forest`（ESG森绿）、`cyber-purple`（数智紫）、`minimal-slate`（极简灰）。
3. **用于邮件提交的 16:9 横版 PDF 导出**：
   - 精准 `@media print` 媒体查询，一页幻灯片对应一页 PDF，无截断无溢出。
   - 支持网页一键打印与 Python 无头 Chrome 自动化静默导出。

### 2. 快速使用

```bash
cd skills/weekly-report-generator

# 1. 从数据生成 HTML 周报
python3 scripts/generate_report.py \
  --data examples/sample_data.json \
  --theme classic-navy \
  --output weekly-report.html

# 2. 导出为高清 PDF 附件
python3 scripts/export_pdf.py \
  --input weekly-report.html \
  --output weekly-report.pdf
```

详细规范请参阅：
- 技能说明：[`skills/weekly-report-generator/SKILL.md`](./skills/weekly-report-generator/SKILL.md)
- 数据格式与 Timeline 规范：[`skills/weekly-report-generator/references/input_format_guide.md`](./skills/weekly-report-generator/references/input_format_guide.md)

---

## 📝 贡献新技能 (Contributing)

欢迎扩展更多通用 Agent Skills！每个新技能应遵循 Antigravity 官方技能规范：

```text
skills/<skill-name>/
├── SKILL.md            # 包含 YAML frontmatter (name, description) 与 Runbook 说明
├── scripts/            # 自动化脚本与工具链
├── templates/          # 模板与配置资源
├── examples/           # 样例输入与产出
└── references/         # 详细规范文档与手册
```

---

## 📄 开源许可
MIT License © 2024-2026 [lighters](https://github.com/lighters)
