# 🤖 Agent Skills Hub (`agent-skills`)

> 通用 AI Agent 技能仓库，面向 Google Antigravity、Claude Code 及主流自动化智能体框架，提供生产级、开箱即用的专业工作流与自动化扩展技能。

---

## 📦 技能目录 (Skill Catalog)

| 技能名称 (Skill) | 目录路径 | 描述说明 | 依赖环境 |
| :--- | :--- | :--- | :--- |
| **`weekly-report-generator`** | [`skills/weekly-report-generator`](./skills/weekly-report-generator) | **企业高保真周报生成器**：1:1 复刻高管汇报级 PPT 排版，支持 4 页标准结构 + 自由扩展 Slide 5+ 方案研讨与议题决议页、端到端 Timeline 甘特图自动排版、交付物红黄绿健康度跟踪、全屏无黑边演示模式、工作周日期智能校验、多企业主题及 16:9 矢量 PDF 导出。 | Python 3.8+ / Google Chrome (可选) |

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

### 1. 核心能力与亮点

1. **PPT 样式 1:1 高保真还原（4 页基础骨架 + Slide 5+ 方案研讨扩展）**：
   - **Slide 1 封面页**：企业 Branding、徽标、项目编号、汇报周期、汇报人、机密等级与整体健康度徽章。
   - **Slide 2 整体项目计划 (Work Plan / Timeline)**：端到端甘特图、跨多周任务条带映射、`We are here` 当前周动态红箭头指针、法定节假日金色高亮列、关键里程碑红星（★）。
   - **Slide 3 交付物及状态 (Deliverables / Output Status)**：聚焦项目**主要交付物与核心里程碑门禁**，支持红黄绿风险状态指示（`Good` / `Caution` / `High Risk`）。
   - **Slide 4 本周工作 (Task Management)**：聚焦微观战术任务执行，完全复刻双列卡片（前期工作 / 下周计划 / 风险管理 / 未来两周里程碑）+ 状态徽标。
   - **Slide 5+ 方案研讨与议题扩展页 (Discussion & Proposal Slides)**：周报后可按需追加任意多页议题页，支持 **方案比选 (`comparison`)**、**卡片矩阵 (`cards`)**、**议题深研 (`agenda`)**、**评估矩阵表格 (`table`)** 与 **自由 HTML (`custom`)** 等多种专业排版，配备方案推荐徽标与底部周会决议卡片。
2. **所见即所得直接内容编辑 (WYSIWYG Inline Editing)**：
   - **细节改字零阻力**：无需 Agent 重新调用 skill 重新生成，点击顶部工具栏 **「✏️ 编辑内容」**（或直接双击页面任意文字，或按快捷键 `E`）即可直接在网页上修改字词、措辞或交付物状态。
   - **双向数据同步**：修改后的文字即时生效并同步回填至嵌入的 JSON 数据中。
   - **一键另存与打印**：点击 **「💾 另存 HTML」** 可将修改好的独立文件保存在本地；点击 **「导出 PDF / 打印」** 直接打印为矢量 PDF。
3. **全屏无黑边演播模式 (Presentation Deck Mode)**：
   - 支持动态 1 至 N 页全屏演播，自动识别总页数并同步更新翻页状态（`1 / N`）。
   - 点击顶部工具栏 **「📽️ 演示模式」**（或按快捷键 `P`，或 URL 附带 `?present=1`）进入演播模式。
   - 响应式等比铺满浏览器视口（自适应屏幕分辨率，彻底消除黑边与背景留白）。
   - 快捷键支持：`←` / `→` 或 `Space` 翻页，`F` 进入全屏，`Esc` 退出；鼠标点击左/右半屏直接切页。
4. **工作周日期严格约束与智能校验系统**：
   - **周一至周五标准工作周**：Timeline 中的每周日期严格要求为周一至周五（Python `weekday() == 0` 到 `4`），杜绝大模型凭空猜测日历导致的星期偏移。
   - **智能推导与报错诊断**：运行生成脚本时自动校验日历，提供详细告警并附带推算后的标准周一至周五区间建议。
   - **命令行支持**：提供 `--check-dates`（仅校验）、`--fix-dates`（自动对齐纠正）与 `--strict-dates`（严格报错中断）。
5. **全页面大标题与副标题动态渲染 & 智能自适应**：
   - Slide 2、3、4 的大标题（`title`）与副标题（`subtitle`）全面支持从输入 JSON 动态传入。
   - **自动范围推导**：若未显式指定副标题或沿用了旧模板默认值，生成器将自动根据实际周列表智能推导周期（如自适应更新为 `(W1 - W8)`），并优先保留用户自定义的阶段目标说明。
6. **多企业风格定义 (Theme System)**：
   - 基于 CSS Custom Properties，内置 6 款预设企业主题：`classic-navy`（阿斯利康蓝）、`tech-blue`（科技蓝）、`corporate-crimson`（华为/联想红）、`emerald-forest`（ESG森绿）、`cyber-purple`（数智紫）、`minimal-slate`（极简灰）。
   - 网页端支持侧边栏抽屉一键实时换肤，内置实时 JSON 编辑器并支持即时重新渲染。
7. **用于邮件提交的 16:9 矢量 PDF 导出**：
   - 精准 `@media print` 媒体查询，一页幻灯片严格对应一页 PDF，无内容截断或溢出。
   - 支持网页一键打印与 Python 无头 Chrome 自动化静默导出。

---

### 2. 快速使用

```bash
cd skills/weekly-report-generator

# 1. 常规编译生成 HTML 周报
python3 scripts/generate_report.py \
  --data examples/sample_data.json \
  --theme classic-navy \
  --output weekly-report.html

# 2. 仅校验时间轴日期合法性（不生成 HTML）
python3 scripts/generate_report.py --data examples/sample_data.json --check-dates

# 3. 自动将非标准日期对齐为周一至周五并生成报告
python3 scripts/generate_report.py --data your_data.json --fix-dates --output weekly-report.html

# 4. 导出为高清 16:9 矢量 PDF 附件（依赖本地 Chrome）
python3 scripts/export_pdf.py \
  --input weekly-report.html \
  --output weekly-report.pdf
```

---

### 3. Agent 周报生成最佳实践 (Agent Best Practices)

当驱动 AI Agent 自动生成周报 JSON 数据时，请特别注意以下设计原则：

#### ① Timeline 日期生成规则
- 严禁凭空估算日期！Agent 应通过 Python 准确推导目标年份的目标工作周：
  ```python
  import datetime
  d = datetime.date(2026, 9, 16)
  mon = d - datetime.timedelta(days=d.weekday()) # 周一
  fri = mon + datetime.timedelta(days=4)          # 周五
  dates = f"{mon.month}.{mon.day}-{fri.month}.{fri.day}" # "9.14-9.18"
  ```
- 法定节假日周（如国庆、春节等）必须设置 `"isHoliday": true` 并提供 `"holidayName": "国庆假期"`，甘特图将自动渲染贯通金色高亮列。

#### ② 交付物看板 (Slide 3) vs 本周任务 (Slide 4) 职责边界
- **Slide 3（Deliverables / Output Status）**：**仅填写主要成果物与战略级里程碑门禁**（如需求确认、核心系统开发完成、SIT/UAT 验收签收、上线发布 Go-Live 等，通常 5~10 项），**严禁记录琐碎的细节开发进展**。
- **Slide 4（This Week / Task Management）**：记录微观战术任务，包括日常联调细节、具体 bug 修复进展、下周行动项与即时风险。

---

### 4. 详细规范与文档链接

- 技能指令说明（Agent Prompting）：[`skills/weekly-report-generator/SKILL.md`](./skills/weekly-report-generator/SKILL.md)
- 数据格式与输入指南：[`skills/weekly-report-generator/references/input_format_guide.md`](./skills/weekly-report-generator/references/input_format_guide.md)
- JSON 数据 Schema 规范：[`skills/weekly-report-generator/references/data_schema.md`](./skills/weekly-report-generator/references/data_schema.md)
- 示例数据集：[`skills/weekly-report-generator/examples/sample_data.json`](./skills/weekly-report-generator/examples/sample_data.json)

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
