import unittest

from oh_my_gtm.schemas import MessageVariantRecord, ResponseClassificationResult
from oh_my_gtm.services.analytics import compute_metrics
from oh_my_gtm.services.execution import ExecutionResult
from oh_my_gtm.services.optimization import extract_success_principles, optimize_hypotheses
from oh_my_gtm.services.replies import classify_reply


class ReplyAnalyticsTests(unittest.TestCase):
    def test_classification_and_metrics(self) -> None:
        classifications = [
            classify_reply("Interesting. Can you send a couple times next week?"),
            classify_reply("No thanks, not interested."),
        ]
        actions = [
            ExecutionResult(
                candidate_name="Jordan Lee",
                provider="email",
                channel="email",
                stage="first_touch",
                outcome="queued",
                requires_human_approval=False,
                details={"variant_label": "A"},
            ),
            ExecutionResult(
                candidate_name="Morgan Diaz",
                provider="email",
                channel="email",
                stage="first_touch",
                outcome="queued",
                requires_human_approval=False,
                details={"variant_label": "B"},
            ),
        ]
        metrics = compute_metrics(actions, classifications)

        metric_names = {metric.metric_name for metric in metrics}
        self.assertIn("reply_rate", metric_names)
        self.assertIn("meeting_booked_rate", metric_names)
        self.assertEqual(classifications[0].label, "meeting_ready")

    def test_optimizer_emits_actionable_decision(self) -> None:
        hypotheses = [
            type(
                "HypothesisProxy",
                (),
                {
                    "title": "RevOps cluster hypothesis",
                    "statement": "Teams will respond to consolidation framing.",
                    "target_problem": "tool sprawl",
                    "recommended_proof_points": ["fast setup"],
                    "recommended_cta": "Open to a 15-minute demo?",
                    "counterargument": "They may only be casually researching.",
                },
            )()
        ]
        classifications = [ResponseClassificationResult(label="meeting_ready", sentiment="positive", urgency="high", confidence=0.95, evidence_snippet="send times")]
        decisions = optimize_hypotheses(hypotheses, {"A": {"meeting_rate": 1.0}}, classifications)
        self.assertEqual(decisions[0].decision_type, "promote_hypothesis")

        principles = extract_success_principles(
            [
                MessageVariantRecord(
                    angle="pain-led",
                    channel="email",
                    stage="first_touch",
                    variant_label="A",
                    opener_text="Saw a pattern around manual follow-up.",
                    body_text="Teams like yours often lose speed due to tool sprawl.",
                    cta_text="Worth a quick look?",
                    expected_risk="low",
                    expected_reply_likelihood=0.2,
                    proof_points_used=["fast setup"],
                )
            ],
            {"A"},
        )
        self.assertIn("principle_statement", principles)


if __name__ == "__main__":
    unittest.main()
