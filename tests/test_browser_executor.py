import unittest

from oh_my_gtm.config import AppSettings
from oh_my_gtm.schemas import LinkedInAgentPlan
from oh_my_gtm.services.browser_executor import execute_linkedin_plan


class BrowserExecutorTests(unittest.TestCase):
    def test_browser_executor_dry_run_executes_only_safe_steps(self) -> None:
        plan = LinkedInAgentPlan(
            mode="assisted_semi_auto",
            target_profile_url="https://www.linkedin.com/in/jordan-lee",
            fallback_search_url="https://www.google.com/search?q=jordan+lee",
            stage="first_touch",
            candidate_name="Jordan Lee",
            company_name="SignalFlow",
            note_text="Worth connecting?",
            playwright_commands=[
                'export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"',
                'export PWCLI="$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh"',
                '"$PWCLI" open "https://www.linkedin.com/in/jordan-lee" --headed',
                '"$PWCLI" snapshot',
                '"$PWCLI" click e1',
            ],
            operator_steps=["Verify profile"],
            completion_requirements=["final_send_clicked_by_human"],
            final_send_blocked=True,
        )
        result = execute_linkedin_plan(plan, AppSettings(env="test"), dry_run=True)
        self.assertEqual(result.status, "prepared")
        self.assertEqual(len(result.executed_steps), 2)
        self.assertTrue(any(output["status"] == "blocked" for output in result.outputs))


if __name__ == "__main__":
    unittest.main()
