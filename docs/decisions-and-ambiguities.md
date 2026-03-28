# Decisions And Ambiguities

This file records practical defaults chosen without asking for clarification, per the project brief.

## 1. Web framework fallback

- Ambiguity: the brief preferred FastAPI, but the runtime environment did not include it.
- Decision: use Starlette for the HTTP layer and keep business logic framework-independent.
- Reason: this keeps the project runnable right now without modifying files outside the repo or relying on additional human setup.

## 2. Database runtime

- Ambiguity: the brief preferred PostgreSQL, but local hackathon verification should run without extra services.
- Decision: default to SQLite locally and in tests, with Postgres shown in `docker-compose.yml`.
- Reason: it allows the autonomous loop and tests to run end to end in one command.

## 3. Research execution without external credentials

- Ambiguity: the product wants research automation, but external APIs and browser sessions are not available in a deterministic local test path.
- Decision: ship a policy-safe mock connector that produces deterministic research items from the generated query plan.
- Reason: this preserves the end-to-end loop and lets the workflow run long enough without operator input.

## 4. Reply ingestion

- Ambiguity: a closed-loop optimizer needs replies, but a clean local repo has no inbound channel.
- Decision: local and test workflow runs synthesize a tiny response sample during the `ingest_responses` stage.
- Reason: this keeps analytics and optimization runnable while avoiding fake network dependencies.

## 5. Hypothesis depth

- Ambiguity: the source docs describe large scope, but hackathon time favors a narrower but complete slice.
- Decision: generate three persisted hypotheses per cluster from a five-template library and approve strong ones automatically.
- Reason: it balances completeness, testability, and code size.

## 6. Human-in-the-loop minimization

- Ambiguity: the brief asks to minimize human input while keeping external actions safe.
- Decision: email can auto-queue in dry-run mode, while LinkedIn-like actions remain preparation-only by default.
- Reason: this aligns with the policy constraints in the provided research documents.

## 7. LinkedIn browser copilot boundary

- Ambiguity: the follow-up request asked for a LinkedIn agent that drives the browser.
- Decision: implement a browser copilot that can open the target page, generate Playwright wrapper commands, and prepare the connection note, while still blocking the final Connect or Send click.
- Reason: this preserves the requested browser-agent UX without turning the project into unattended LinkedIn automation.

## 8. Daemon brief completion

- Ambiguity: the daemon is expected to operate from a single natural-language brief, but the brief may omit the user's company and product context.
- Decision: default the daemon to discovery-style market-mapping outreach when product context is missing, and record that assumption in the artifacts.
- Reason: this keeps the process autonomous enough for the hackathon while making the implicit tradeoff visible.

## 9. Independent browser session

- Ambiguity: a daemon process cannot rely on the Codex browser session.
- Decision: use a dedicated persistent browser profile for LinkedIn collection and expose a `browser-login` command for one-time manual bootstrap.
- Reason: this lets the daemon run independently after an initial login without requiring Codex to stay attached.
