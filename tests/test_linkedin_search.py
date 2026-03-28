import json
import os
import tempfile
import unittest
from subprocess import CompletedProcess

from oh_my_gtm.config import AppSettings
from oh_my_gtm.schemas import LinkedInSearchSpec
from oh_my_gtm.services.chrome_linkedin import ChromeLinkedInCollector
from oh_my_gtm.services.linkedin_search import LinkedInSearchClient, collected_result_to_capture_items


class LinkedInSearchClientTests(unittest.TestCase):
    def test_client_parses_collector_output_and_builds_capture_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = {
                "query": "stablecoin payments founder",
                "vertical": "people",
                "search_url": "https://www.linkedin.com/search/results/people/?keywords=stablecoin",
                "page_title": "stablecoin | Search | LinkedIn",
                "captured_at": "2026-03-28T22:00:00Z",
                "items": [
                    {
                        "vertical": "people",
                        "entity_name": "Avery Kim",
                        "entity_url": "https://www.linkedin.com/in/avery-kim",
                        "raw_text": "Avery Kim\nFounder at StableOps\nSan Francisco, CA\nConnect",
                        "lines": ["Avery Kim", "Founder at StableOps", "San Francisco, CA", "Connect"],
                        "title": "Founder at StableOps",
                        "company_name": "StableOps",
                        "location": "San Francisco, CA",
                        "action_label": "Connect",
                    }
                ],
            }

            def runner(_: list[str]) -> CompletedProcess[str]:
                return CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")

            class DisabledChromeCollector(ChromeLinkedInCollector):
                @property
                def available(self) -> bool:
                    return False

            client = LinkedInSearchClient(
                AppSettings(output_dir=os.path.join(temp_dir, "output"), linkedin_browser_profile_dir=os.path.join(temp_dir, "profile")),
                runner=runner,
                chrome_collector=DisabledChromeCollector(AppSettings()),
            )
            result = client.collect(LinkedInSearchSpec(query="stablecoin payments founder", vertical="people", limit=5))
            self.assertEqual(result.items[0].entity_name, "Avery Kim")

            capture_items = collected_result_to_capture_items(result)
            self.assertEqual(capture_items[0].item_type, "profile")
            self.assertEqual(capture_items[0].author_name, "Avery Kim")


if __name__ == "__main__":
    unittest.main()
