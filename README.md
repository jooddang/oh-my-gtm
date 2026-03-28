# oh-my-gtm
<p align="center">
  <a href="https://www.youtube.com/watch?v=ieNK4yCiZZE">
    <img src="https://i.ytimg.com/vi/ieNK4yCiZZE/hqdefault.jpg" alt="Watch the demo on YouTube" width="720" />
  </a>
</p>
<p align="center">
  <a href="https://www.youtube.com/watch?v=ieNK4yCiZZE"><strong>[ Play demo on YouTube ]</strong></a>
</p>

Policy-aware autonomous GTM agent for US-focused B2B SaaS outbound research and messaging.

This repo started from strategy-only markdowns and is now a runnable hackathon MVP that:

- ingests GTM context with assumption logging
- generates a research plan without asking the operator follow-up questions
- runs a policy-safe mock research loop
- extracts and scores targets
- clusters leads and generates hypotheses
- drafts first-touch messages and assigns experiments
- prepares outbound actions with guardrails
- prepares LinkedIn browser-copilot plans with a mandatory human final-send gate
- ingests real Signal Inbox data from URL, CSV, and visible capture payloads
- supports real OpenAI Responses API integration when `OH_MY_GTM_OPENAI_API_KEY` is set
- classifies replies, computes metrics, and emits optimization decisions
- includes an independent daemon and CLI driver that can take a one-line brief, run LinkedIn search collection, and export email drafts

## Why Starlette instead of FastAPI

The product brief preferred FastAPI, but the execution environment used for this build did not have `fastapi` installed while `starlette`, `pydantic`, `sqlalchemy`, and `uvicorn` were available. The MVP therefore uses Starlette for the ASGI layer and keeps the service layer framework-independent. This tradeoff is documented in [docs/decisions-and-ambiguities.md](/Users/jooddang/Documents/oh-my-gtm/docs/decisions-and-ambiguities.md).

## Project layout

```text
oh_my_gtm/
  api/              ASGI app and HTTP routes
  orchestration/    Resumable workflow engine
  services/         Business logic modules
  config.py         Settings
  database.py       Engine/session helpers
  models.py         SQLAlchemy models
  schemas.py        Pydantic schemas
docs/
  PRD.md
  architecture.md
  decisions-and-ambiguities.md
tests/
  unittest-based test suite
scripts/
  seed_demo.py
```

## Quick start

1. Create a virtual environment and install the package:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Start the API:

```bash
python3 -m uvicorn oh_my_gtm.api.app:app --reload
```

3. Run the tests:

```bash
python3 -m unittest discover -s tests -v
```

4. Seed a demo workspace and execute the workflow:

```bash
python3 scripts/seed_demo.py
```

5. Run the autonomous daemon once against a one-line brief:

```bash
oh-my-gtm-daemon run-once --brief "스테이블 코인 결제 인프라 경쟁 업체 찾고 어프로치 할 수 있게 도와줘"
```

6. Or start the daemon loop and submit jobs:

```bash
oh-my-gtm-daemon serve
oh-my-gtm-daemon submit --brief "Find stablecoin payment infrastructure competitors and draft outreach"
```

7. Warm up the daemon's dedicated LinkedIn browser profile for manual login bootstrap:

```bash
oh-my-gtm-daemon browser-login --wait-ms 300000
```

## API routes

- `POST /api/workspaces`
- `GET /api/workspaces/{workspace_id}`
- `PATCH /api/workspaces/{workspace_id}/context`
- `GET /api/workspaces/{workspace_id}/missing-fields`
- `POST /api/workspaces/{workspace_id}/signal-inbox/urls`
- `POST /api/workspaces/{workspace_id}/signal-inbox/csv`
- `POST /api/workspaces/{workspace_id}/signal-inbox/capture`
- `POST /api/workspaces/{workspace_id}/linkedin/prepare`
- `POST /api/workspaces/{workspace_id}/linkedin/execute`
- `POST /api/workspaces/{workspace_id}/orchestrate`
- `GET /api/workflows/{workflow_id}`
- `GET /openapi.json`

## Local data model and migrations

The hackathon MVP uses `SQLAlchemy.create_all()` for fast local setup and includes a starter SQL migration in [migrations/0001_initial.sql](/Users/jooddang/Documents/oh-my-gtm/migrations/0001_initial.sql). The recommended production move is Alembic-backed Postgres migrations.

## Long-running autonomy defaults

- Missing GTM context is inferred where possible and written into the assumption log.
- Research uses Signal Inbox data when present, otherwise falls back to policy-safe mock connectors so the full loop can execute without human input.
- Outbound execution defaults to dry-run plus approval-safe handling for LinkedIn.
- LinkedIn copilot preparation emits headed Playwright wrapper commands, but final send stays human-only.
- Local and test environments synthesize a tiny response sample so the analytics and optimization stages can run end to end.

## Optional LLM setup

Set these env vars to enable real OpenAI-backed enrichment, hypothesis generation, message generation, and reply-classification fallback:

```bash
export OH_MY_GTM_OPENAI_API_KEY=your_key
export OH_MY_GTM_OPENAI_MODEL=gpt-5
```

## Known security warning

- `POST /api/workspaces/{workspace_id}/linkedin/execute` is not hardened for untrusted input yet.
- The current executor path still runs generated Playwright command strings through a shell-backed subprocess.
- Treat this project as local-only and trusted-operator-only until that path is refactored to structured argv execution without `shell=True`.
- Do not expose the API to the public internet, do not accept arbitrary third-party plan payloads, and do not wire raw LLM output directly into the execute endpoint.
- Runtime artifacts such as `output/`, browser profiles, daemon run outputs, and local databases may contain sensitive local session or outreach data and should remain untracked.

## Daemon artifacts

- Jobs are stored in the application database under `autonomy_jobs`.
- LinkedIn collection uses a dedicated persistent browser profile at `OH_MY_GTM_LINKEDIN_BROWSER_PROFILE_DIR` or `output/linkedin-profile`.
- Each daemon run writes artifacts under `output/autopilot/<job_id>/`.
- The main daemon outputs are `linkedin_search_results.json`, `email_drafts.json`, `run_summary.json`, and `decisions.md`.
- If the brief does not include first-party product details, the daemon defaults to discovery-style outreach and records that assumption in the artifact summary.

## Constraints respected

- No file outside the project root is modified.
- No stealth scraping, CAPTCHA bypass, or LinkedIn send automation is implemented.
- Human gating is preserved for external-platform steps that should not be fully autonomous.
