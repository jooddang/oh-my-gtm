"""Collect LinkedIn search results using Python Playwright."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect LinkedIn search results.")
    parser.add_argument("--mode", default="search", choices=["search", "login"])
    parser.add_argument("--query", default="")
    parser.add_argument("--vertical", default="people", choices=["people", "companies"])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--profile-dir", required=True)
    parser.add_argument("--artifact-path")
    parser.add_argument("--wait-ms", type=int, default=300000)
    parser.add_argument("--headless", default="1")
    return parser.parse_args()


def _build_search_url(query: str, vertical: str) -> str:
    return f"https://www.linkedin.com/search/results/{vertical}/?keywords={quote(query)}"


def _collect_items(page, vertical: str, limit: int) -> list[dict]:
    return page.locator("main ul li").evaluate_all(
        """
        (cards, config) => {
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
          const parser = config.vertical === "companies" ? parseCompanyCard : parsePeopleCard;
          return cards.map((card) => parser(card)).filter(Boolean).slice(0, config.limit);
        }
        """,
        {"vertical": vertical, "limit": limit},
    )


def main() -> None:
    args = _parse_args()
    profile_dir = Path(args.profile_dir).resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)
    headless = args.headless == "1"

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile_dir),
            headless=headless,
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            if args.mode == "login":
                page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
                page.wait_for_timeout(args.wait_ms)
                print(json.dumps({"status": "login_window_closed", "profile_dir": str(profile_dir)}))
                return

            if not args.query:
                raise SystemExit("--query is required in search mode")

            search_url = _build_search_url(args.query, args.vertical)
            page.goto(search_url, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
            items = _collect_items(page, args.vertical, args.limit)
            payload = {
                "query": args.query,
                "vertical": args.vertical,
                "search_url": page.url,
                "page_title": page.title(),
                "items": items,
                "captured_at": page.evaluate("() => new Date().toISOString()"),
            }
            if args.artifact_path:
                artifact_path = Path(args.artifact_path).resolve()
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                payload["artifact_path"] = str(artifact_path)
            print(json.dumps(payload))
        finally:
            context.close()


if __name__ == "__main__":
    main()
