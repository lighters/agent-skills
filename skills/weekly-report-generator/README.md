# Weekly Report Generator（企业高阶周报生成器）

> 基于结构化 JSON 自动生成高保真企业级 HTML 与 16:9 矢量 PDF 周报的 Antigravity 技能。1:1 复刻麦肯锡、埃森哲等顶级咨询及世界 500 强高管汇报 PPT 视觉标准。

---

## 🌟 核心特性

- **四页标准基础骨架 + 灵活扩展 Slide 5+ 方案研讨页**：
  1. **Slide 1 封面页 (Cover)**：企业 Branding、项目编码、周期、汇报人、机密等级与整体健康度徽章。
  2. **Slide 2 项目总体计划 (Work Plan Overview)**：端到端甘特图、跨多周任务条带映射、`We are here` 当前周指示箭头、法定节假日金色高亮列、关键里程碑星标（★）。
  3. **Slide 3 交付物及状态 (Deliverables / Output Status)**：聚焦战略级主要交付物与核心里程碑门禁，红黄绿健康度指示灯。
  4. **Slide 4 本周工作 (Task Management)**：微观战术执行，前期重点工作、下周工作计划、风险管理双列卡片 + 状态徽标。
  5. **Slide 5+ 方案研讨与议题扩展页 (Discussion & Proposal Slides)**：支持在周报后追加任意多页讨论页，提供 **方案比选 (`comparison`)**、**卡片矩阵 (`cards`)**、**议题深研 (`agenda`/`deep-dive`)**、**评估矩阵表格 (`table`)** 与 **自由 HTML (`custom`)** 等企业级布局，配备推荐徽标与底部周会决议卡片。
- **✏️ 所见即所得直接内容编辑 (WYSIWYG Inline Editing)**：
  - **细节改字零阻力**：无需 Agent 重新跑一遍 skill 生成，点击顶部 **「✏️ 编辑内容」**（或直接双击页面任意文字，或按 `E`）即可直接在网页上修改错别字、润色一句话或修改交付物状态。
  - **双向数据同步**：修改后的文字不仅即时更新 DOM，还会自动同步回填至嵌入的 JSON 数据状态中。
  - **一键另存与打印**：点击 **「💾 另存 HTML」** 可一键下载保存包含修改的完整 HTML；点击 **「导出 PDF / 打印」** 即刻输出最新矢量 PDF。
- **📽️ 全屏无黑边演示模式 (Presentation Deck Mode)**：
  - 支持动态 1 至 N 页全屏演播，自动识别并更新页码标签（`1 / N`）。
  - 点击工具栏 **「演示模式」** 或按快捷键 `P` 进入，按 `F` 全屏，`←` / `→` 或 `Space` 翻页，`Esc` 退出。
  - 响应式等比缩放自适应浏览器视口，彻底消除黑边与背景留白。
- **📅 周一至周五工作周严格约束与智能日期校验**：
  - 时间轴日期严格要求为周一至周五（Python `weekday() == 0` 到 `4`），杜绝大模型日期幻觉。
  - 内置自动校验机制，支持 `--check-dates`（校验）、`--fix-dates`（自动对齐纠正）与 `--strict-dates`（严格模式）。
- **🏷️ 全页面标题/副标题动态自适应**：
  - 支持自定义所有页面的大标题与副标题，未指定时自动根据实际周列表自适应计算周期区间（如 `(W1 - W8)`）。
- **🎨 6 款企业主题换肤系统**：
  - 内置 `classic-navy`、`tech-blue`、`corporate-crimson`、`emerald-forest`、`cyber-purple`、`minimal-slate`。
  - 网页端支持侧边栏抽屉实时换肤与即时 JSON 编辑渲染。
- **📄 16:9 矢量 PDF 导出**：
  - 严格 `@media print` 媒体查询，一页幻灯片对应一页 PDF（无论 4 页还是 N 页），无溢出截断。

---

## 🚀 命令行快速上手

```bash
# 1. 常规编译生成 HTML 周报
python3 scripts/generate_report.py \
  --data examples/sample_data.json \
  --theme classic-navy \
  --output weekly-report.html

# 2. 仅校验时间轴日期与节假日合法性
python3 scripts/generate_report.py --data examples/sample_data.json --check-dates

# 3. 自动纠正非标准日期为周一至周五并生成报告
python3 scripts/generate_report.py --data your_data.json --fix-dates --output weekly-report.html

# 4. 导出为高清 16:9 矢量 PDF 附件（依赖本地 Chrome）
python3 scripts/export_pdf.py \
  --input weekly-report.html \
  --output weekly-report.pdf
```

---

## 📂 目录结构与关键文件

```text
skills/weekly-report-generator/
├── SKILL.md                          # Antigravity 技能说明与 Agent 执行规范 (必读)
├── README.md                         # 技能概述与使用手册
├── scripts/
│   ├── generate_report.py            # 周报核心 HTML 编译引擎（支持日期校验与自动修正）
│   └── export_pdf.py                 # 无头 Chrome 矢量 PDF 导出脚本
├── templates/
│   ├── weekly_report_template.html   # 高保真 PPT 4 页响应式 HTML 模板
│   └── theme-presets.json            # 6 款企业主题调色板配置
├── examples/
│   ├── sample_data.json              # 基础范例数据（包含多工作流、多阶段甘特条与节假日）
│   ├── weekly-report.html            # 编译生成的示范周报
│   └── weekly-report.pdf             # 导出的示范矢量 PDF
└── references/
    ├── input_format_guide.md         # 周报 JSON 数据输入格式与甘特图排版详细指南
    └── data_schema.md                # JSON Schema 字段定义规范
```

---

## 📖 详细文档

- **Agent 技能指令与执行约束**：[`SKILL.md`](./SKILL.md)
- **JSON 输入格式与排版指南**：[`references/input_format_guide.md`](./references/input_format_guide.md)
- **Schema 字段说明**：[`references/data_schema.md`](./references/data_schema.md)
