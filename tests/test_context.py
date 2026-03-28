import unittest

from oh_my_gtm.schemas import CompanyProfile, GTMContextInput
from oh_my_gtm.services.context import normalize_context


class ContextNormalizationTests(unittest.TestCase):
    def test_normalize_context_infers_missing_fields_and_logs_assumptions(self) -> None:
        context = GTMContextInput(
            company_profile=CompanyProfile(
                workspace_name="Hackathon Workspace",
                company_name="Oh My GTM",
                product_name="oh-my-gtm",
                one_line_pitch="Autonomous outbound research and follow-up automation for B2B SaaS teams",
                product_description="Helps revops and growth teams reduce manual follow-up and improve pipeline visibility.",
            ),
            competitor_names=["Apollo"],
        )

        normalized, assumptions, missing = normalize_context(context)

        self.assertEqual(normalized.product_category, "gtm-automation")
        self.assertIn("RevOps Leader", normalized.buyer_personas)
        self.assertIn("manual follow-up", normalized.pain_points)
        self.assertIn("company_profile.proof_points", missing)
        self.assertGreaterEqual(len(assumptions), 4)
        self.assertFalse(normalized.readiness_to_research)


if __name__ == "__main__":
    unittest.main()
