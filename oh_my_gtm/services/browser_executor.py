"""Execute policy-safe Playwright browser plans for LinkedIn copilot flows."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

from oh_my_gtm.config import AppSettings
from oh_my_gtm.schemas import LinkedInAgentPlan, LinkedInExecutionResult


ALLOWED_PLAYWRIGHT_VERBS = {"open", "snapshot", "screenshot"}
BLOCKED_TOKENS = {"click", "type", "fill", "press", "drag", "run-code", "evaluate"}


def _playwright_wrapper_path() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills" / "playwright" / "scripts" / "playwright_cli.sh"


def _artifact_dir(settings: AppSettings) -> Path:
    target = Path(settings.output_dir) / "playwright" / datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    target.mkdir(parents=True, exist_ok=True)
    return target


def execute_linkedin_plan(
    plan: LinkedInAgentPlan,
    settings: AppSettings,
    *,
    dry_run: bool = True,
) -> LinkedInExecutionResult:
    wrapper = _playwright_wrapper_path()
    artifact_dir = _artifact_dir(settings)
    env = os.environ.copy()
    env["PWCLI"] = str(wrapper)

    executed_steps: list[str] = []
    outputs: list[dict] = []
    for command in plan.playwright_commands:
        normalized = command.strip()
        if not normalized or normalized.startswith("#") or normalized.startswith("export "):
            continue
        if any(token in normalized for token in BLOCKED_TOKENS):
            outputs.append({"command": normalized, "status": "blocked", "reason": "unsafe_playwright_action"})
            continue
        if not any(f" {verb} " in normalized or normalized.endswith(f" {verb}") for verb in ALLOWED_PLAYWRIGHT_VERBS):
            outputs.append({"command": normalized, "status": "skipped", "reason": "unsupported_playwright_action"})
            continue
        executed_steps.append(normalized)
        if dry_run:
            outputs.append({"command": normalized, "status": "dry_run"})
            continue
        result = subprocess.run(
            normalized,
            shell=True,
            cwd=Path.cwd(),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        outputs.append(
            {
                "command": normalized,
                "status": "completed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-2000:],
            }
        )

    status = "prepared" if dry_run else "completed"
    if any(output.get("status") == "failed" for output in outputs):
        status = "failed"
    return LinkedInExecutionResult(
        status=status,
        dry_run=dry_run,
        executed_steps=executed_steps,
        outputs=outputs,
        artifact_dir=str(artifact_dir),
        final_send_blocked=plan.final_send_blocked,
    )
