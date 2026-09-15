# Weekly Report JSON Data Schema Guide

This document describes the structured JSON schema used to feed the Weekly Report Generator skill (`weekly-report-generator`).

## Schema Overview

```json
{
  "theme": "classic-navy | tech-blue | corporate-crimson | emerald-forest | cyber-purple | minimal-slate",
  "company": {
    "name": "string - Company or Business Unit Name",
    "logoText": "string - 2-4 letter logo badge acronym (e.g. 'AZ', 'TECH', 'HW')",
    "department": "string - Department or PMO team name"
  },
  "project": {
    "title": "string - Full project title",
    "reportTitle": "string - Defaults to 'Weekly Report'",
    "projectCode": "string - Project identifier (e.g. 'PRJ-2024-Q1')",
    "reporter": "string - Reporter or team name",
    "reportDate": "string - Date format YYYY-MM-DD",
    "period": "string - Period text (e.g. 'Week 16 (2024.04.01 ～ 2024.04.03)')",
    "currentWeek": "string - Week identifier matching plan (e.g. 'W16')"
  },
  "slide1_cover": {
    "title": "string - Cover title",
    "subtitle": "string - Cover subtitle",
    "period": "string - Cover period",
    "meta": [
      { "label": "string", "value": "string" }
    ]
  },
  "slide2_plan": {
    "title": "Work Plan —Overview",
    "subtitle": "string",
    "currentWeek": "W16",
    "weAreHereLabel": "We are here",
    "weeks": [
      { "id": "W6", "name": "W6", "dates": "1.22-1.26" },
      { "id": "W9", "name": "W9", "dates": "2.12-2.17", "isHoliday": true, "holidayName": "春节假期" },
      { "id": "W16", "name": "W16", "dates": "4.1-4.5", "isCurrent": true }
    ],
    "rows": [
      {
        "workstream": "string - e.g. '手机端搭建'",
        "category": "string - e.g. '系统开发&测试'",
        "task": "string - e.g. '系统开发'",
        "spans": [
          { "start": "W10", "end": "W13", "type": "completed" },
          { "start": "W14", "end": "W16", "type": "active" }
        ],
        "stars": ["W17"]
      }
    ]
  },
  "slide3_deliverables": {
    "title": "Deliverables / Output Status",
    "subtitle": "string",
    "items": [
      {
        "milestone": "string - Milestone name",
        "progress": "string - Details on current progress",
        "date": "string - Expected date",
        "status": "已完成 | 进行中 | 未开始",
        "risk": "good | caution | risk | none"
      }
    ]
  },
  "slide4_tasks": {
    "title": "Task Management",
    "subtitle": "Week 16：4.1～4.3，2024",
    "overallStatus": "good | caution | risk",
    "previousTasks": [
      {
        "index": 1,
        "tag": "系统开发",
        "content": "系统开发，手机端功能收尾。"
      }
    ],
    "nextSteps": [
      {
        "index": 1,
        "tag": "系统实现",
        "content": "手机端功能联调，掌上AZ&翻译API。"
      }
    ],
    "risks": [
      {
        "index": 1,
        "tag": "",
        "content": "首页部分功能变更，整体timeline预计4月底前可以完成。"
      }
    ],
    "milestones": [
      {
        "name": "Key milestone description or '-'",
        "date": "YYYY.MM.DD or '-'"
      }
    ]
  }
}
```

## Theme Presets
- `classic-navy`: Original AstraZeneca Navy Blue corporate style (`#005587`, `#001847`).
- `tech-blue`: Modern Enterprise Blue (`#2563eb`, `#1e3a8a`).
- `corporate-crimson`: Executive Red / Huawei / Lenovo style (`#b91c1c`, `#7f1d1d`).
- `emerald-forest`: Green energy, ESG, healthcare style (`#047857`, `#064e3b`).
- `cyber-purple`: AI, tech, cloud innovation purple (`#7c3aed`, `#4c1d95`).
- `minimal-slate`: Monochrome minimalist executive slate (`#334155`, `#0f172a`).
