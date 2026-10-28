# 🛡️ AGY & Claude Code Crash Guard + Cross-IDE Session Sync Kit (v2.0)

**Stop losing 500+ step coding sessions to permanent `HTTP 400 INVALID_ARGUMENT` and `30.000MB message limit` trajectory poisoning.**

Built by **HM Shihabuddin Jashory (Shihab)** — [Vision Flow](https://visionflowgroup.com)

---

## ⚡ 1. Install via AI Agent (Claude Code, Antigravity, Cursor, Codex)
Paste this single prompt into your AI coding agent:
> **Prompt:** `Clone https://github.com/jashory/agy-claude-crash-guard-kit and run "python install.py" to install the Crash Guard hooks, Session Sync, and Agent Skill.`

## 💻 2. Install via CLI (Terminal / Skills CLI / pip)
```bash
# Option A: Agent Skills CLI (Claude Code / Antigravity / Cursor)
npx skills add jashory/agy-claude-crash-guard-kit

# Option B: Direct Git Clone + 1-Command Installer (Installs Hooks + Skills)
git clone https://github.com/jashory/agy-claude-crash-guard-kit.git
cd agy-claude-crash-guard-kit && python install.py

# Option C: Global CLI Tool via pip / uv
pip install git+https://github.com/jashory/agy-claude-crash-guard-kit.git
```

---

## 🔥 Why Coding Agents Crash Permanently (And How This Fixes It)

When an AI coding agent (**Google Antigravity**, **Claude Code**, or **Cursor**) calls `read_file` or `Read` on:
1. A **Password-Protected PDF** (bank statement, encrypted invoice),
2. A **0-byte or Fake-HTML corrupted image** downloaded via `curl`/`adb pull`, or
3. Repeated **4K uncompressed PNG screenshots (`>450 KB`)**,

the raw binary is permanently appended into `transcript.jsonl`. Every subsequent retry re-sends that poisoned history, bricking the entire conversation with `HTTP 400 INVALID_ARGUMENT` or `The message size exceeds 30.000MB limit`.

### What's Inside This Kit
1. **`crash_guard.py` (Full 760-Line Engine)**:
   - **`PreToolUse` Firewall**: Blocks locked PDFs, 0-byte media, fake HTML-disguised images, and `>450 KB` uncompressed screenshots *before* they enter `transcript.jsonl`, returning an exact Python workaround command to the agent.
   - **Loop-Safe `Stop` Verification Gate**: Ensures the agent runs a practical verification command after editing source code before claiming completion (fires at most once per turn—never causes `/goal` infinite loops).
   - **Dark-Mode Crash Doctor GUI (`--diagnose auto`)**: Parses `transcript.jsonl` and `language_server.log` to pinpoint the exact step and file that caused an error, with 1-click recovery prompt copy.
2. **`session_sync.py` (Cross-IDE Session Memory Bridge)**:
   - Automatically syncs missing conversation turns between **Claude Desktop App** and **Claude Code VS Code / Antigravity IDE** via the `UserPromptSubmit` hook without duplicate injection.
3. **`SKILL.md` + `install.py` + `pyproject.toml`**:
   - Works both as an autonomous Agent Skill and as a standalone CLI (`agy-crash-guard`).
