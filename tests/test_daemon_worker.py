import json
import os
import tempfile
import unittest
from pathlib import Path

from oh_my_gtm.config import AppSettings
from oh_my_gtm.database import create_session_factory, init_db
from oh_my_gtm.daemon.worker import AutonomyDaemon
from oh_my_gtm.models import AutonomyJob
from oh_my_gtm.orchestration.workflow import WorkflowEngine
from oh_my_gtm.schemas import LinkedInCollectedItem, LinkedInSearchResult, LinkedInSearchSpec


class FakeSearchClient:
    def __init__(self, output_dir: str) -> None:
        self.output_dir = output_dir

    def collect(self, spec: LinkedInSearchSpec) -> LinkedInSearchResult:
        name = "Avery Kim" if spec.vertical == "people" else "StableOps"
        url = "https://www.linkedin.com/in/avery-kim" if spec.vertical == "people" else "https://www.linkedin.com/company/stableops"
        item = LinkedInCollectedItem(
            vertical=spec.vertical,
            entity_name=name,
            entity_url=url,
            raw_text=f"{name}\nFounder at StableOps\nSan Francisco, CA\nConnect",
            lines=[name, "Founder at StableOps", "San Francisco, CA", "Connect"],
            title="Founder at StableOps",
            company_name="StableOps",
            location="San Francisco, CA",
            action_label="Connect",
        )
        artifact_path = Path(self.output_dir) / f"{spec.vertical}.json"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps({"query": spec.query, "vertical": spec.vertical}), encoding="utf-8")
        return LinkedInSearchResult(
            query=spec.query,
            vertical=spec.vertical,
            search_url=f"https://www.linkedin.com/search/results/{spec.vertical}/?keywords={spec.query}",
            page_title=f"{spec.query} | Search | LinkedIn",
            items=[item],
            artifact_path=str(artifact_path),
        )


class EmptySearchClient:
    def collect(self, spec: LinkedInSearchSpec) -> LinkedInSearchResult:
        return LinkedInSearchResult(
            query=spec.query,
            vertical=spec.vertical,
            search_url=f"https://www.linkedin.com/search/results/{spec.vertical}/?keywords={spec.query}",
            page_title=f"{spec.query} | Search | LinkedIn",
            items=[],
        )


class DaemonWorkerTests(unittest.TestCase):
    def test_daemon_run_once_creates_job_workspace_and_email_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = AppSettings(
                database_url=f"sqlite+pysqlite:///{os.path.join(temp_dir, 'daemon.db')}",
                output_dir=os.path.join(temp_dir, "output"),
                env="test",
            )
            session_factory = create_session_factory(settings)
            init_db(session_factory)
            daemon = AutonomyDaemon(
                session_factory,
                settings,
                workflow_engine=WorkflowEngine(session_factory, settings),
                search_client=FakeSearchClient(settings.output_dir),
            )

            result = daemon.run_once("stablecoin payment infrastructure competitors")

            self.assertIn("workspace_id", result)
            self.assertTrue(os.path.exists(result["email_drafts_file"]))
            self.assertEqual(result["workflow"]["status"], "completed")
            fetch_stage = next(stage for stage in result["workflow"]["stages"] if stage["stage_name"] == "fetch_research_items")
            self.assertEqual(fetch_stage["details"]["source"], "signal_inbox")

            with session_factory() as session:
                jobs = session.query(AutonomyJob).all()
                self.assertEqual(len(jobs), 1)
                self.assertEqual(jobs[0].status, "completed")

    def test_daemon_falls_back_when_live_search_returns_no_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = AppSettings(
                database_url=f"sqlite+pysqlite:///{os.path.join(temp_dir, 'daemon.db')}",
                output_dir=os.path.join(temp_dir, "output"),
                env="test",
            )
            session_factory = create_session_factory(settings)
            init_db(session_factory)
            daemon = AutonomyDaemon(
                session_factory,
                settings,
                workflow_engine=WorkflowEngine(session_factory, settings),
                search_client=EmptySearchClient(),
            )

            result = daemon.run_once("stablecoin payment infrastructure competitors")

            self.assertEqual(result["linkedin_ingestion_count"], 0)
            self.assertTrue(result["warnings"])
            fetch_stage = next(stage for stage in result["workflow"]["stages"] if stage["stage_name"] == "fetch_research_items")
            self.assertEqual(fetch_stage["details"]["items_created"], 16)


if __name__ == "__main__":
    unittest.main()
