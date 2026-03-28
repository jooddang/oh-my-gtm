import asyncio
import os
import tempfile
import unittest

import httpx

from oh_my_gtm.api.app import create_app
from oh_my_gtm.config import AppSettings


class WorkflowApiTests(unittest.TestCase):
    def test_api_can_create_workspace_and_run_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_url = f"sqlite+pysqlite:///{os.path.join(temp_dir, 'test.db')}"
            app = create_app(AppSettings(database_url=database_url, env="test"))

            async def scenario() -> None:
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.post("/api/workspaces", json={"workspace_name": "Test Workspace"})
                    self.assertEqual(response.status_code, 201)
                    workspace_id = response.json()["workspace_id"]

                    patch_payload = {
                        "company_profile": {
                            "workspace_name": "Test Workspace",
                            "company_name": "Oh My GTM",
                            "product_name": "oh-my-gtm",
                            "one_line_pitch": "Autonomous outbound research and messaging for B2B SaaS",
                            "product_description": "Helps revops teams reduce manual follow-up and tool sprawl.",
                            "proof_points": ["fast setup"],
                            "approved_claims": ["fast setup"],
                            "forbidden_claims": ["guaranteed meetings"],
                            "target_market": "US B2B SaaS",
                            "booking_link": "https://example.com/book",
                        },
                        "competitor_names": ["Apollo"],
                        "problem_keywords": ["manual follow-up", "tool sprawl"],
                    }
                    response = await client.patch(f"/api/workspaces/{workspace_id}/context", json=patch_payload)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.json()["normalized_context"]["readiness_to_research"])

                    response = await client.post(f"/api/workspaces/{workspace_id}/orchestrate")
                    self.assertEqual(response.status_code, 200)
                    workflow_id = response.json()["workflow_run_id"]
                    self.assertEqual(response.json()["status"], "completed")
                    execute_stage = next(stage for stage in response.json()["stages"] if stage["stage_name"] == "execute_outbound")
                    self.assertGreaterEqual(execute_stage["details"]["linkedin_actions_prepared"], 1)

                    response = await client.get(f"/api/workflows/{workflow_id}")
                    self.assertEqual(response.status_code, 200)
                    self.assertGreaterEqual(len(response.json()["stages"]), 5)

            asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
