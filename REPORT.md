# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

**Q: What is the agentic loop?**

A: The agentic loop is the core reasoning cycle that autonomous AI agents follow to accomplish tasks. It's typically described as:

**Observe → Think → Act**

1. **Observe** — Gather information from the environment (user input, tool outputs, external data)
2. **Think** — Process the information, reason about next steps, make decisions
3. **Act** — Execute actions (call tools, send messages, modify files, etc.)

Then the loop repeats with the new observations from the action's results.

Extended variations add learning and reflection:
- Perceive → Reason → Act → Learn
- Goal → Plan → Act → Observe → Reflect

**Q: What labs are available in our LMS?**

A: The available labs in the LMS are:

| Lab | Title | Focus |
|-----|-------|-------|
| Lab 4 | Testing, Front-end, and AI Agents | Back-end development for the LMS, testing, and AI agent integration |
| Lab 5 | Data Pipeline & Analytics Dashboard | Data engineering, populating databases, building analytics and visualizations |
| Lab 6 | Build Your Own Agent | Creating a CLI agent that reads docs and queries the backend API |
| Lab 7 | Build a Client with an AI Coding Agent | Building a Telegram bot with LLM-powered interactions for the LMS |
| Lab 8 | The Agent is the Interface | Setting up nanobot as an AI interface for natural language queries about the system |

## Task 1B — Agent with LMS tools

**Q: What labs are available?**

A: The agent returned 8 labs from the LMS backend:
- Lab 01: Products, Architecture & Roles
- Lab 02: Run, Fix, and Deploy a Backend Service
- Lab 03: Backend API: Explore, Debug, Implement, Deploy
- Lab 04: Testing, Front-end, and AI Agents
- Lab 05: Data Pipeline and Analytics Dashboard
- Lab 06: Build Your Own Agent
- Lab 07: Build a Client with an AI Coding Agent
- Lab 08: lab-08

**Q: Describe the architecture of the LMS system**

A: The LMS architecture consists of:

**Client Layer:** Swagger UI, React Frontend, External Clients (Telegram Bot)

**Caddy (Reverse Proxy):** Routes requests, TLS termination, static file serving

**FastAPI Application:** 
- Routers: /items, /interactions, /learners
- Authentication: API Key verification
- Database Layer: async SQL queries

**PostgreSQL Database:** Stores items, interactions, learners

**pgAdmin:** Database management GUI

**Request Flow:** Client → Caddy → FastAPI (auth + routing) → Database → PostgreSQL → Response

## Task 1C — Skill prompt

**Skill file:** `nanobot/workspace/skills/lms/SKILL.md`

The skill prompt teaches the agent:
- Which `lms_*` tools are available and when to use each
- To ask for lab parameter when not provided
- To format numeric results nicely (percentages, counts)
- To keep responses concise
- How to explain capabilities when asked "what can you do?"

**Expected behavior for "Show me the scores":**
The agent should ask which lab or list available labs instead of returning all scores.

*Note: Qwen API daily quota exceeded during testing. Verify when quota resets.*

## Task 2A — Deployed agent

**Nanobot startup log excerpt:**

```
nanobot-1  | Using config: /app/nanobot/config.resolved.json
nanobot-1  | 🐈 Starting nanobot gateway version 0.1.4.post5 on port 18790...
nanobot-1  |   Created HEARTBEAT.md
nanobot-1  |   Created AGENTS.md
nanobot-1  |   Created TOOLS.md
nanobot-1  |   Created SOUL.md
nanobot-1  |   Created USER.md
nanobot-1  |   Created memory/MEMORY.md
nanobot-1  |   Created memory/HISTORY.md
nanobot-1  | 2026-03-27 11:36:41.164 | INFO | nanobot.heartbeat.service:start:122 - Heartbeat started
nanobot-1  | 2026-03-27 11:36:41.973 | INFO | nanobot.agent.loop:run:260 - Agent loop started
```

**Status:** Nanobot gateway is running in Docker on port 18790. No channels enabled yet (webchat will be added in Part B).

## Task 2B — Web client

<!-- Screenshot of a conversation with the agent in the Flutter web app -->

## Task 3A — Structured logging

<!-- Paste happy-path and error-path log excerpts, VictoriaLogs query screenshot -->

## Task 3B — Traces

<!-- Screenshots: healthy trace span hierarchy, error trace -->

## Task 3C — Observability MCP tools

<!-- Paste agent responses to "any errors in the last hour?" under normal and failure conditions -->

## Task 4A — Multi-step investigation

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

## Task 4C — Bug fix and recovery

<!-- 1. Root cause identified
     2. Code fix (diff or description)
     3. Post-fix response to "What went wrong?" showing the real underlying failure
     4. Healthy follow-up report or transcript after recovery -->
