"""Message generation, follow-up sequencing, and experiment assignment."""

from __future__ import annotations

from collections import defaultdict

from oh_my_gtm.schemas import AssignmentRecord, CandidateRecord, GTMContextInput, HypothesisRecord, MessageVariantRecord
from oh_my_gtm.services.guardrails import validate_message


ANGLE_OPENERS = {
    "pain-led": "Saw a pattern that often shows up when teams are stuck with manual follow-up.",
    "curiosity-led": "Curious whether this is on your radar after the recent signal we saw.",
    "credibility-led": "We built this specifically for teams dealing with the same GTM operations drag.",
}


def generate_initial_variants(
    hypothesis: HypothesisRecord,
    context: GTMContextInput,
    channel: str = "linkedin",
) -> list[MessageVariantRecord]:
    """Generate three first-touch variants with evidence-based framing."""

    variants: list[MessageVariantRecord] = []
    approved_claims = context.company_profile.approved_claims
    forbidden_claims = context.company_profile.forbidden_claims
    proof_points = hypothesis.recommended_proof_points or context.company_profile.proof_points[:1]
    for label, angle in zip(["A", "B", "C"], ["pain-led", "curiosity-led", "credibility-led"], strict=True):
        opener = ANGLE_OPENERS[angle]
        body = (
            f"{hypothesis.statement} "
            f"We've been focused on {hypothesis.target_problem}, with an approach built around {proof_points[0]}."
        )
        cta = context.messaging_constraints.demo_cta_text
        variant = MessageVariantRecord(
            angle=angle,
            channel=channel,
            stage="first_touch",
            variant_label=label,
            opener_text=opener,
            body_text=body,
            cta_text=cta,
            expected_risk="low" if channel != "linkedin" else "medium",
            expected_reply_likelihood=0.24 if angle == "pain-led" else 0.2 if angle == "curiosity-led" else 0.18,
            proof_points_used=proof_points[:1],
        )
        blocking, warnings, quality = validate_message(variant, approved_claims, forbidden_claims)
        variant.risk_flags = blocking + warnings
        variant.quality_score = quality
        variants.append(variant)
    return variants


def generate_followup_sequence(
    hypothesis: HypothesisRecord,
    context: GTMContextInput,
    channel: str = "email",
    tone: str = "consultative",
) -> list[MessageVariantRecord]:
    sequence_steps = [
        ("step_1", "Light continuation", "Wanted to add a bit more context to the initial note."),
        ("step_2", "Sharper value articulation", "The pattern we keep seeing is teams losing speed because of fragmented follow-up."),
        ("step_3", "Low-friction close", "Happy to close the loop here if this is not a priority right now."),
    ]
    variants: list[MessageVariantRecord] = []
    for idx, (stage, _, lead) in enumerate(sequence_steps, start=1):
        body = f"{lead} {hypothesis.statement} {hypothesis.counterargument}"
        variant = MessageVariantRecord(
            angle=tone,
            channel=channel,
            stage=stage,
            variant_label=f"F{idx}",
            opener_text=lead,
            body_text=body,
            cta_text=context.messaging_constraints.demo_cta_text if idx < 3 else "Worth revisiting later?",
            expected_risk="low",
            expected_reply_likelihood=0.18 - (idx * 0.02),
            proof_points_used=hypothesis.recommended_proof_points[:1],
        )
        blocking, warnings, quality = validate_message(
            variant,
            context.company_profile.approved_claims,
            context.company_profile.forbidden_claims,
        )
        variant.risk_flags = blocking + warnings
        variant.quality_score = quality
        variants.append(variant)
    return variants


def allocate_experiments(
    candidates: list[CandidateRecord],
    variants: list[MessageVariantRecord],
    channel: str,
    holdout_every: int = 10,
) -> list[AssignmentRecord]:
    """Balance assignments by company and seniority with light holdout support."""

    assignments: list[AssignmentRecord] = []
    counts_by_group = defaultdict(int)
    variant_cycle = [variant.variant_label for variant in variants]
    company_touch_count: dict[str, int] = defaultdict(int)
    for index, candidate in enumerate(sorted(candidates, key=lambda lead: (-lead.priority_score, lead.company_name, lead.person_name))):
        if company_touch_count[candidate.company_name] >= 2:
            continue
        holdout = index > 0 and index % holdout_every == 0
        if holdout:
            assignments.append(
                AssignmentRecord(
                    candidate_name=candidate.person_name,
                    company_name=candidate.company_name,
                    variant_label="HOLDOUT",
                    channel=channel,
                    stage="first_touch",
                    holdout=True,
                )
            )
            continue
        key = f"{candidate.seniority}:{candidate.company_name}"
        label = variant_cycle[counts_by_group[key] % len(variant_cycle)]
        counts_by_group[key] += 1
        company_touch_count[candidate.company_name] += 1
        assignments.append(
            AssignmentRecord(
                candidate_name=candidate.person_name,
                company_name=candidate.company_name,
                variant_label=label,
                channel=channel,
                stage="first_touch",
                holdout=False,
            )
        )
    return assignments
