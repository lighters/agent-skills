# 🤖 Agent Skills Hub (`agent-skills`)

<p align="center">
  <a href="https://github.com/lighters/agent-skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.8+-3776AB.svg?logo=python&logoColor=white" alt="Python">
  <a href="https://github.com/lighters/agent-skills/actions/workflows/ci.yml"><img src="https://github.com/lighters/agent-skills/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://lighters.github.io/agent-skills/"><img src="https://img.shields.io/badge/Live_Demo-GitHub_Pages-orange?logo=github" alt="Live Demo"></a>
  <a href="https://github.com/lighters/agent-skills/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

> **通用 AI Agent 技能仓库 (Universal AI Agent Skills Hub)**：面向主流自动化智能体框架（Claude Code、Cursor、Google Antigravity、Roo Code、Windsurf、Cline 及自定义 Agent 系统），遵循开放技能标准（`SKILL.md` + 标准化脚本工具链），提供生产级、开箱即用的专业工作流扩展技能。

> ⚡ **零第三方依赖 (Zero External Dependencies)**：核心引擎完全基于 Python 标准库（`json`, `re`, `datetime`, `argparse`）构建，**无需 `pip install` 任何第三方包**，开箱即用。

---

## 🎨 视觉效果预览 (Visual Previews)

> 💡 **在线交互体验**：无需安装或 Clone，直接访问 👉 [**在线体验 Live Demo (GitHub Pages)**](https://lighters.github.io/agent-skills/)  
> （在在线网页中按 `P` 键进入影院级全屏演示，按 `E` 键直接修改文字，右上角抽屉可一键换肤）

| Slide 1: 沉浸式高管汇报封面 (Cover) | Slide 2: 端到端计划甘特图 (Work Plan Timeline) |
| :---: | :---: |
| ![Slide 1 Cover](./docs/assets/slide1_cover_preview.png) | ![Slide 2 Gantt](./docs/assets/slide2_gantt_preview.png) |
| **Slide 3: 交付物健康度看板 (Deliverables)** | **Slide 4: 任务执行与两周里程碑 (Tasks)** |
| ![Slide 3 Deliverables](./docs/assets/slide3_deliverables_preview.png) | ![Slide 4 Tasks](./docs/assets/slide4_tasks_preview.png) |

---

## 📦 技能目录 (Skill Catalog)

| 技能名称 (Skill) | 目录路径 | 描述说明 | 依赖环境 |
| :--- | :--- | :--- | :--- |
| **`weekly-report-generator`** | [`skills/weekly-report-generator`](./skills/weekly-report-generator) | **企业高保真周报与演示文稿生成器**：1:1 复刻麦肯锡、埃森哲等顶级咨询与 500 强高管汇报级排版。支持 4 页标准结构 + 自由扩展 Slide 5+ 方案研讨与议题决议页、端到端 Timeline 甘特图自动排版、交付物健康度跟踪、所见即所得直接编辑、影院级全屏演示动效、7 大企业主题及 16:9 矢量 PDF 导出。 | Python 3.8+ (纯标准库) / Google Chrome (可选导出 PDF) |

---

## 🚀 通用安装指南 (Universal Installation)

本仓库遵循通用 Agent 技能规范（基于标准目录结构的 `SKILL.md`、`scripts/`、`templates/`），兼容各类主流智能体运行时及无 Agent 的本地命令行环境。

### 方式一：项目工作区技能 (Project Workspace, 团队共享推荐)

将技能引入任意具体项目的代码库，适合团队协同与版本管理：

```bash
cd your-project/

# 方案 A: 通过 Git Submodule 引入（推荐，便于后续拉取上游技能更新）
mkdir -p .agents/skills
git submodule add https://github.com/lighters/agent-skills.git .agents/skills/agent-skills

# 方案 B: 直接拷贝目标技能目录
mkdir -p .agents/skills/weekly-report-generator
cp -R /path/to/agent-skills/skills/weekly-report-generator/* .agents/skills/weekly-report-generator/
```

### 方式二：用户级全局技能 (User Global Skills, 全系统通用)

在本地机器上克隆一次，即可在所有的项目与 Agent 会话中全局调用：

```bash
# 1. 克隆技能仓库至本地通用目录
git clone https://github.com/lighters/agent-skills.git ~/.agent-skills

# 2. 创建通用全局技能目录并建立软链接
mkdir -p ~/.agent/skills
ln -s ~/.agent-skills/skills/* ~/.agent/skills/
```

#### 主流 Agent 框架一键软链接映射：
根据你所使用的 AI Agent 运行时，将技能软链接至其识别的技能目录即可：

```bash
# Claude Code 全局技能目录
mkdir -p ~/.claude/skills
ln -s ~/.agent-skills/skills/weekly-report-generator ~/.claude/skills/weekly-report-generator

# Google Antigravity / Gemini CLI 全局技能目录
mkdir -p ~/.gemini/antigravity-cli/skills
ln -s ~/.agent-skills/skills/weekly-report-generator ~/.gemini/antigravity-cli/skills/weekly-report-generator

# Cursor / Windsurf / Cline / Roo Code / OpenCode
# 推荐放置在项目根目录的 .agents/skills/ 或在规则中指定路径
```

### 方式三：独立本地命令行使用 (无需 Agent 运行时)

即使不依赖任何 AI Agent，本工具链也可作为标准的 Python CLI 独立运行：

```bash
cd skills/weekly-report-generator

# 一键编译生成独立 HTML 周报
python3 scripts/generate_report.py \
  --data examples/sample_data.json \
  --theme astrazeneca \
  --output weekly-report.html

# 一键导出为 16:9 矢量 PDF（依赖本地 Chrome/Edge 浏览器）
python3 scripts/export_pdf.py \
  --input weekly-report.html \
  --output weekly-report.pdf
```

---

## 🛠️ 技能详解：`weekly-report-generator`

### 1. 核心能力与亮点

1. **PPT 样式 1:1 高保真还原（4 页基础骨架 + Slide 5+ 方案研讨扩展）**：
   - **Slide 1 封面页**：企业 Branding、徽标、项目编号、汇报周期、汇报人、机密等级与整体健康度徽章，搭配沉浸式深色渐变与微透毛玻璃卡片。
   - **Slide 2 整体项目计划 (Work Plan / Timeline)**：端到端甘特图、跨多周任务条带映射、`We are here` 当前周动态红箭头指针、法定节假日金色高亮列、关键里程碑红星（★）。
   - **Slide 3 交付物及状态 (Deliverables / Output Status)**：聚焦项目**主要交付物与战略里程碑门禁**，支持红黄绿风险状态指示（`Good` / `Caution` / `High Risk`）与软胶囊徽标。
   - **Slide 4 本周工作 (Task Management)**：聚焦微观战术任务执行，完全复刻双列卡片（前期工作 / 下周计划 / 风险管理 / 未来两周里程碑）+ 统一行高规范与彩色指示前缀。
   - **Slide 5+ 方案研讨与议题扩展页 (Discussion & Proposal Slides)**：周报后可按需追加任意多页议题页，支持 **方案比选 (`comparison`)**、**卡片矩阵 (`cards`)**、**议题深研 (`agenda`)**、**评估矩阵表格 (`table`)** 与 **自由 HTML (`custom`)** 等多种专业排版，配备方案推荐徽标与底部周会决议卡片。
2. **影院级演播动效与无黑边演示模式 (Presentation Deck Mode)**：
   - **交错入场动画（Staggered Entrance）**：翻页时标题、指标与卡片依次平滑升起，动效自然灵动。
   - **动态微胶囊分页点**：悬浮 HUD 自动适配页面数量，当前页展开为发光胶囊 Pill，支持点击任意点即时跳转。
   - **空闲 2.6s 自动隐匿**：全屏演播时 HUD 智能淡出，100% 呈现无遮挡内容；鼠标轻移或按键瞬间滑出唤醒。
   - **快捷键交互**：`P` 进入演示，`←` / `→` 或 `Space` 翻页，`F` 全屏，`Esc` 退出；鼠标点击左右两侧半屏直接切页。
   - **浮空 Toast 通知**：主题切换、模式切换、保存导出时提供柔和的毛玻璃气泡状态反馈。
3. **所见即所得直接内容编辑 (WYSIWYG Inline Editing)**：
   - **细节改字零阻力**：无需 Agent 重新调用技能编译，点击顶部工具栏 **「✏️ 编辑内容」**（或直接双击页面任意文字，或按快捷键 `E`）即可直接在网页上改写字词或交付物状态。
   - **双向数据同步**：修改内容即时渲染并自动同步回填至嵌入的 JSON 数据中。
   - **一键另存与打印**：点击 **「💾 另存 HTML」** 下载包含所有修改的独立文件；点击 **「导出 PDF / 打印」** 直接打印为矢量 PDF。
4. **工作周日期严格约束与智能校验系统**：
   - **周一至周五标准工作周**：Timeline 中的每周日期严格要求为周一至周五（Python `weekday() == 0` 到 `4`），杜绝大模型猜测日历导致的星期偏移。
   - **智能推导与报错诊断**：运行生成脚本时自动校验日历，提供详细告警并附带推算后的标准周一至周五区间建议。
   - **命令行工具支持**：提供 `--check-dates`（仅校验）、`--fix-dates`（自动对齐纠正）与 `--strict-dates`（严格报错中断）。
5. **7 大企业主题与自定义调色 (Theme System)**：
   - 内置 7 套企业级视觉预设：
     * `astrazeneca`（阿斯利康 · 经典深蓝与洋红）
     * `novartis`（诺华 · 钴蓝与活力暖橙）
     * `bayer`（拜耳 · 经典深蓝与生机绿）
     * `jnj`（强生 · 热情红）
     * `novo-nordisk`（诺和诺德 · 纯蓝与海蓝）
     * `wukong-green`（极客翠绿 · 翠绿生机与赛博青）
     * `vercel-minimal`（Vercel 极简风 · 黑白无衬线）
   - 支持在 JSON 数据中传入 `customTheme` 自定义颜色覆盖，网页端支持侧边栏抽屉一键实时调色。
6. **用于邮件提交的 16:9 矢量 PDF 导出**：
   - 精准 `@media print` 媒体查询，动画与过渡自动安全降级为零延迟矢量排版，一页幻灯片严格对应一页 PDF，无跨页或溢出截断。

---

### 2. 快速使用指令

```bash
cd skills/weekly-report-generator

# 1. 常规编译生成 HTML 周报
python3 scripts/generate_report.py \
  --data examples/sample_data.json \
  --theme astrazeneca \
  --output weekly-report.html

# 2. 仅校验时间轴日期合法性（不生成 HTML）
python3 scripts/generate_report.py --data examples/sample_data.json --check-dates

# 3. 自动将非标准日期对齐为周一至周五并生成报告
python3 scripts/generate_report.py --data your_data.json --fix-dates --output weekly-report.html

# 4. 导出为高清 16:9 矢量 PDF 附件（依赖本地 Chrome/Edge）
python3 scripts/export_pdf.py \
  --input weekly-report.html \
  --output weekly-report.pdf
```

---

### 3. Agent 驱动周报生成最佳实践 (Agent Best Practices)

当驱动任意 AI Agent（Claude Code、Antigravity、Cursor 等）自动构建周报 JSON 数据时，请提示 Agent 遵循以下设计准则：

#### ① Timeline 日期推导规则
- 严禁凭空估算日期！Agent 应使用标准库准确推导目标年份的工作周：
  ```python
  import datetime
  d = datetime.date(2026, 9, 16)
  mon = d - datetime.timedelta(days=d.weekday())  # 周一 (Monday)
  fri = mon + datetime.timedelta(days=4)           # 周五 (Friday)
  dates = f"{mon.month}.{mon.day}-{fri.month}.{fri.day}"  # "9.14-9.18"
  ```
- 法定节假日周（如国庆、春节等）必须设置 `"isHoliday": true` 并提供 `"holidayName": "国庆假期"`，甘特图将自动渲染贯通金色高亮列。

#### ② 交付物看板 (Slide 3) vs 本周任务 (Slide 4) 职责边界
- **Slide 3（Deliverables / Output Status）**：**仅填写主要成果物与战略级里程碑门禁**（如需求确认、核心系统开发完成、SIT/UAT 验收签收、上线发布 Go-Live 等，通常 5~10 项），**严禁记录细碎的日常开发动作**。
- **Slide 4（This Week / Task Management）**：记录微观战术任务，包括日常联调细节、具体功能收尾、下周行动项与即时风险。

---

## 🗺️ 技能路线图 (Skill Roadmap)

Agent Skills Hub 正在持续扩展高频通用工作流，欢迎社区参与共建：

- [x] **`weekly-report-generator`**：高管级周报、甘特图排版、方案研讨与 16:9 PDF 生成
- [ ] **`meeting-minutes-extractor`**：基于会议转录文本，自动提炼决策结论、行动项（Action Items）并分配责任人
- [ ] **`code-review-reporter`**：针对多文件 Git Diff 自动生成结构化代码审查报告与重构建议
- [ ] **`release-notes-generator`**：基于 Git Commit 与 PR 规范，全自动提取版本发布日志与变更说明
- [ ] **`adr-generator`**：软件架构决策记录（Architecture Decision Record）自动化生成与维护

---

## 📝 扩展新技能 (Contributing)

欢迎贡献更多通用 Agent Skills！每个新技能遵循通用开放技能标准，详情请查阅 [CONTRIBUTING.md](./CONTRIBUTING.md)：

```text
skills/<skill-name>/
├── SKILL.md            # 包含 YAML frontmatter (name, description) 与执行手册
├── README.md           # 人类可读使用指南与 CLI 命令行说明
├── scripts/            # 跨平台自动化脚本与工具链
├── templates/          # 模板与配置资源
├── examples/           # 样例输入与生成产出
└── references/         # 详细规范文档与数据模型说明
```

---

## 📄 开源许可

MIT License © 2024-2026 [lighters](https://github.com/lighters)
