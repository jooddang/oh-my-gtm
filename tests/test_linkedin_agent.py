import asyncio
import os
import tempfile
import unittest

import httpx

from oh_my_gtm.api.app import create_app
from oh_my_gtm.config import AppSettings
from oh_my_gtm.schemas import CandidateRecord, MessageVariantRecord
from oh_my_gtm.services.linkedin_agent import build_linkedin_agent_plan


class LinkedInAgentTests(unittest.TestCase):
    def test_build_linkedin_agent_plan_blocks_final_send(self) -> None:
        candidate = CandidateRecord(
            person_name="Jordan Lee",
            linkedin_url="https://www.linkedin.com/in/jordan-lee",
            company_name="SignalFlow",
            evidence_snippet="Recently discussed manual follow-up bottlenecks.",
            qualification_status="Tier A",
        )
        variant = MessageVariantRecord(
            angle="pain-led",
            channel="linkedin",
            stage="first_touch",
            variant_label="A",
            opener_text="Saw a pattern around manual follow-up.",
            body_text="Teams like yours often lose speed because follow-up stays manual.",
            cta_text="Worth connecting?",
            expected_risk="medium",
            expected_reply_likelihood=0.2,
            proof_points_used=["fast setup"],
        )
        plan = build_linkedin_agent_plan(candidate, variant, mode="assisted_semi_auto")
        self.assertTrue(plan.final_send_blocked)
        self.assertIn("PWCLI", " ".join(plan.playwright_commands))
        self.assertIn("final_send_clicked_by_human", plan.completion_requirements)

    def test_prepare_endpoint_returns_browser_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app(AppSettings(database_url=f"sqlite+pysqlite:///{os.path.join(temp_dir, 'test.db')}", env="test"))

            async def scenario() -> None:
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.post("/api/workspaces", json={"workspace_name": "Test Workspace"})
                    workspace_id = response.json()["workspace_id"]
                    response = await client.post(
                        f"/api/workspaces/{workspace_id}/linkedin/prepare",
                        json={
                            "candidate_name": "Jordan Lee",
                            "company_name": "SignalFlow",
                            "linkedin_url": "https://www.linkedin.com/in/jordan-lee",
                            "opener_text": "Saw a pattern around manual follow-up.",
                            "body_text": "Teams like yours often lose speed because follow-up stays manual.",
                            "cta_text": "Worth connecting?",
                            "mode": "assisted_semi_auto",
                        },
                    )
                    self.assertEqual(response.status_code, 200)
                    payload = response.json()
                    self.assertEqual(payload["mode"], "assisted_semi_auto")
                    self.assertTrue(payload["final_send_blocked"])

            asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
