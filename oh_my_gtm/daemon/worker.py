"""Long-running daemon worker for autonomous GTM jobs."""

from __future__ import annotations

import json
import time
from contextlib import suppress
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from oh_my_gtm.config import AppSettings
from oh_my_gtm.models import AutonomyJob, Workspace
from oh_my_gtm.orchestration.workflow import WorkflowEngine
from oh_my_gtm.schemas import SignalInboxIngestionResult, VisibleCaptureIngestionRequest
from oh_my_gtm.services.briefing import build_autopilot_brief, build_context_from_brief, build_linkedin_search_specs
from oh_my_gtm.services.context import normalize_context
from oh_my_gtm.services.linkedin_search import LinkedInSearchClient, collected_result_to_capture_items
from oh_my_gtm.services.outreach_artifacts import build_email_drafts, write_email_drafts
from oh_my_gtm.services.signal_inbox import ingest_visible_capture


def _ensure_artifact_dir(settings: AppSettings, job_id: str) -> Path:
    target = Path(settings.output_dir) / "autopilot" / job_id
    target.mkdir(parents=True, exist_ok=True)
    return target


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class AutonomyDaemon:
    def __init__(
        self,
        session_factory: sessionmaker,
        settings: AppSettings,
        *,
        workflow_engine: WorkflowEngine | None = None,
        search_client: LinkedInSearchClient | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.workflow_engine = workflow_engine or WorkflowEngine(session_factory, settings)
        self.search_client = search_client or LinkedInSearchClient(settings)

    def submit_job(self, brief_text: str, *, request: dict | None = None) -> str:
        with self.session_factory() as session:
            job = AutonomyJob(
                status="pending",
                brief_text=brief_text,
                request_json=request or {},
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job.id

    def run_once(self, brief_text: str) -> dict:
        job_id = self.submit_job(brief_text)
        return self.process_job(job_id)

    def process_pending_jobs(self, *, limit: int = 1) -> list[dict]:
        results: list[dict] = []
        with self.session_factory() as session:
            jobs = session.scalars(
                select(AutonomyJob).where(AutonomyJob.status == "pending").order_by(AutonomyJob.created_at.asc())
            ).all()
        for job in jobs[:limit]:
            results.append(self.process_job(job.id))
        return results

    def serve_forever(self) -> None:
        while True:
            try:
                handled = self.process_pending_jobs(limit=1)
            except Exception:
                time.sleep(self.settings.daemon_poll_interval_seconds)
                continue
            if not handled:
                time.sleep(self.settings.daemon_poll_interval_seconds)

    def process_job(self, job_id: str) -> dict:
        with self.session_factory() as session:
            job = session.get(AutonomyJob, job_id)
            if job is None:
                raise ValueError(f"Job {job_id} not found.")
            if job.status == "completed":
                return job.result_json
            job.status = "running"
            job.started_at = datetime.utcnow()
            session.commit()

        artifact_dir = _ensure_artifact_dir(self.settings, job_id)
        try:
            result = self._execute_job(job_id, artifact_dir)
        except Exception as exc:
            with self.session_factory() as session:
                job = session.get(AutonomyJob, job_id)
                if job is not None:
                    job.status = "failed"
                    job.completed_at = datetime.utcnow()
                    job.artifact_dir = str(artifact_dir)
                    job.error_text = str(exc)
                    session.commit()
            raise

        with self.session_factory() as session:
            job = session.get(AutonomyJob, job_id)
            if job is not None:
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.artifact_dir = str(artifact_dir)
                job.result_json = result
                session.commit()
        return result

    def _execute_job(self, job_id: str, artifact_dir: Path) -> dict:
        with self.session_factory() as session:
            job = session.get(AutonomyJob, job_id)
            if job is None:
                raise ValueError(f"Job {job_id} not found.")
            spec = build_autopilot_brief(job.brief_text)
            context = build_context_from_brief(spec)
            normalized, assumptions, missing = normalize_context(context)
            workspace = Workspace(
                name=f"Autopilot {spec.market_label[:64]}",
                context_json=context.model_dump(),
                normalized_context_json=normalized.model_dump(),
                missing_fields_json=missing,
                readiness_to_research=normalized.readiness_to_research,
                assumption_summary_json=[
                    *[assumption.model_dump() for assumption in assumptions],
                    *[{"field_name": "brief_assumption", "inferred_value": note, "confidence": 0.55, "rationale": "autopilot_default"} for note in spec.assumptions],
                ],
            )
            session.add(workspace)
            session.flush()
            job.workspace_id = workspace.id
            session.commit()
            workspace_id = workspace.id

        search_specs = build_linkedin_search_specs(
            spec,
            max_queries=self.settings.daemon_max_search_queries,
            limit=self.settings.daemon_max_search_results_per_query,
        )
        collected_payloads: list[dict] = []
        ingestions: list[SignalInboxIngestionResult] = []
        warnings: list[str] = []
        for spec_item in search_specs:
            collected = self.search_client.collect(spec_item)
            collected_payloads.append(collected.model_dump(mode="json"))
            capture_items = collected_result_to_capture_items(collected)
            if not capture_items:
                if "/uas/login" in collected.search_url or "login" in collected.page_title.lower():
                    warnings.append(
                        f"LinkedIn redirected query '{collected.query}' to login. "
                        "The daemon-specific browser profile is not authenticated."
                    )
                    continue
                warnings.append(
                    f"No ingestible LinkedIn {collected.vertical} results for query '{collected.query}'."
                )
                continue
            request = VisibleCaptureIngestionRequest(
                page_url=collected.search_url,
                page_type=f"linkedin_{collected.vertical}_search",
                items=capture_items,
            )
            with self.session_factory() as session:
                ingestions.append(ingest_visible_capture(session, workspace_id, request))
                session.commit()

        if not ingestions:
            warnings.append(
                "LinkedIn search returned no ingestible results. "
                "The daemon will continue with fallback research. "
                "If LinkedIn was redirected to login, run `oh-my-gtm-daemon browser-login` and sign in inside that exact browser window."
            )

        workflow_result = self.workflow_engine.run(workspace_id, dry_run=True)
        with self.session_factory() as session:
            drafts = build_email_drafts(session, workspace_id, spec, limit=self.settings.daemon_max_email_drafts)

        search_path = artifact_dir / "linkedin_search_results.json"
        _write_json(search_path, {"results": collected_payloads})
        drafts_path = write_email_drafts(artifact_dir, drafts)
        summary = {
            "job_id": job_id,
            "workspace_id": workspace_id,
            "market_label": spec.market_label,
            "assumptions": spec.assumptions,
            "linkedin_queries_run": [item.model_dump() for item in search_specs],
            "linkedin_results_file": str(search_path),
            "linkedin_ingestion_count": len(ingestions),
            "warnings": warnings,
            "email_drafts_file": str(drafts_path),
            "email_draft_count": len(drafts),
            "workflow": workflow_result.model_dump(mode="json"),
        }
        _write_json(artifact_dir / "run_summary.json", summary)
        with suppress(OSError):
            (artifact_dir / "decisions.md").write_text(
                "\n".join(
                    [
                        f"# Autopilot Decisions for {spec.market_label}",
                        "",
                        "## Assumptions",
                        *[f"- {item}" for item in spec.assumptions],
                        "",
                        "## Workflow",
                        f"- Workspace: {workspace_id}",
                        f"- Email drafts: {len(drafts)}",
                        f"- Search artifacts: {search_path}",
                    ]
                ),
                encoding="utf-8",
            )
        return summary
