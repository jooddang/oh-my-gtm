import asyncio
import os
import tempfile
import unittest

import httpx

from oh_my_gtm.api.app import create_app
from oh_my_gtm.config import AppSettings


class SignalInboxTests(unittest.TestCase):
    def test_signal_inbox_ingests_urls_csv_and_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app(AppSettings(database_url=f"sqlite+pysqlite:///{os.path.join(temp_dir, 'test.db')}", env="test"))

            async def scenario() -> None:
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.post("/api/workspaces", json={"workspace_name": "Inbox Workspace"})
                    workspace_id = response.json()["workspace_id"]

                    response = await client.post(
                        f"/api/workspaces/{workspace_id}/signal-inbox/urls",
                        json=[{"source_url": "https://www.linkedin.com/feed/update/test", "source_type": "linkedin_post_url", "note": "competitor mention"}],
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["normalized_items_created"], 1)

                    response = await client.post(
                        f"/api/workspaces/{workspace_id}/signal-inbox/csv",
                        json={"csv_text": "source_url,source_type,post_text,author_name,company_name\nhttps://example.com/post,blog_post,pain thread,Alex,SignalFlow\n"},
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["source"], "csv")

                    response = await client.post(
                        f"/api/workspaces/{workspace_id}/signal-inbox/capture",
                        json={
                            "page_url": "https://www.linkedin.com/feed/",
                            "items": [
                                {
                                    "item_type": "participant",
                                    "text": "Manual follow-up is killing us.",
                                    "author_name": "Jordan Lee",
                                    "company_name": "SignalFlow",
                                    "role": "Head of RevOps",
                                }
                            ],
                        },
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["normalized_items_created"], 1)

            asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
