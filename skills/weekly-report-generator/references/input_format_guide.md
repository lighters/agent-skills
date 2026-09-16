# 周报数据输入格式与 Timeline 生成规范 (Weekly Report Input Format Guide)

本文档详细说明每一页周报内容的输入格式规范。其他 Agent 或业务系统只需按照此 JSON 结构提供数据，即可通过生成脚本或 HTML 页面自动生成完整的 4 页周报（包含自动计算排版的端到端 Timeline 甘特图）。

---

## 1. 整体数据结构概览

```json
{
  "theme": "classic-navy",
  "company": { ... },
  "project": { ... },
  "timeline": { ... },
  "deliverables": { ... },
  "thisWeek": { ... }
}
```

---

## 2. 详细页面输入格式

### 第 1 页：封面页 (`company` & `project`)

封面页展示企业信息、项目标识、汇报周期和元数据网格。

```json
{
  "company": {
    "name": "AstraZeneca / 数字化交付中心",     // 企业或组织名称
    "logoText": "AZ",                          // Logo 徽标字母缩写（2-4字符）
    "department": "商业技术交付团队"              // 所属部门或团队
  },
  "project": {
    "title": "手机端搭建与 Web 端优化项目",        // 项目全称
    "reportTitle": "Weekly Report",             // 报告主标题（默认 Weekly Report）
    "projectCode": "PRJ-2024-AZ-Q1",            // 项目编号
    "period": "Week 16 (2024.04.01 ～ 2024.04.03)", // 汇报周期文本
    "reporter": "项目交付组 (AZ Team)",           // 汇报人 / 团队
    "reportDate": "2024-04-03",                 // 报告发布日期
    "confidential": "CONFIDENTIAL · 内部汇报"    // 密级说明
  }
}
```

---

### 第 2 页：Timeline 整体项目计划甘特图 (`timeline`)

Timeline 是核心复杂图表，支持**按周时间轴**定义、**多工作流与任务分组**、**执行阶段条带**、**特殊假期金色高亮列**、**关键里程碑星标（★）**以及**当前周（We are here）指针**。

#### 核心规范：Work Plan 周日期（周一至周五）与法定节假日约束（Agent 必读）

为确保周报项目计划时间轴的专业性与准确性，所有 Agent 在生成 `timeline.weeks[]` 时必须严格遵循以下日历约束：

1. **严格周一至周五标准工作周**：
   - 每一周的 `dates` 必须代表**周一到周五**的日期区间，标准格式为 `M.D-M.D`（如 `9.14-9.18`、`10.12-10.16`），跨年时可写作 `YYYY.M.D-YYYY.M.D`。
   - 起始日期必须为**周一**（Python `weekday() == 0`），结束日期必须为**周五**（Python `weekday() == 4`）。
   - **禁止凭空捏造日历日期**（例如将周二至周六误当作工作周）。Agent 在填充日期前请通过 Python `datetime` 计算准确的周一与周五：
     ```python
     import datetime
     d = datetime.date(2026, 9, 16)
     mon = d - datetime.timedelta(days=d.weekday()) # 周一
     fri = mon + datetime.timedelta(days=4)          # 周五
     dates = f"{mon.month}.{mon.day}-{fri.month}.{fri.day}" # "9.14-9.18"
     ```

2. **法定节假日规范标注 (`isHoliday` & `holidayName`)**：
   - 当项目跨越国家法定节假日（如国庆假期、春节假期、劳动节、中秋节、端午节、清明节、元旦等）且该周整体放假调休时：
     - 必须设置 `"isHoliday": true`
     - 必须设置 `"holidayName": "国庆假期"`（或 `"春节假期"` 等）
   - 引擎会自动将节假日列高亮为金色贯通条带，并垂直居中呈现假期名称。

#### Timeline 输入结构：

```json
{
  "timeline": {
    "title": "Work Plan —Overview",             // 页面大标题
    "subtitle": "端到端执行计划及进度跟踪 (W6 - W20)", // 副标题
    "currentWeek": "W16",                       // 当前周标识，自动生成 "▲ We are here" 指针
    "weAreHereText": "We are here",             // 指针说明文本

    // 1. 时间轴周定义 (按列排序，严格周一至周五或法定节假日)
    "weeks": [
      { "id": "W6", "name": "W6", "dates": "1.22-1.26" },
      { "id": "W7", "name": "W7", "dates": "1.29-2.2" },
      { "id": "W8", "name": "W8", "dates": "2.5-2.9" },
      { "id": "W9", "name": "W9", "dates": "2.12-2.16", "isHoliday": true, "holidayName": "春节假期" },
      { "id": "W10", "name": "W10", "dates": "2.19-2.23" },
      { "id": "W11", "name": "W11", "dates": "2.26-3.1" },
      { "id": "W12", "name": "W12", "dates": "3.4-3.8" },
      { "id": "W13", "name": "W13", "dates": "3.11-3.15" },
      { "id": "W14", "name": "W14", "dates": "3.18-3.22" },
      { "id": "W15", "name": "W15", "dates": "3.25-3.29" },
      { "id": "W16", "name": "W16", "dates": "4.1-4.5" },
      { "id": "W17", "name": "W17", "dates": "4.8-4.12" },
      { "id": "W18", "name": "W18", "dates": "4.15-4.19" },
      { "id": "W19", "name": "W19", "dates": "4.22-4.26" },
      { "id": "W20", "name": "W20", "dates": "4.29-5.3" }
    ],

    // 2. 任务列表 (自动合并相同 workstream 与 category 的单元格)
    "tasks": [
      {
        "workstream": "手机端搭建",             // 工作流名称（相同工作流自动纵向合并单元格）
        "category": "系统设计",                 // 类别（相同类别自动纵向合并单元格）
        "task": "原型设计与确认",                // 任务名称
        "start": "W6",                         // 起始周 ID
        "end": "W7",                           // 截止周 ID
        "status": "completed",                 // 状态: "completed" (已完成浅蓝), "active" (在途深蓝), "planned" (计划执行)
        "milestone": false                     // 是否设置里程碑星标，可设为 true 或具体的周 ID 如 "W7"
      },
      {
        "workstream": "手机端搭建",
        "category": "系统开发&测试",
        "task": "系统开发",
        // 多阶段任务可使用 spans 数组指定不同阶段：
        "spans": [
          { "start": "W10", "end": "W13", "status": "completed" },
          { "start": "W14", "end": "W16", "status": "active" }
        ],
        "milestone": "W17"                     // 在 W17 列上打红星 ★
      }
    ]
  }
}
```

#### Timeline 自动生成逻辑：
1. **自动单元格合并 (`rowspan`)**：生成引擎会扫描 `workstream` 与 `category`，自动计算合并跨度，无需手动写 HTML `rowspan`。
2. **特殊假期列自动识别**：只要 `isHoliday: true`，该列会被自动渲染为纵向金色条带，并垂直居中显示 `holidayName`（如“春节假期”）。支持时间轴中包含多个节假日周。
3. **指针自动定位**：在 `currentWeek` 所在列的底部自动锚定红箭头与 `We are here`。
4. **里程碑星标渲染**：若指定了 `milestone: "Wxx"`，系统会在该任务的对应周格中渲染红星 ★。

---

### 第 3 页：交付物及状态 (`deliverables`)

#### 核心定位与编写指引（Agent 必读：重大交付物/里程碑 vs 细节任务）

第 3 页是面向高管层、业务负责人和 PMO 的**主要成果物交付与里程碑健康度仪表盘**。

- **核心原则**：这里**仅跟进项目的主要交付物或阶段性重要里程碑**，**切勿填写琐碎的细节任务进展**。
- **职责边界区分（Slide 3 vs Slide 4）**：
  - **Slide 3（Deliverables / Output Status）**：宏观视角，关注战略成果与阶段门禁（如：需求基线签收、高保真确认、核心系统开发完成、UAT验收、上线发布）。
  - **Slide 4（This Week / Task Management）**：微观战术视角，记录本周具体开发动作、问题排查、联调细节和下周执行事项。

#### 范例对比（应该写什么 vs 不应该写什么）：

| 阶段 | ✅ 适合写在 Slide 3（主要交付物/重大里程碑） | ❌ 严禁写在 Slide 3（属于 Slide 4 细节任务） |
| :--- | :--- | :--- |
| **需求阶段** | 业务需求规格说明书 (PRD) 评审与确认 | 梳理了 5 个会员模块的接口字段与字典值 |
| **设计阶段** | 系统高保真交互与视觉设计确认 | 优化了登录弹窗遮罩层的透明度样式 |
| **开发阶段** | 手机端&Web端核心功能系统开发完成 | 手机端对接翻译 API，处理 500 报错与重试逻辑 |
| **测试阶段** | 全链路集成测试 (SIT) 完成与准出 | 提交了 12 个 bug，跟进修复其中 10 个 |
| **验收阶段** | 业务验收测试 (UAT) 签收通过 | 组织销售运营团队召开 1 小时 UAT 培训会 |
| **上线阶段** | 生产环境系统正式上线 (Go-Live) | 运维配置 Nginx 反向代理与 SSL 证书续期 |

#### Deliverables 输入结构：

```json
{
  "deliverables": {
    "title": "Deliverables / Output Status",
    "subtitle": "关键交付节点与成果物健康度评估",
    "items": [
      {
        "milestone": "手机端&web端重点功能系统开发完成", // 主要交付物/重要里程碑名称（清晰、可验收）
        "progress": "完成行业大会和临床研究模块搭建，手机端调整中。", // 宏观进展（1~2句概括现状/卡点，未开始填 "-"）
        "date": "2024.4.12",                      // 目标交付/验收日期 (YYYY.M.D 或 M.D)
        "status": "进行中",                        // 宏观状态："已完成" / "进行中" / "未开始"
        "risk": "caution"                         // 风险等级："good" (🟢 无风险), "caution" (🟡 需关注), "risk" (🔴 严重延期风险), "none" (-)
      },
      {
        "milestone": "手机端&web端重点功能系统UAT",
        "progress": "-",
        "date": "2024.4.19",
        "status": "未开始",
        "risk": "none"
      },
      {
        "milestone": "手机端&web端重点功能系统Go-live",
        "progress": "-",
        "date": "2024.4.26",
        "status": "未开始",
        "risk": "none"
      }
    ]
  }
}
```

---

### 第 4 页：本周工作 (`thisWeek`) - 完全复刻 PPT 样式

完全对齐原 PPT 第 4 页的两列卡片 + 右上角状态徽标 + 底部图例。

```json
{
  "thisWeek": {
    "title": "Task Management",
    "subtitle": "Week 16：4.1～4.3，2024",
    "overallStatus": "caution",                 // "good" (🟢 如期进行), "caution" (🟡 有问题但不影响), "risk" (🔴 重大问题)

    // 左列卡片 1: 前期重点工作
    "previousTasks": [
      { "tag": "系统开发", "content": "系统开发，手机端功能收尾。" },
      { "tag": "变更处理", "content": "首页设计基于讨论做了更新，待确认。" }
    ],

    // 左列卡片 2: 下周计划重点
    "nextSteps": [
      { "tag": "系统实现", "content": "手机端功能联调，掌上AZ&翻译API。" }
    ],

    // 右列卡片 1: 风险管理
    "risks": [
      { "tag": "", "content": "首页部分功能变更，整体timeline预计4月底前可以完成。" }
    ],

    // 右列下方表格: 未来两周关键里程碑
    "milestones": [
      { "name": "-", "date": "-" }
    ]
  }
}
```

---

## 3. 生成方法

### 方式 A：使用 Python 脚本生成 (推荐 Agent 使用)
```bash
# 1. 常规生成（脚本会自动校验周一至周五日期与节假日标注，若有问题会输出高亮警示与推导建议）
python3 scripts/generate_report.py \
  --data your_weekly_data.json \
  --theme classic-navy \
  --output weekly-report.html

# 2. 仅进行时间轴日期与节假日合法性校验（不生成 HTML）：
python3 scripts/generate_report.py --data your_weekly_data.json --check-dates

# 3. 自动将非节假日日期纠正对齐为周一至周五标准区间：
python3 scripts/generate_report.py --data your_weekly_data.json --fix-dates --output weekly-report.html

# 4. 严格校验模式（若日期非周一至周五直接报错中断）：
python3 scripts/generate_report.py --data your_weekly_data.json --strict-dates
```

### 方式 B：在网页中实时输入并生成 (交互预览)
1. 用浏览器打开 `weekly-report.html`。
2. 点击顶部栏中的 **「📝 输入数据与生成」** 按钮。
3. 弹出 JSON 编辑器，粘贴或修改您的数据（包含修改 Timeline 的任务与周期）。
4. 点击 **「即时渲染周报」**，所有页面（包括 Timeline 甘特图）立即实时重新计算并渲染。
5. 点击 **「导出 PDF」** 即可获取最新周报。
