"""CLI driver for the independent autopilot daemon process."""

from __future__ import annotations

import argparse
import json
import time

from oh_my_gtm.config import AppSettings
from oh_my_gtm.database import create_session_factory, init_db
from oh_my_gtm.daemon.worker import AutonomyDaemon


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the autonomous GTM daemon.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit = subparsers.add_parser("submit", help="Queue a new autonomous job.")
    submit.add_argument("--brief", required=True, help="Single-line operator brief.")
    submit.add_argument("--wait", action="store_true", help="Wait for job completion.")

    run_once = subparsers.add_parser("run-once", help="Submit and execute a single job immediately.")
    run_once.add_argument("--brief", required=True, help="Single-line operator brief.")

    serve = subparsers.add_parser("serve", help="Run the daemon loop and process queued jobs.")
    serve.add_argument("--poll-seconds", type=int, default=None, help="Override poll interval.")

    status = subparsers.add_parser("status", help="Inspect a job by id.")
    status.add_argument("--job-id", required=True)

    login = subparsers.add_parser("browser-login", help="Open the dedicated LinkedIn browser profile for login warmup.")
    login.add_argument("--wait-ms", type=int, default=300000)
    return parser


def _load_daemon(settings: AppSettings) -> AutonomyDaemon:
    session_factory = create_session_factory(settings)
    init_db(session_factory)
    return AutonomyDaemon(session_factory, settings)


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    settings = AppSettings()
    if getattr(args, "poll_seconds", None):
        settings = settings.model_copy(update={"daemon_poll_interval_seconds": args.poll_seconds})
    daemon = _load_daemon(settings)

    if args.command == "submit":
        job_id = daemon.submit_job(args.brief)
        print(json.dumps({"job_id": job_id, "status": "pending"}))
        if args.wait:
            while True:
                result = daemon.process_pending_jobs(limit=1)
                if result:
                    print(json.dumps(result[0], indent=2))
                    return
                time.sleep(settings.daemon_poll_interval_seconds)
        return

    if args.command == "run-once":
        result = daemon.run_once(args.brief)
        print(json.dumps(result, indent=2))
        return

    if args.command == "serve":
        daemon.serve_forever()
        return

    if args.command == "browser-login":
        result = daemon.search_client.open_login_browser(wait_ms=args.wait_ms) or {}
        if "status" not in result:
            result["status"] = "login_browser_started"
        if "profile_dir" not in result:
            result["profile_dir"] = settings.linkedin_browser_profile_dir
        print(json.dumps(result))
        return

    if args.command == "status":
        with daemon.session_factory() as session:
            from oh_my_gtm.models import AutonomyJob

            job = session.get(AutonomyJob, args.job_id)
            if job is None:
                raise SystemExit(f"Job {args.job_id} not found.")
            print(
                json.dumps(
                    {
                        "job_id": job.id,
                        "status": job.status,
                        "workspace_id": job.workspace_id,
                        "artifact_dir": job.artifact_dir,
                        "error_text": job.error_text,
                        "result": job.result_json,
                    },
                    indent=2,
                )
            )


if __name__ == "__main__":
    main()
