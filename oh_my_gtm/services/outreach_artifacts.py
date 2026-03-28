"""Build operator-ready outreach artifacts from workflow results."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from oh_my_gtm.models import CandidateTarget, MessageVariant
from oh_my_gtm.schemas import AutopilotBriefSpec, EmailDraftArtifact


def _first_name(full_name: str) -> str:
    return full_name.split()[0] if full_name.strip() else "there"


def _personalize_body(candidate: CandidateTarget, variant: MessageVariant, spec: AutopilotBriefSpec) -> str:
    intro = f"Hi {_first_name(candidate.person_name)},"
    evidence = candidate.evidence_snippet or f"I came across your work while researching {spec.market_label}."
    company_line = f" at {candidate.company_name}" if candidate.company_name else ""
    return "\n\n".join(
        [
            intro,
            f"I found your role{company_line} while researching {spec.market_label}. {evidence}",
            f"{variant.opener_text} {variant.body_text}",
            variant.cta_text,
            "Best,\nOperator Research Desk",
        ]
    )


def build_email_drafts(session: Session, workspace_id: str, spec: AutopilotBriefSpec, *, limit: int = 5) -> list[EmailDraftArtifact]:
    candidates = session.scalars(
        select(CandidateTarget)
        .where(CandidateTarget.workspace_id == workspace_id, CandidateTarget.qualification_status != "Reject")
        .order_by(CandidateTarget.priority_score.desc(), CandidateTarget.person_name.asc())
    ).all()
    variants = session.scalars(
        select(MessageVariant)
        .where(MessageVariant.workspace_id == workspace_id, MessageVariant.channel == "email")
        .order_by(MessageVariant.readability_score.desc(), MessageVariant.variant_label.asc())
    ).all()
    if not candidates or not variants:
        return []
    drafts: list[EmailDraftArtifact] = []
    for index, candidate in enumerate(candidates[:limit]):
        variant = variants[index % len(variants)]
        subject = f"{candidate.company_name or spec.market_label}: quick intro"[:120]
        drafts.append(
            EmailDraftArtifact(
                candidate_name=candidate.person_name,
                company_name=candidate.company_name,
                subject=subject,
                body=_personalize_body(candidate, variant, spec),
                evidence_snippet=candidate.evidence_snippet,
                source_url=candidate.source_url,
                confidence=min(0.92, max(0.35, candidate.priority_score / 100.0)),
                metadata={
                    "variant_label": variant.variant_label,
                    "channel": "email",
                    "market_label": spec.market_label,
                },
            )
        )
    return drafts


def write_email_drafts(artifact_dir: Path, drafts: list[EmailDraftArtifact]) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    target = artifact_dir / "email_drafts.json"
    target.write_text(json.dumps([draft.model_dump() for draft in drafts], indent=2), encoding="utf-8")
    return target
