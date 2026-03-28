import unittest

from oh_my_gtm.schemas import CompanyProfile, GTMContextInput
from oh_my_gtm.services.context import normalize_context
from oh_my_gtm.services.research import create_research_plan, run_mock_research, score_research_items


class ResearchPlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = GTMContextInput(
            company_profile=CompanyProfile(
                workspace_name="Hackathon Workspace",
                company_name="Oh My GTM",
                product_name="oh-my-gtm",
                one_line_pitch="Policy-aware GTM automation for outbound teams",
                product_description="Reduce manual follow-up and tool sprawl for revops leaders.",
                proof_points=["fast setup"],
            ),
            competitor_names=["Apollo", "Outreach"],
            problem_keywords=["manual follow-up", "tool sprawl"],
        )
        self.normalized, _, _ = normalize_context(self.context)

    def test_research_plan_and_scoring_produce_ranked_items(self) -> None:
        plan = create_research_plan(self.normalized, self.context)
        self.assertGreater(len(plan.all_queries), 5)

        items = run_mock_research(plan)
        scored = score_research_items(items, self.normalized)

        self.assertGreaterEqual(len(scored), 4)
        self.assertGreaterEqual(scored[0].score, scored[-1].score)
        self.assertIn("problem_relevance", scored[0].explanation)


if __name__ == "__main__":
    unittest.main()
