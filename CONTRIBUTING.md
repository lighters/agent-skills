# Contributing to Agent Skills Hub

Thank you for your interest in contributing to **Agent Skills Hub (`agent-skills`)**!

This repository aims to provide production-ready, universal skills for all modern AI coding agents (Claude Code, Cursor, Google Antigravity, Windsurf, Roo Code, Cline, etc.) as well as standalone CLI tools.

---

## 🎯 Code of Conduct & Principles

1. **Universal Compatibility (普适性)**: Skills must follow open, standard directory structures (`SKILL.md`, `scripts/`, `templates/`, `references/`) and work across multiple agent runtimes.
2. **Minimal Dependencies (零繁琐依赖)**: Tool scripts should prefer standard libraries or widely available runtimes (Python 3.8+ built-ins, standard shell utilities).
3. **Deterministic & Production Quality**: Instructions in `SKILL.md` must be clear, actionable, and resilient against model hallucinations (e.g., date constraints, schema validation).

---

## 🛠️ Adding a New Skill

Each skill resides under the `skills/<skill-name>/` directory with the following structure:

```text
skills/<skill-name>/
├── SKILL.md            # Required: YAML frontmatter + agent execution runbook
├── README.md           # Required: Human-readable usage guide and CLI instructions
├── scripts/            # Executable scripts and automation tooling
├── templates/          # Templates, CSS/HTML, theme definitions
├── examples/           # Sample inputs and generated output artifacts
└── references/         # Data schemas, format guides, specifications
```

### Skill Definition Guidelines (`SKILL.md`)
- Keep frontmatter concise with a clear `name` and `description` explaining *when* the agent should invoke this skill.
- Provide step-by-step guidance for the agent to follow before, during, and after execution.
- Include explicit error handling and constraint checks.

---

## 🔄 Development Workflow

1. **Fork the repository** on GitHub.
2. **Create a feature branch**:
   ```bash
   git checkout -b feat/my-new-skill
   ```
3. **Test locally**:
   - Verify that your scripts run without external dependency errors.
   - If modifying `weekly-report-generator`, test compilation:
     ```bash
     python3 skills/weekly-report-generator/scripts/generate_report.py \
       --data skills/weekly-report-generator/examples/sample_data.json \
       --output /tmp/test.html
     ```
4. **Commit with Conventional Commits**:
   - `feat(skill-name): add ...`
   - `fix(skill-name): resolve ...`
   - `docs: update ...`
5. **Push and open a Pull Request**.

---

## 📝 Reporting Issues

- For bugs or broken templates, please open a Bug Report issue.
- For proposing new skills or themes, please use the Feature Request or New Skill Request template.
