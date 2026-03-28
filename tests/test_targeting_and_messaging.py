import unittest

from oh_my_gtm.schemas import CompanyProfile, ExclusionRuleInput, ExclusionRules, GTMContextInput
from oh_my_gtm.services.context import normalize_context
from oh_my_gtm.services.messaging import allocate_experiments, generate_initial_variants
from oh_my_gtm.services.research import create_research_plan, run_mock_research, score_research_items
from oh_my_gtm.services.targeting import cluster_candidates, enrich_candidate, evaluate_exclusions, extract_candidates, generate_hypotheses, rank_hypotheses, score_candidate


class TargetingAndMessagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = GTMContextInput(
            company_profile=CompanyProfile(
                workspace_name="Hackathon Workspace",
                company_name="Oh My GTM",
                product_name="oh-my-gtm",
                one_line_pitch="Policy-aware GTM automation for outbound teams",
                product_description="Reduce manual follow-up and tool sprawl for revops leaders.",
                proof_points=["fast setup"],
                approved_claims=["fast setup"],
            ),
            exclusion_rules=ExclusionRules(
                rules=[ExclusionRuleInput(name="block_students", rule_type="keyword_pattern", config={"keywords": ["student"]})]
            ),
            competitor_names=["Apollo"],
            problem_keywords=["manual follow-up", "tool sprawl"],
        )
        self.normalized, _, _ = normalize_context(self.context)
        plan = create_research_plan(self.normalized, self.context)
        self.scored = score_research_items(run_mock_research(plan), self.normalized)

    def test_extract_enrich_cluster_and_message(self) -> None:
        candidates = extract_candidates(self.scored)
        self.assertGreaterEqual(len(candidates), 3)

        enriched_candidates = []
        for candidate in candidates:
            enrichment = enrich_candidate(candidate, self.normalized)
            scored = score_candidate(candidate, enrichment, self.normalized)
            excluded, reasons = evaluate_exclusions(scored, self.context.exclusion_rules, self.normalized.competitor_names)
            if excluded:
                scored.exclusion_reason = ", ".join(reasons)
            enriched_candidates.append(scored)

        eligible = [candidate for candidate in enriched_candidates if not candidate.exclusion_reason]
        clusters = cluster_candidates(eligible)
        self.assertGreaterEqual(len(clusters), 1)

        hypotheses = rank_hypotheses(generate_hypotheses(clusters[0], self.normalized, self.context))
        variants = generate_initial_variants(hypotheses[0], self.context, channel="email")
        assignments = allocate_experiments(eligible, variants, channel="email")

        self.assertEqual(len(variants), 3)
        self.assertTrue(all(variant.quality_score > 0 for variant in variants))
        self.assertGreaterEqual(len(assignments), 1)


if __name__ == "__main__":
    unittest.main()
