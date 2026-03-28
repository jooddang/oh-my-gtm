import unittest
from unittest.mock import Mock, patch

from oh_my_gtm.config import AppSettings
from oh_my_gtm.schemas import LLMRequest
from oh_my_gtm.services.llm import OpenAIResponsesClient


class LLMClientTests(unittest.TestCase):
    @patch("oh_my_gtm.services.llm.httpx.post")
    def test_openai_responses_client_parses_output_text(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {
            "output": [
                {
                    "content": [
                        {
                            "type": "output_text",
                            "text": "{\"label\":\"positive_interest\",\"sentiment\":\"positive\",\"urgency\":\"low\",\"confidence\":0.8,\"evidence_snippet\":\"interesting\"}",
                        }
                    ]
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenAIResponsesClient(AppSettings(openai_api_key="test-key", openai_model="gpt-5", env="test"))
        response = client.generate(
            LLMRequest(
                system_prompt="Return JSON.",
                user_prompt="Classify this reply",
                response_format="json",
            )
        )
        self.assertEqual(response.provider, "openai_responses")
        self.assertEqual(response.parsed_json["label"], "positive_interest")


if __name__ == "__main__":
    unittest.main()
