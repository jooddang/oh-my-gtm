"""Use Chrome on macOS for LinkedIn collection, including a reusable daemon-managed browser."""

from __future__ import annotations

import json
import platform
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import quote

import httpx
from playwright.sync_api import sync_playwright

from oh_my_gtm.config import AppSettings
from oh_my_gtm.schemas import LinkedInCollectedItem, LinkedInSearchResult, LinkedInSearchSpec


Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _default_runner(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _collect_items_js() -> str:
    return """
const limit = __LIMIT__;
const vertical = "__VERTICAL__";
const ignored = new Set(["Connect", "Follow", "Message", "View profile", "View company profile"]);
function parsePeopleCard(card) {
  const link = card.querySelector('a[href*="/in/"]');
  if (!link) return null;
  const text = (card.innerText || "").trim();
  const lines = text.split("\\n").map((line) => line.trim()).filter(Boolean);
  const roleLine = lines.find((line) =>
    !line.startsWith("View ") &&
    !line.includes("degree connection") &&
    !line.startsWith("·") &&
    !line.endsWith("followers") &&
    !ignored.has(line) &&
    line !== lines[0]
  ) || "";
  const locationLine = lines.find((line) =>
    line !== lines[0] &&
    line !== roleLine &&
    !line.startsWith("View ") &&
    !line.includes("degree connection") &&
    !line.startsWith("·") &&
    !line.endsWith("followers") &&
    !ignored.has(line)
  ) || "";
  const actionLabel = Array.from(card.querySelectorAll("button, a"))
    .map((node) => (node.textContent || "").trim())
    .find((value) => ignored.has(value)) || "";
  const companyMatch = roleLine.match(/\\bat\\s+(.+)$/i);
  return {
    vertical: "people",
    entity_name: lines[0] || "",
    entity_url: link.href,
    raw_text: text,
    lines,
    title: roleLine,
    company_name: companyMatch ? companyMatch[1] : "",
    location: locationLine,
    action_label: actionLabel,
  };
}
function parseCompanyCard(card) {
  const link = card.querySelector('a[href*="/company/"]');
  if (!link) return null;
  const text = (card.innerText || "").trim();
  const lines = text.split("\\n").map((line) => line.trim()).filter(Boolean);
  return {
    vertical: "companies",
    entity_name: lines[0] || "",
    entity_url: link.href,
    raw_text: text,
    lines,
    title: lines[1] || "",
    company_name: lines[0] || "",
    location: lines[2] || "",
    action_label: "",
  };
}
const parser = vertical === "companies" ? parseCompanyCard : parsePeopleCard;
return Array.from(document.querySelectorAll("main ul li")).map((card) => parser(card)).filter(Boolean).slice(0, limit);
    """.strip()


@dataclass
class ChromeLinkedInCollector:
    settings: AppSettings
    runner: Runner = _default_runner

    @property
    def available(self) -> bool:
        return platform.system() == "Darwin" and shutil.which("osascript") is not None

    @property
    def session_file(self) -> Path:
        return Path(self.settings.linkedin_browser_profile_dir) / "cdp_session.json"

    def start_managed_login_browser(self) -> dict:
        if not self.available:
            raise RuntimeError("Managed Chrome login is only supported on macOS.")
        profile_dir = Path(self.settings.linkedin_browser_profile_dir).resolve()
        profile_dir.mkdir(parents=True, exist_ok=True)
        port = _free_port()
        command = [
            "open",
            "-na",
            self.settings.chrome_app_name,
            "--args",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            "https://www.linkedin.com/feed/",
        ]
        launched = subprocess.run(command, capture_output=True, text=True, check=False)
        if launched.returncode != 0:
            raise RuntimeError(launched.stderr.strip() or launched.stdout.strip() or "Failed to launch Chrome.")
        self._wait_for_cdp(port)
        payload = {
            "port": port,
            "profile_dir": str(profile_dir),
            "browser_app": self.settings.chrome_app_name,
            "created_at": time.time(),
        }
        self.session_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def active_session(self) -> dict | None:
        if not self.session_file.exists():
            return None
        try:
            payload = json.loads(self.session_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        port = payload.get("port")
        if not isinstance(port, int):
            return None
        try:
            response = httpx.get(f"http://127.0.0.1:{port}/json/version", timeout=2.0)
            response.raise_for_status()
        except Exception:
            return None
        return payload

    def collect(self, spec: LinkedInSearchSpec) -> LinkedInSearchResult:
        session = self.active_session()
        if session:
            return self._collect_via_cdp(spec, session["port"])
        return self._collect_via_applescript(spec)

    def _collect_via_cdp(self, spec: LinkedInSearchSpec, port: int) -> LinkedInSearchResult:
        search_url = f"https://www.linkedin.com/search/results/{spec.vertical}/?keywords={quote(spec.query)}"
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            try:
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = context.new_page()
                try:
                    page.goto(search_url, wait_until="domcontentloaded")
                    page.wait_for_timeout(4000)
                    items = page.evaluate(_collect_items_js().replace("__LIMIT__", str(spec.limit)).replace("__VERTICAL__", spec.vertical))
                    return LinkedInSearchResult(
                        query=spec.query,
                        vertical=spec.vertical,
                        search_url=page.url,
                        page_title=page.title(),
                        items=[LinkedInCollectedItem.model_validate(item) for item in items],
                        captured_at=page.evaluate("() => new Date().toISOString()"),
                    )
                finally:
                    page.close()
            finally:
                browser.close()

    def _collect_via_applescript(self, spec: LinkedInSearchSpec) -> LinkedInSearchResult:
        search_url = f"https://www.linkedin.com/search/results/{spec.vertical}/?keywords={quote(spec.query)}"
        script = self._build_script(search_url, spec.limit, spec.vertical)
        completed = self.runner(["osascript", "-e", script])
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Chrome collector failed.")
        payload = json.loads(completed.stdout.strip())
        return LinkedInSearchResult(
            query=spec.query,
            vertical=spec.vertical,
            search_url=payload.get("search_url", search_url),
            page_title=payload.get("page_title", ""),
            items=[LinkedInCollectedItem.model_validate(item) for item in payload.get("items", [])],
            captured_at=payload.get("captured_at"),
        )

    def _wait_for_cdp(self, port: int) -> None:
        last_error = None
        for _ in range(30):
            try:
                response = httpx.get(f"http://127.0.0.1:{port}/json/version", timeout=1.0)
                response.raise_for_status()
                return
            except Exception as exc:  # pragma: no cover - transient startup path
                last_error = exc
                time.sleep(0.5)
        raise RuntimeError(f"Chrome remote debugging port {port} did not become ready: {last_error}")

    def _build_script(self, search_url: str, limit: int, vertical: str) -> str:
        parser_js = _collect_items_js().replace("__LIMIT__", str(limit)).replace("__VERTICAL__", vertical)
        parser_js = parser_js.replace("\\", "\\\\").replace('"', '\\"')
        search_url_escaped = search_url.replace('"', '\\"')
        app_name = self.settings.chrome_app_name.replace('"', '\\"')
        return f'''
set targetUrl to "{search_url_escaped}"
set scrapeJs to "{parser_js}"
tell application "{app_name}"
    activate
    if (count of windows) = 0 then
        make new window
    end if
    tell front window
        set newTab to make new tab with properties {{URL:targetUrl}}
        set active tab index to (count of tabs)
    end tell
    delay 6
    set payload to execute active tab of front window javascript scrapeJs
    close active tab of front window
end tell
return payload
        '''.strip()
