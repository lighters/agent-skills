# 钉钉项目工时获取

从已授权的钉钉宜搭应用查询、导出并核对项目工时，生成项目和人员投入底稿。适用于“某些项目有哪些人、各投入多少小时”“补查审批中记录”“导出全部历史工时”等请求。

## 能力与边界

- 按项目编码、时间、人员及状态核实查询范围，导出全部匹配结果。
- 对照工时明细报表和运行中记录，核对遗漏与重复；不能确认的记录单列待核，不强行合计。
- 展开父子表，只累加工时明细；保留实例、源文件、源行号、获取时间及审批口径，避免父合计重复计数。
- 默认交付 Excel：项目汇总、人员投入、工时明细、口径与异常。保留原始导出供本地追溯。
- 不填报、提交或审批工时，不保存共享筛选，不从日历估算实际工时。缺少实际成本率及适用口径时，不将工时换算成货币成本。

这是指令型工作流，没有独立 CLI、内置宜搭连接器或自动执行脚本。查询需要实际可用且已授权的 API／CLI 或浏览器工具；文件处理需要当前环境的表格读取与制作能力。运行环境、登录权限和企业配置决定能否执行，安装 Skill 本身不提供这些能力。

[宜搭操作参考](references/yida-export.md) 包含云程应用的已观察入口、项目编码和表头，仅适用于对应公司上下文；其他公司必须重新确认。页面提示和字段可能变化，每次操作以当前页面和导出文件为准。

## 安装

在仓库根目录执行对应命令。使用 Codex 的 `CODEX_HOME`，未设置时使用用户目录下的 `.codex`；更新已有安装前保留自行修改的副本。

macOS（Bash／Zsh）：

```bash
skill_target="${CODEX_HOME:-$HOME/.codex}/skills/dingtalk-project-hours"
mkdir -p "$skill_target"
cp -R skills/dingtalk-project-hours/. "$skill_target/"
```

Windows（PowerShell）：

```powershell
$skillHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$skillTarget = Join-Path $skillHome 'skills/dingtalk-project-hours'
New-Item -ItemType Directory -Path $skillTarget -Force | Out-Null
Copy-Item -Path './skills/dingtalk-project-hours/*' -Destination $skillTarget -Recurse -Force
```

其他 Agent 按其技能目录机制安装本目录。安装后重新开始会话或使用运行时支持的重载机制。

## 使用示例

```text
用 $dingtalk-project-hours 获取指定项目 2026 年 9 月的人员工时，
包含审批中记录并核对重复，输出项目汇总、人员投入和可追溯明细 Excel。
```

也可要求全部历史工时或仅已审批记录；后者必须有明确审批证据。“全部”限于确认的查询条件及当前账号可见记录，不代表未填写或无权限查看的工时。

## 验证边界

安装和发布检查覆盖 Skill 格式、元数据、相对链接、源文件保真、统计规则静态推演与安装副本一致性。本次未运行真实宜搭查询／导出，也未执行 Windows 或 PowerShell 实测；这些检查不证明当前会话权限或线上端到端可用。核心规则见 [SKILL.md](SKILL.md)。
