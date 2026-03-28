"""Closed-loop optimization and success-principle extraction."""

from __future__ import annotations

from collections import Counter

from oh_my_gtm.schemas import HypothesisRecord, MessageVariantRecord, OptimizationDecisionResult, ResponseClassificationResult


def extract_success_principles(
    variants: list[MessageVariantRecord],
    successful_variant_labels: set[str],
) -> dict[str, object]:
    successful = [variant for variant in variants if variant.variant_label in successful_variant_labels]
    if not successful:
        return {
            "principle_statement": "No winners yet; keep exploring angles with stronger evidence.",
            "supporting_examples": [],
            "confidence": 0.4,
            "safe_scope_of_application": "new experiments only",
        }
    openings = Counter(variant.angle for variant in successful)
    lengths = [len(" ".join([variant.opener_text, variant.body_text, variant.cta_text]).split()) for variant in successful]
    avg_length = round(sum(lengths) / len(lengths), 1)
    winning_angle, _ = openings.most_common(1)[0]
    return {
        "principle_statement": f"Messages led by {winning_angle} framing are outperforming alternatives in this cohort.",
        "supporting_examples": [variant.body_text[:120] for variant in successful[:3]],
        "confidence": 0.82,
        "safe_scope_of_application": f"use on similar segments with message length near {avg_length} words",
    }


def optimize_hypotheses(
    hypotheses: list[HypothesisRecord],
    variant_performance: dict[str, dict[str, float]],
    reply_classifications: list[ResponseClassificationResult],
) -> list[OptimizationDecisionResult]:
    decisions: list[OptimizationDecisionResult] = []
    failures = sum(1 for classification in reply_classifications if classification.label in {"no_interest", "opt_out"})
    meetings = sum(1 for classification in reply_classifications if classification.label == "meeting_ready")
    if not hypotheses:
        return decisions

    top_hypothesis = hypotheses[0]
    if meetings >= 1:
        successful_variant_labels = {label for label, score in variant_performance.items() if score.get("meeting_rate", 0.0) > 0}
        decisions.append(
            OptimizationDecisionResult(
                decision_type="promote_hypothesis",
                subject_type="hypothesis",
                subject_id=top_hypothesis.title,
                reason="Observed at least one meeting-ready reply within the sample.",
                recommendation={
                    "new_status": "winning",
                    "success_principles": extract_success_principles([], successful_variant_labels),
                },
            )
        )
    elif failures >= 2:
        replacement_titles = [f"{top_hypothesis.title} replacement {index}" for index in range(1, 4)]
        decisions.append(
            OptimizationDecisionResult(
                decision_type="retire_hypothesis",
                subject_type="hypothesis",
                subject_id=top_hypothesis.title,
                reason="Repeated negative or no-interest responses suggest the current framing is weak.",
                recommendation={"new_status": "retired", "replacement_hypotheses": replacement_titles},
            )
        )
    else:
        decisions.append(
            OptimizationDecisionResult(
                decision_type="rotate_message_strategy",
                subject_type="hypothesis",
                subject_id=top_hypothesis.title,
                reason="Insufficient signal to declare a winner; try a different angle within the same hypothesis.",
                recommendation={"next_variant_focus": "curiosity-led", "status": "active"},
            )
        )
    return decisions
