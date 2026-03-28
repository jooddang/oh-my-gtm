# Product Requirements Document

## Product

`oh-my-gtm` is an autonomous GTM operating loop for founder-led outbound into US B2B SaaS. It is not a LinkedIn scraping bot. It is a research, hypothesis, messaging, measurement, and optimization system with policy-aware action gating.

## Problem

Founders and lean GTM teams struggle to:

- identify the right prospects from weak public signals
- convert scattered signals into usable segment hypotheses
- run channel-specific messaging experiments at speed
- keep reply handling fast and consistent
- learn from failures without manual spreadsheet operations

## Goals

- Minimize human-in-the-loop while keeping the workflow correct and safe
- Default to segment hypotheses instead of one-off person hypotheses
- Use LinkedIn only in policy-safe, human-gated ways
- Automate the full loop from research planning through optimization
- Keep every automated decision auditable

## Non-goals

- Headless LinkedIn scraping
- Stealth browser automation
- Unsupported claims or invented personalization
- CRM replacement

## MVP scope implemented in this repo

- workspace setup with context normalization and assumption logging
- research planning plus real Signal Inbox ingestion and deterministic mock fallback
- lead extraction, enrichment, exclusion, and priority scoring
- cluster generation and hypothesis generation
- message drafting and A/B allocation
- policy-safe outbound execution stubs
- LinkedIn browser-copilot preparation with explicit human approval gate
- LinkedIn browser-plan execution for safe open/snapshot steps
- real OpenAI Responses API integration when credentials are configured
- reply classification
- analytics snapshots
- closed-loop optimization recommendations
- resumable workflow execution with audit logs

## Guardrails

- LinkedIn execution is never automated beyond safe preparation
- quant claims without approved proof points are blocked
- excluded or opted-out candidates are blocked from outbound
- the workflow records stage-level audit events and correlation IDs

## Success metrics

- booked demo rate
- reply rate
- positive reply rate
- meeting booked rate
- hypothesis win rate
- variant lift

## MVP acceptance conditions

- A workspace can be created and patched with GTM context
- Missing fields are surfaced but the system can still infer enough to proceed
- A workflow run completes without manual intervention in local mode
- The workflow writes clusters, hypotheses, actions, metrics, and optimization decisions
- Tests pass locally
