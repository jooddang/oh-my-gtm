"""Message and automation guardrails."""

from __future__ import annotations

import re

from oh_my_gtm.schemas import CandidateRecord, MessageVariantRecord


def validate_message(variant: MessageVariantRecord, approved_claims: list[str], forbidden_claims: list[str]) -> tuple[list[str], list[str], float]:
    warnings: list[str] = []
    blocking: list[str] = []
    combined = " ".join([variant.opener_text, variant.body_text, variant.cta_text]).lower()

    if len(combined) > 300 and variant.channel == "linkedin":
        blocking.append("linkedin_length_exceeded")
    if len(combined) > 800 and variant.channel == "email":
        warnings.append("email_is_long")
    if any(term.lower() in combined for term in forbidden_claims):
        blocking.append("forbidden_claim")
    if re.search(r"\b\d+%|\b\d+x", combined) and not approved_claims:
        blocking.append("unsupported_quantified_claim")
    if any(token in combined for token in ["guarantee", "best-in-class", "perfect fit"]):
        warnings.append("overclaim_risk")
    if any(token in combined for token in ["just circling back", "quick question", "touching base"]):
        warnings.append("generic_sales_language")

    quality_score = 100.0 - (len(warnings) * 12) - (len(blocking) * 35)
    return blocking, warnings, max(0.0, quality_score)


def validate_automation_plan(candidate: CandidateRecord, prior_attempts: int, opted_out: bool) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    blocking: list[str] = []
    if opted_out:
        blocking.append("opt_out_present")
    if prior_attempts >= 3:
        blocking.append("over_contact_limit")
    if candidate.qualification_status == "Reject":
        blocking.append("candidate_rejected")
    if candidate.exclusion_reason:
        blocking.append("candidate_excluded")
    if candidate.policy_risk_score > 40:
        warnings.append("elevated_policy_risk")
    return blocking, warnings
