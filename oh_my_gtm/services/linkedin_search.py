"""Standalone LinkedIn browser search collection for the daemon workflow."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Callable

from oh_my_gtm.config import AppSettings
from oh_my_gtm.schemas import LinkedInCollectedItem, LinkedInSearchResult, LinkedInSearchSpec, VisibleCaptureItem
from oh_my_gtm.services.chrome_linkedin import ChromeLinkedInCollector


Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _default_runner(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


class LinkedInSearchClient:
    def __init__(
        self,
        settings: AppSettings,
        *,
        runner: Runner | None = None,
        chrome_collector: ChromeLinkedInCollector | None = None,
    ) -> None:
        self.settings = settings
        self.runner = runner or _default_runner
        self.chrome_collector = chrome_collector or ChromeLinkedInCollector(settings)

    def collect(self, spec: LinkedInSearchSpec) -> LinkedInSearchResult:
        if self.settings.linkedin_collection_strategy in {"auto", "chrome_existing"} and self.chrome_collector.available:
            try:
                return self.chrome_collector.collect(spec)
            except Exception:
                if self.settings.linkedin_collection_strategy == "chrome_existing":
                    raise
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "linkedin_search_collector.py"
        artifact_dir = Path(self.settings.output_dir) / "linkedin-search"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / f"{spec.vertical}-{spec.query.replace(' ', '_')[:48]}.json"
        cmd = self._python_command(
            script_path,
            [
                "--query",
                spec.query,
                "--vertical",
                spec.vertical,
                "--limit",
                str(spec.limit),
                "--profile-dir",
                self.settings.linkedin_browser_profile_dir,
                "--artifact-path",
                str(artifact_path),
                "--headless",
                "1" if self.settings.linkedin_search_headless else "0",
            ],
        )
        completed = self.runner(cmd)
        if completed.returncode != 0:
            error_text = completed.stderr.strip() or completed.stdout.strip() or "LinkedIn search collector failed."
            raise RuntimeError(error_text)
        payload = json.loads(completed.stdout.strip())
        payload["artifact_path"] = payload.get("artifact_path") or str(artifact_path)
        return LinkedInSearchResult.model_validate(payload)

    def open_login_browser(self, *, wait_ms: int = 300000) -> dict | None:
        if self.settings.linkedin_collection_strategy in {"auto", "chrome_existing"} and self.chrome_collector.available:
            return self.chrome_collector.start_managed_login_browser()
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "linkedin_search_collector.py"
        cmd = self._python_command(
            script_path,
            [
                "--mode",
                "login",
                "--profile-dir",
                self.settings.linkedin_browser_profile_dir,
                "--wait-ms",
                str(wait_ms),
                "--headless",
                "0",
            ],
        )
        completed = self.runner(cmd)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "LinkedIn login warmup failed.")
        try:
            return json.loads(completed.stdout.strip())
        except json.JSONDecodeError:
            return {"status": "login_browser_closed", "profile_dir": self.settings.linkedin_browser_profile_dir}

    def _python_command(self, script_path: Path, args: list[str]) -> list[str]:
        return [sys.executable, str(script_path), *args]


def collected_result_to_capture_items(result: LinkedInSearchResult) -> list[VisibleCaptureItem]:
    items: list[VisibleCaptureItem] = []
    for item in result.items:
        metadata = {
            "query": result.query,
            "vertical": result.vertical,
            "search_url": result.search_url,
            "artifact_path": result.artifact_path,
        }
        if result.vertical == "companies":
            items.append(
                VisibleCaptureItem(
                    item_type="company_page",
                    text=item.raw_text,
                    author_name=item.entity_name,
                    company_name=item.entity_name,
                    role=item.title or "Company search result",
                    source_url=item.entity_url,
                    engagement_type="search_result",
                    metadata=metadata,
                )
            )
            continue
        items.append(
            VisibleCaptureItem(
                item_type="profile",
                text=item.raw_text,
                author_name=item.entity_name,
                company_name=item.company_name,
                role=item.title,
                profile_url=item.entity_url,
                source_url=item.entity_url,
                engagement_type="search_result",
                metadata={**metadata, "location": item.location, "action_label": item.action_label},
            )
        )
    return items


def normalize_collected_payload(payload: dict) -> LinkedInSearchResult:
    items = [LinkedInCollectedItem.model_validate(item) for item in payload.get("items", [])]
    return LinkedInSearchResult(
        query=payload["query"],
        vertical=payload["vertical"],
        search_url=payload["search_url"],
        page_title=payload.get("page_title", ""),
        items=items,
        captured_at=payload.get("captured_at"),
        artifact_path=payload.get("artifact_path"),
    )
