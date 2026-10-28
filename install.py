#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1-Command Cross-Platform Installer for AGY & Claude Crash Guard + Session Sync
Author: HM Shihabuddin Jashory (Shihab) — Vision Flow (https://visionflowgroup.com)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

def install_to_target(target_home: str) -> dict:
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    install_dir = os.path.join(target_home, ".visionflow-agent-guard")
    os.makedirs(install_dir, exist_ok=True)

    cg_dst = os.path.join(install_dir, "crash_guard.py")
    ss_dst = os.path.join(install_dir, "session_sync.py")
    shutil.copy2(os.path.join(pkg_dir, "crash_guard.py"), cg_dst)
    shutil.copy2(os.path.join(pkg_dir, "session_sync.py"), ss_dst)

    py_cmd = sys.executable.replace("\\", "/")
    cg_cmd = f'"{py_cmd}" "{cg_dst.replace(chr(92), "/")}"'
    ss_cmd = f'"{py_cmd}" "{ss_dst.replace(chr(92), "/")}"'

    # 1. Configure Claude Code (~/.claude/settings.json)
    claude_dir = os.path.join(target_home, ".claude")
    os.makedirs(claude_dir, exist_ok=True)
    claude_settings_path = os.path.join(claude_dir, "settings.json")
    claude_cfg = {}
    if os.path.exists(claude_settings_path):
        try:
            with open(claude_settings_path, "r", encoding="utf-8") as f:
                claude_cfg = json.load(f)
        except Exception:
            claude_cfg = {}

    hooks = claude_cfg.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])
    guard_entry = {
        "matcher": "Read|read_file|view_file",
        "hooks": [{"type": "command", "command": f"{cg_cmd} --event ClaudePreToolUse"}],
    }
    if not any("crash_guard.py" in json.dumps(x) for x in pre_tool):
        pre_tool.append(guard_entry)

    prompt_submit = hooks.setdefault("UserPromptSubmit", [])
    sync_entry = {
        "matcher": ".*",
        "hooks": [{"type": "command", "command": ss_cmd}],
    }
    if not any("session_sync.py" in json.dumps(x) for x in prompt_submit):
        prompt_submit.append(sync_entry)

    with open(claude_settings_path, "w", encoding="utf-8") as f:
        json.dump(claude_cfg, f, indent=2, ensure_ascii=False)

    # 2. Install Skill into ~/.claude/skills/crash-and-binary-guard/SKILL.md
    skill_dir = os.path.join(claude_dir, "skills", "crash-and-binary-guard")
    os.makedirs(skill_dir, exist_ok=True)
    skill_src = os.path.join(pkg_dir, "SKILL.md")
    if os.path.exists(skill_src):
        shutil.copy2(skill_src, os.path.join(skill_dir, "SKILL.md"))

    return {
        "status": "installed",
        "install_dir": install_dir,
        "claude_settings": claude_settings_path,
        "skill_path": os.path.join(skill_dir, "SKILL.md"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", default=os.path.expanduser("~"), help="Target home directory")
    args = parser.parse_args()
    res = install_to_target(args.home)
    print(json.dumps(res, indent=2))
