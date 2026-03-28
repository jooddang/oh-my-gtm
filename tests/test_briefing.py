import unittest

from oh_my_gtm.services.briefing import build_autopilot_brief, build_context_from_brief, build_linkedin_search_specs


class BriefingTests(unittest.TestCase):
    def test_korean_brief_is_normalized_into_market_and_queries(self) -> None:
        brief = "스테이블 코인 결제 인프라 경쟁 업체 찾고 어프로치 할 수 있게 도와줘"
        spec = build_autopilot_brief(brief)

        self.assertIn("stablecoin", spec.normalized_brief.lower())
        self.assertIn("payments", spec.market_label)
        self.assertGreaterEqual(len(spec.search_terms), 1)

        context = build_context_from_brief(spec)
        self.assertTrue(context.company_profile.one_line_pitch)
        self.assertIn("Founder", context.icp_profile.target_personas)

        searches = build_linkedin_search_specs(spec, max_queries=4, limit=3)
        self.assertEqual(len(searches), 4)
        self.assertEqual(searches[0].vertical, "companies")


if __name__ == "__main__":
    unittest.main()
