# Agent Guidelines & Repository Architecture

This repository contains reusable AI agent skills designed for coding agents (Claude Code, Oh My Pi, Codex, Cursor, etc.).

## Skills Organization

Skills are organized into domain bucket folders under `skills/`:

- `media/`: multimedia processing, asset extraction, video manipulation, web optimization
- `engineering/`: software architecture, testing, refactoring, CI/CD (future skills)
- `productivity/`: workflow automation, research, planning (future skills)

### Anatomy of a Skill

Each skill directory (`skills/<bucket>/<skill-name>/`) follows standard agent skill packaging:

1. `SKILL.md`: Mandatory skill manifest containing:
   - YAML frontmatter with `name` and descriptive `description` explaining triggers and capability
   - Architecture and workflow overview
   - Usage instructions and runnable command recipes
   - Troubleshooting and best practices
2. `scripts/`: Optional standalone CLI helper scripts or utilities required by the skill.
3. `agents/openai.yaml`: Optional metadata defining `display_name` and `short_description` for OpenAI/Codex agent interfaces.

## Skill Installation & Distribution

Skills are distributed via the open agent skills ecosystem:

- **Skills CLI (`skills.sh`)**:
  ```bash
  npx skills@latest add naufalgholib/ai-skills
  ```
- **Local Harness Linking**:
  Skills can be linked into local agent discovery paths:
  - Oh My Pi: `~/.pi/agent/skills/<skill-name>`
  - Claude Code: `~/.claude/skills/<skill-name>`
  - Codex / Agent tools: `~/.agents/skills/<skill-name>`

## Standards

- Always keep paths generic and relative; never commit hardcoded local home paths or credentials.
- Ensure scripts run cleanly in modern environments (Python 3.10+, Node 20+).
- All documentation follows clean, concise technical prose.
