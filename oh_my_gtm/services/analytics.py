"""Metrics and experiment analytics."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import median

from oh_my_gtm.schemas import MetricResult, ResponseClassificationResult
from oh_my_gtm.services.execution import ExecutionResult


def compute_metrics(
    actions: list[ExecutionResult],
    classifications: list[ResponseClassificationResult],
) -> list[MetricResult]:
    sent = sum(1 for action in actions if action.outcome in {"queued", "sent", "prepared"})
    replied = len(classifications)
    positives = sum(1 for classification in classifications if classification.label in {"positive_interest", "meeting_ready"})
    meetings = sum(1 for classification in classifications if classification.label == "meeting_ready")
    negatives = sum(1 for classification in classifications if classification.label in {"opt_out", "no_interest"})
    conversion = lambda num, den: round((num / den), 4) if den else 0.0

    label_counts = Counter(classification.label for classification in classifications)
    metrics = [
        MetricResult(metric_name="send_queue_completion_rate", value=conversion(sent, max(sent, 1))),
        MetricResult(metric_name="reply_rate", value=conversion(replied, sent), details={"replied": replied, "sent": sent}),
        MetricResult(metric_name="positive_reply_rate", value=conversion(positives, sent), details={"positives": positives}),
        MetricResult(metric_name="negative_reply_rate", value=conversion(negatives, sent), details={"negatives": negatives}),
        MetricResult(metric_name="meeting_booked_rate", value=conversion(meetings, sent), details={"meetings": meetings}),
        MetricResult(metric_name="label_distribution", value=1.0, details=dict(label_counts)),
    ]
    return metrics


def compute_variant_uplift(
    actions: list[ExecutionResult],
    classifications_by_candidate: dict[str, ResponseClassificationResult],
) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = defaultdict(lambda: {"sent": 0.0, "positive": 0.0, "meeting": 0.0})
    for action in actions:
        label = action.details.get("variant_label", "unknown")
        stats[label]["sent"] += 1
        classification = classifications_by_candidate.get(action.candidate_name)
        if classification and classification.label in {"positive_interest", "meeting_ready"}:
            stats[label]["positive"] += 1
        if classification and classification.label == "meeting_ready":
            stats[label]["meeting"] += 1
    for label, values in stats.items():
        sent = values["sent"] or 1.0
        values["positive_rate"] = round(values["positive"] / sent, 4)
        values["meeting_rate"] = round(values["meeting"] / sent, 4)
        values["score"] = round(values["meeting"] * 5 + values["positive"] * 3, 2)
    return dict(stats)


def median_time_to_reply(hours_to_reply: list[float]) -> float:
    return float(median(hours_to_reply)) if hours_to_reply else 0.0
