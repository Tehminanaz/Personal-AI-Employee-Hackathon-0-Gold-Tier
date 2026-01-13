# 👁️ Vision 2026: The Digital FTE Sentinel

**Current Status:** _Gold Tier Operational_ 🥇
**Version:** 3.0 (Fully Autonomous & Self-Auditing)
**Last Verified:** 2026-01-12

> "The first automated employee that checks its own work."

---

## 🌎 Overview

The **Digital FTE Sentinel** is an enterprise-grade autonomous operation system that lives in your filesystem. It transforms a standard folder structure into a cognitive processing engine, capable of executing complex workflows, auditing its own performance, and interacting with the real world (Email, LinkedIn, APIs).

Unlike a chatbot, the Sentinel is **persistent**, **state-aware**, and **proactive**.

## 🏗️ Architecture

The system operates on a file-based event loop:

### 1. The Sentinel Loop (`orchestrator.py`)
- **Monitors** `00_Inbox/` for new tasks (Markdown files).
- **Analyzes** intent using the "Council of Experts":
    - 🏛️ **Chief of Staff** (Strategy & Briefings)
    - 🗣️ **Comm Strategist** (Content & Social)
    - 💰 **Financial Controller** (Xero & Accounting)
    - 🛠️ **Web Executor** (Code & Dev)
    - 🛡️ **Safety Guardrail** (Ethics & Compliance)
    - 📊 **Data Analyst** (Decision Science)
    - 📅 **Project Manager** (Agile & Roadmap)
    - 🚀 **Growth Hacker** (Marketing & SEO)
    - 🧠 **Learning Specialist** (Research & Synthesis)
- **Plans & Drafts** content in `01_Needs_Action/`.
- **Verifies** quality using automated tests.
- **Approves** final outputs to `03_Approved/`.

### 2. The Execution Layer (`action_executor.py`)
- **Watches** `03_Approved/` for actionable tasks.
- **Executes** external actions safely (Gmail, API calls, Scripts).
- **Logs** every action to `Logs/Action_Logs.json`.
- **Archives** completed tasks to `04_Archive/`.

### 3. The Perception Layer (`gmail_watcher.py`)
- **Scans** incoming emails for specific triggers.
- **Converts** emails into formatted task files in `00_Inbox/`.
- **Closes the loop** between communication and execution.

---

## 🚀 Key Features (Gold Tier)

### ✅ Autonomous Execution
- **Robust File Handling**: strict naming conventions and path resilience.
- **Safe Triggers**: `GMAIL_SEND_` prefix enforcement for high-risk actions.
- **System Health Checks**: `VERIFICATION_` triggers for self-diagnostics.

### 🧠 Chief of Staff Mode
- **Weekly CEO Briefing**: Automated generation of "Amazon-style" 6-page narrative reports.
- **Success Rate Auditing**: Calculates performance metrics from `Action_Logs.json`.
- **Strategic Planning**: Narratives over powerpoint.

### 🛡️ Safety & Auditing
- **UTF-8 Logging**: Full support for emojis and special characters in logs.
- **Visible Audit Trail**: Real-time logging to `Logs/` directory.
- **Human-in-the-Loop**: Critical actions require file movement to `03_Approved/`.

---

## 📂 Directory Structure

| Directory | Purpose |
|-----------|---------|
| `00_Inbox/` | Entry point for new tasks (User or Email) |
| `01_Needs_Action/` | AI-generated plans awaiting review |
| `02_Pending_Approval/` | Final drafts ready for sign-off |
| `03_Approved/` | **THE RED BUTTON**. Files here execute immediately. |
| `04_Archive/` | Storage for completed/executed tasks |
| `Logs/` | System logs and Audit JSONs |
| `.claude/skills/` | The "Brain" (Skill definitions) |

---

## 💻 Quick Start

### 1. Start the System
```powershell
# Start the Orchestrator (The Brain)
python orchestrator.py

# Start the Watcher (The Eyes - Optional)
python gmail_watcher.py
```

### 2. Create a Task
Drop a file into `00_Inbox/`:
```markdown
# TASK: Weekly Finance Report
Please analyze the attached CSV and generate a summary.
```

### 3. Trigger an Audit (CEO Mode)
Drop a file into `00_Inbox/`:
```markdown
# TASK: Generate CEO Audit
Run the generate_weekly_audit command.
```

---

*Powered by Advanced Agentic Coding - Google Deepmind*
