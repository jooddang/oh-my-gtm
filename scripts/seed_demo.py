"""Seed a demo workspace and execute the workflow."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from oh_my_gtm.api.app import create_app
from oh_my_gtm.config import AppSettings
from oh_my_gtm.models import Workspace


def main() -> None:
    settings = AppSettings(database_url="sqlite+pysqlite:///./demo_seed.db")
    app = create_app(settings)
    session_factory = app.state.session_factory
    with session_factory() as session:
        workspace = Workspace(name="Demo Workspace")
        workspace.context_json = {
            "company_profile": {
                "workspace_name": "Demo Workspace",
                "company_name": "Oh My GTM",
                "product_name": "oh-my-gtm",
                "one_line_pitch": "Autonomous GTM workflow for outbound research and messaging",
                "product_description": "Policy-aware outbound research, hypothesis generation, and message orchestration for B2B SaaS teams.",
                "proof_points": ["fast setup", "closed-loop learning"],
                "approved_claims": ["fast setup"],
                "forbidden_claims": ["guaranteed meetings"],
                "target_market": "US B2B SaaS",
                "booking_link": "https://example.com/book",
            },
            "product_profile": {
                "category": "gtm-automation",
                "value_props": ["reduces manual outbound work", "improves experimentation speed"],
                "differentiation": ["policy-aware execution"],
                "adjacent_tools": ["Apollo", "HubSpot"],
                "pain_points": ["manual follow-up", "poor visibility"],
            },
            "icp_profile": {
                "target_personas": ["RevOps Leader", "Growth Leader"],
                "industries": ["B2B SaaS"],
                "company_size_ranges": ["11-200"],
                "geographies": ["United States"],
                "target_seniority": ["executive", "manager"],
            },
            "exclusion_rules": {
                "rules": [
                    {"name": "block_students", "rule_type": "keyword_pattern", "config": {"keywords": ["student", "intern"]}, "is_hard": True}
                ]
            },
            "messaging_constraints": {
                "demo_cta_text": "Open to a 15-minute demo next week?",
                "linkedin_mode": "compliance_manual",
                "email_mode": "auto_send",
                "human_review_required_for_high_risk_claims": True,
            },
            "experiment_goals": {
                "primary_metric": "booked_demo_rate",
                "target_reply_rate": 0.08,
                "target_positive_reply_rate": 0.03,
                "target_meeting_rate": 0.02,
            },
            "competitor_names": ["Apollo", "Outreach"],
            "problem_keywords": ["manual follow-up", "tool sprawl"],
        }
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
    result = app.state.workflow_engine.run(workspace.id, dry_run=True)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
