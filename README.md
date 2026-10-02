# AI Skills

[![skills.sh](https://skills.sh/b/naufalgholib/ai-skills)](https://skills.sh/naufalgholib/ai-skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

A curated collection of modular, production-grade AI agent skills designed for coding agents ([Claude Code](https://claude.ai/code), [Oh My Pi](https://github.com), [Codex](https://github.com), and [Cursor](https://cursor.com)).

These skills condense real-world engineering workflows, automation scripts, and best practices into composable agent capabilities.

Inspired by [mattpocock/skills](https://github.com/mattpocock/skills).

---

## Quick Installation

### 1. Using Skills CLI (Universal)

You can install skills directly into your repository or project using the Skills CLI:

```bash
npx skills@latest add naufalgholib/ai-skills
```

Select the skill(s) you need and target your agent of choice.

### 2. Oh My Pi / Local Agent Harness

Clone or link the skills into your global agent skills directory:

```bash
# Clone the repository
git clone https://github.com/naufalgholib/ai-skills.git ~/ai-skills

# Symlink a skill to Oh My Pi
ln -s ~/ai-skills/skills/media/instagram-moment-extractor ~/.pi/agent/skills/instagram-moment-extractor

# Or symlink to Claude Code
ln -s ~/ai-skills/skills/media/instagram-moment-extractor ~/.claude/skills/instagram-moment-extractor
```

---

## Skills Catalog

### Media

Skills for multimedia manipulation, frame extraction, video sampling, and web asset optimization.

| Skill | Description | Category | Invocation |
|---|---|---|---|
| **[instagram-moment-extractor](./skills/media/instagram-moment-extractor/SKILL.md)** | Extract high-definition visual assets & video frames from Instagram Reels, Stories, Highlights, and Posts with 3-tier fallback access and dual-format PNG lossless + WebP web optimization. | Media | Model / User |

---

## Repository Structure

```
ai-skills/
├── .gitignore
├── AGENTS.md                      # Agent conventions & skill authoring guide
├── LICENSE                        # MIT License
├── README.md                      # Repository overview & catalog
└── skills/                        # Categorized skills
    ├── README.md
    └── media/
        ├── README.md
        └── instagram-moment-extractor/
            ├── SKILL.md           # Core skill instructions & recipes
            ├── agents/
            │   └── openai.yaml    # Agent interface metadata
            └── scripts/
                └── extract_moments.py  # Standalone CLI extraction tool
```

---

## Philosophy

1. **Deterministic & Composable**: Each skill solves a specific, repeatable challenge without needless abstraction.
2. **Real-world Fallbacks**: Skills handle real friction (authentication walls, format variations, rate limits) with clear fallback tiers.
3. **Agent-Optimized**: Guidance is structured with explicit preconditions, triggers, runnable CLI recipes, and observable acceptance criteria.

---

## License

[MIT](./LICENSE) © 2026 Naufal Gholib Shiddiq
