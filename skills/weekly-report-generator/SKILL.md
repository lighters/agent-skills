---
name: weekly-report-generator
description: >-
  Generate high-fidelity, presentation-grade HTML and PDF weekly reports based on enterprise PPT templates (e.g. Weekly Report Sample-v1.pptx). Features 4 slides (Cover, Gantt Work Plan Overview, Deliverables & Status, and Task Management 1:1 PPT layout), 100% vector PDF export for email attachments, and enterprise theme customization (CSS variables, multiple presets).
---

# Weekly Report Generator (企业高阶周报生成器)

This skill provides an automated workflow to produce professional corporate weekly reports matching the visual and structural fidelity of enterprise management presentations (`Weekly Report Sample-v1.pptx`).

---

## 1. 结构化输入格式规范 (Input Data Specification)

每一页的内容均支持由结构化 JSON 数据驱动并自动计算生成。完整规范详见 [input_format_guide.md](./references/input_format_guide.md)。

### Timeline（项目整体计划甘特图）输入格式
其他 Agent 生成 Timeline 时，无需关心复杂的 HTML 表格合并，只需输入周列表与任务清单：

```json
{
  "timeline": {
    "title": "Work Plan —Overview",
    "subtitle": "端到端执行计划及进度跟踪",
    "currentWeek": "W16",                  // 自动生成 "▲ We are here" 红色指针
    "weAreHereText": "We are here",
    
    // 1. 周定义（支持假期金色高亮列）
    "weeks": [
      { "id": "W6", "name": "W6", "dates": "1.22-1.26" },
      { "id": "W9", "name": "W9", "dates": "2.12-2.17", "isHoliday": true, "holidayName": "春节假期" },
      { "id": "W16", "name": "W16", "dates": "4.1-4.5" }
    ],

    // 2. 任务清单（自动识别相同 workstream 和 category 进行单元格合并）
    "tasks": [
      {
        "workstream": "手机端搭建",
        "category": "系统设计",
        "task": "原型设计与确认",
        "start": "W6",
        "end": "W7",
        "status": "completed",             // "completed" (已完成浅蓝), "active" (在途深蓝), "planned" (计划)
        "milestone": false                 // 或指定周 ID 如 "W7" 打红星 ★
      },
      {
        "workstream": "手机端搭建",
        "category": "系统开发&测试",
        "task": "系统开发",
        "spans": [                         // 跨多阶段的任务支持 spans 数组
          { "start": "W10", "end": "W13", "status": "completed" },
          { "start": "W14", "end": "W16", "status": "active" }
        ],
        "milestone": "W17"
      }
    ]
  }
}
```

### 交付物状态 (`deliverables`) 输入格式
```json
{
  "deliverables": {
    "title": "Deliverables / Output Status",
    "items": [
      {
        "milestone": "手机端&web端重点功能系统开发完成",
        "progress": "完成行业大会和临床研究模块搭建，手机端调整中。",
        "date": "2024.4.12",
        "status": "进行中",
        "risk": "caution" // "good" (🟢), "caution" (🟡), "risk" (🔴), "none" (-)
      }
    ]
  }
}
```

### 本周工作 (`thisWeek`) 输入格式 (1:1 复刻 PPT 样式)
```json
{
  "thisWeek": {
    "subtitle": "Week 16：4.1～4.3，2024",
    "overallStatus": "caution",
    "previousTasks": [
      { "tag": "系统开发", "content": "系统开发，手机端功能收尾。" },
      { "tag": "变更处理", "content": "首页设计基于讨论做了更新，待确认。" }
    ],
    "nextSteps": [
      { "tag": "系统实现", "content": "手机端功能联调，掌上AZ&翻译API。" }
    ],
    "risks": [
      { "tag": "", "content": "首页部分功能变更，整体timeline预计4月底前可以完成。" }
    ],
    "milestones": [
      { "name": "-", "date": "-" }
    ]
  }
}
```

---

## 2. Agent 调用运行手册 (Runbook)

### 方式一：Python 脚本生成与编译 (推荐)

```bash
# 生成指定主题的 HTML
python3 scripts/generate_report.py \
  --data your_data.json \
  --theme classic-navy \
  --output weekly-report.html

# 自动导出为高保真 PDF 用于邮件发送
python3 scripts/export_pdf.py \
  --input weekly-report.html \
  --output weekly-report.pdf
```

### 方式二：网页中交互式数据输入与即时生成
打开生成的 `weekly-report.html`，点击顶部导航栏中的 **「📝 输入数据与生成」**，可在弹出的 JSON 面板中直接编辑任务或粘贴新数据，点击 **「即时计算生成全套周报」** 即可瞬间重新渲染包含 Timeline 甘特图在内的所有 4 页。

---

## 3. 企业主题适配说明
支持通过 `--theme` 参数或页面下拉菜单切换：
- `classic-navy`: 经典企业蓝 (对应原 PPT 阿斯利康 Astra 风格)
- `tech-blue`: 现代科技蓝
- `corporate-crimson`: 商务中国红 (华为/联想)
- `emerald-forest`: 自然与新能源绿 (ESG)
- `cyber-purple`: 未来数智紫 (AI)
- `minimal-slate`: 极简极客灰

---

## 4. 文件导航

- [generate_report.py](./scripts/generate_report.py): 动态生成脚本
- [export_pdf.py](./scripts/export_pdf.py): 无头 Chrome PDF 导出脚本
- [weekly_report_template.html](./templates/weekly_report_template.html): 核心模板与浏览器计算渲染引擎
- [sample_data.json](./examples/sample_data.json): 标准输入样例数据
- [input_format_guide.md](./references/input_format_guide.md): 详尽输入格式规范指南
