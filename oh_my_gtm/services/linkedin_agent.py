"""Human-gated LinkedIn browser copilot planning."""

from __future__ import annotations

from urllib.parse import quote_plus

from oh_my_gtm.schemas import CandidateRecord, LinkedInAgentPlan, LinkedInPrepareRequest, MessageVariantRecord


def _slugify_person_name(name: str) -> str:
    return "-".join(part for part in name.lower().replace(".", " ").split() if part)


def default_linkedin_url(candidate_name: str) -> str:
    return f"https://www.linkedin.com/in/{_slugify_person_name(candidate_name)}"


def build_linkedin_search_url(candidate_name: str, company_name: str = "") -> str:
    query = " ".join(part for part in [candidate_name, company_name, "linkedin"] if part).strip()
    return f"https://www.google.com/search?q={quote_plus(query)}"


def build_linkedin_agent_plan(
    candidate: CandidateRecord,
    variant: MessageVariantRecord,
    *,
    mode: str = "compliance_manual",
) -> LinkedInAgentPlan:
    profile_url = candidate.linkedin_url or default_linkedin_url(candidate.person_name)
    note = " ".join(part for part in [variant.opener_text, variant.body_text, variant.cta_text] if part).strip()[:300]
    search_url = build_linkedin_search_url(candidate.person_name, candidate.company_name)

    commands = [
        'export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"',
        'export PWCLI="$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh"',
        f'"$PWCLI" open "{profile_url}" --headed',
        '"$PWCLI" snapshot',
    ]
    if mode == "assisted_semi_auto":
        commands.append(f'# draft note ready for manual paste: {note}')

    operator_steps = [
        "Verify the opened profile matches the candidate and company.",
        "Review the evidence snippet and the prepared note before taking any action.",
        "Keep the final Connect or Send click human-operated.",
        "Record the final outcome as sent, skipped, or needs_revision.",
    ]
    if mode == "compliance_manual":
        operator_steps.insert(2, "Use the agent only for opening the page and gathering a snapshot.")
    elif mode == "assisted_semi_auto":
        operator_steps.insert(2, "Assisted mode may navigate and prepare context, but final send is still blocked.")

    return LinkedInAgentPlan(
        mode=mode,
        target_profile_url=profile_url,
        fallback_search_url=search_url,
        stage=variant.stage,
        candidate_name=candidate.person_name,
        company_name=candidate.company_name,
        note_text=note,
        playwright_commands=commands,
        operator_steps=operator_steps,
        completion_requirements=[
            "identity_verified",
            "message_reviewed",
            "final_send_clicked_by_human",
            "outcome_recorded",
        ],
        final_send_blocked=True,
        evidence_snippet=candidate.evidence_snippet,
        metadata={
            "variant_label": variant.variant_label,
            "angle": variant.angle,
            "risk_flags": variant.risk_flags,
            "expected_risk": variant.expected_risk,
        },
    )


def plan_from_request(request: LinkedInPrepareRequest) -> LinkedInAgentPlan:
    candidate = CandidateRecord(
        person_name=request.candidate_name,
        linkedin_url=request.linkedin_url,
        company_name=request.company_name,
        title=request.title,
        evidence_snippet=request.evidence_snippet,
        qualification_status="Tier B",
    )
    variant = MessageVariantRecord(
        angle=request.angle,
        channel="linkedin",
        stage=request.stage,
        variant_label=request.variant_label,
        opener_text=request.opener_text,
        body_text=request.body_text,
        cta_text=request.cta_text,
        expected_risk="medium",
        expected_reply_likelihood=0.2,
        proof_points_used=request.proof_points_used,
        risk_flags=[],
        quality_score=80.0,
    )
    return build_linkedin_agent_plan(candidate, variant, mode=request.mode)
