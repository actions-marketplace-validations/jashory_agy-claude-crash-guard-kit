#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Cross-IDE Session Sync (Open-Source Universal Edition)
Author: HM Shihabuddin Jashory (Shihab) — Vision Flow (https://visionflowgroup.com)
License: MIT

Keeps a single Claude Code conversation continuous across multiple apps/IDEs
(e.g. Claude Code Desktop, VS Code extension, Cursor, Antigravity IDE).
When the same session ID is resumed in two different workspace paths, each app
writes to its own transcript copy (`~/.claude/projects/<project>/<session_id>.jsonl`).
This hook detects new messages written in any sibling copy and injects them as
`additionalContext` once—without ever mutating or corrupting the transcript files.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import tempfile

MAX_CONTEXT_CHARS = 8000
MAX_MSG_CHARS = 1800
STATE_DIR = os.environ.get("CLAUDE_SESSION_SYNC_STATE") or os.path.join(
    tempfile.gettempdir(), "claude_session_sync"
)
UUID_RE = re.compile(rb'"uuid"\s*:\s*"([0-9a-fA-F-]{36})"')


def config_dirs() -> list[str]:
    dirs = []
    candidates = [
        os.environ.get("CLAUDE_CONFIG_DIR"),
        os.path.join(os.path.expanduser("~"), ".claude"),
    ]
    for d in candidates:
        if d and os.path.isdir(d):
            real = os.path.realpath(d)
            if real not in [os.path.realpath(x) for x in dirs]:
                dirs.append(d)
    return dirs


def other_copies(session_id: str, transcript_path: str) -> list[str]:
    me = os.path.realpath(transcript_path) if transcript_path else ""
    found, seen = [], {me}
    for cfg in config_dirs():
        for path in glob.glob(os.path.join(cfg, "projects", "*", f"{session_id}.jsonl")):
            real = os.path.realpath(path)
            if real in seen:
                continue
            try:
                if me and os.path.exists(me) and os.path.samefile(real, me):
                    continue
            except OSError:
                pass
            seen.add(real)
            found.append(path)
    return found


def own_uuids(path: str) -> set[str]:
    out: set[str] = set()
    try:
        with open(path, "rb") as f:
            for line in f:
                m = UUID_RE.search(line)
                if m:
                    out.add(m.group(1).decode())
    except OSError:
        pass
    return out


def message_text(row: dict) -> str:
    msg = row.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text") or "")
    return "\n".join(p for p in parts if p.strip())


def new_rows(path: str, known: set[str], injected: set[str]) -> list[dict]:
    rows = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                uid = row.get("uuid")
                if not uid or uid in known or uid in injected:
                    continue
                if row.get("type") not in ("user", "assistant") or row.get("isMeta"):
                    continue
                text = message_text(row).strip()
                if not text:
                    continue
                if row["type"] == "user" and text.startswith("<"):
                    continue
                rows.append({
                    "uuid": uid,
                    "type": row["type"],
                    "ts": str(row.get("timestamp", ""))[:16],
                    "text": text,
                })
    except OSError:
        pass
    return rows


def load_state(session_id: str) -> dict:
    try:
        with open(os.path.join(STATE_DIR, f"{session_id}.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(session_id: str, state: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = os.path.join(STATE_DIR, f"{session_id}.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, os.path.join(STATE_DIR, f"{session_id}.json"))


def build_context(source: str, rows: list[dict]) -> str:
    lines, used = [], 0
    for r in reversed(rows):
        text = r["text"] if len(r["text"]) <= MAX_MSG_CHARS else r["text"][:MAX_MSG_CHARS] + " ...[cut]"
        entry = f"[{r['ts']}] {'USER' if r['type'] == 'user' else 'CLAUDE'}: {text}"
        if used + len(entry) > MAX_CONTEXT_CHARS and lines:
            break
        lines.append(entry)
        used += len(entry)
    lines.reverse()
    skipped = len(rows) - len(lines)
    head = (
        "SESSION SYNC: this same chat was also continued in another Claude Code window/IDE. "
        f"Messages present in that copy but not in this one ({len(rows)} total) follow, oldest first:\n"
        f"Source copy: {source}\n"
    )
    if skipped:
        head += f"({skipped} older messages omitted for context budget.)\n"
    return head + "\n".join(lines)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    session_id = str(payload.get("session_id") or "")
    transcript = str(payload.get("transcript_path") or "")
    event = str(payload.get("hook_event_name") or "UserPromptSubmit")
    if not session_id:
        return
    copies = other_copies(session_id, transcript)
    if not copies:
        return
    state = load_state(session_id)
    seen_files = state.setdefault("files", {})
    injected = set(state.get("injected", []))

    changed = []
    for path in copies:
        try:
            st = os.stat(path)
        except OSError:
            continue
        sig = f"{st.st_size}:{int(st.st_mtime)}"
        if seen_files.get(path) != sig:
            changed.append((path, sig))
    if not changed:
        return

    known = own_uuids(transcript) if transcript else set()
    blocks = []
    for path, sig in changed:
        rows = new_rows(path, known, injected)
        seen_files[path] = sig
        if rows:
            blocks.append(build_context(path, rows))
            injected.update(r["uuid"] for r in rows)
    state["injected"] = sorted(injected)[-50000:]
    save_state(session_id, state)
    if blocks:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": event,
                        "additionalContext": "\n\n".join(blocks),
                    }
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
