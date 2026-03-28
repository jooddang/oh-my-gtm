"""Inbound response classification."""

from __future__ import annotations

from oh_my_gtm.schemas import ResponseClassificationResult


def classify_reply(message_text: str) -> ResponseClassificationResult:
    text = message_text.strip().lower()
    label = "unclear"
    sentiment = "neutral"
    urgency = "low"
    objection_type = None
    next_step = None
    confidence = 0.55

    if any(token in text for token in ["unsubscribe", "remove me", "stop emailing"]):
        label = "opt_out"
        sentiment = "negative"
        confidence = 0.98
    elif any(token in text for token in ["book time", "send times", "available", "let's meet", "next week"]):
        label = "meeting_ready"
        sentiment = "positive"
        urgency = "high"
        next_step = "schedule_meeting"
        confidence = 0.93
    elif any(token in text for token in ["interesting", "tell me more", "curious"]):
        label = "positive_interest"
        sentiment = "positive"
        next_step = "share_more_context"
        confidence = 0.85
    elif any(token in text for token in ["not the right person", "loop in", "talk to"]):
        label = "referral"
        sentiment = "neutral"
        next_step = "follow_referral"
        confidence = 0.87
    elif any(token in text for token in ["budget", "timing", "already using", "not now"]):
        label = "objection"
        sentiment = "neutral"
        objection_type = "timing_or_existing_solution"
        next_step = "handle_objection"
        confidence = 0.82
    elif any(token in text for token in ["no thanks", "not interested"]):
        label = "no_interest"
        sentiment = "negative"
        confidence = 0.91

    return ResponseClassificationResult(
        label=label,
        sentiment=sentiment,
        urgency=urgency,
        objection_type=objection_type,
        next_step_requested=next_step,
        confidence=confidence,
        evidence_snippet=message_text[:120],
    )
