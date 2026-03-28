"""Signal Inbox ingestion for URLs, CSV uploads, and visible capture payloads."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy.orm import Session

from oh_my_gtm.models import ResearchItemNormalized, ResearchItemRaw
from oh_my_gtm.schemas import CSVSignalIngestionRequest, SignalInboxIngestionResult, UrlSignalInput, VisibleCaptureIngestionRequest


def _infer_item_type_from_url(url: str, source_type: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.lower()
    if "linkedin.com" in parsed.netloc:
        if "/posts/" in path or "/feed/update/" in path:
            return "post"
        if "/in/" in path:
            return "comment" if source_type == "person_profile_url" else "post"
        if "/company/" in path:
            return "article"
    if "blog" in source_type:
        return "article"
    return "discussion"


def ingest_url_signals(session: Session, workspace_id: str, signals: list[UrlSignalInput]) -> SignalInboxIngestionResult:
    raw_ids: list[str] = []
    normalized_ids: list[str] = []
    for signal in signals:
        raw = ResearchItemRaw(
            workspace_id=workspace_id,
            source_type=signal.source_type,
            external_id=str(uuid4()),
            url=signal.source_url,
            payload_json=signal.model_dump(),
            captured_at=datetime.utcnow(),
        )
        session.add(raw)
        session.flush()
        normalized = ResearchItemNormalized(
            workspace_id=workspace_id,
            raw_item_id=raw.id,
            item_type=_infer_item_type_from_url(signal.source_url, signal.source_type),
            canonical_url=signal.source_url,
            title=signal.note or signal.source_url,
            author_name="",
            company_name="",
            text_excerpt=signal.note,
            normalized_json={
                "source_type": signal.source_type,
                "external_id": raw.external_id,
                "url": signal.source_url,
                "title": signal.note or signal.source_url,
                "author_name": "",
                "company_name": "",
                "text_excerpt": signal.note,
                "item_type": _infer_item_type_from_url(signal.source_url, signal.source_type),
                "matched_keywords": [],
                "matched_competitors": [],
                "engagement_type": "provided_url",
                "recency_days": 1,
                "comments": [],
                "engagers": [],
            },
        )
        session.add(normalized)
        session.flush()
        raw_ids.append(raw.id)
        normalized_ids.append(normalized.id)
    return SignalInboxIngestionResult(
        raw_items_created=len(raw_ids),
        normalized_items_created=len(normalized_ids),
        raw_item_ids=raw_ids,
        normalized_item_ids=normalized_ids,
        source="url",
    )


def ingest_csv_signals(session: Session, workspace_id: str, request: CSVSignalIngestionRequest) -> SignalInboxIngestionResult:
    rows = list(csv.DictReader(io.StringIO(request.csv_text)))
    signals = []
    for row in rows:
        source_url = row.get("source_url", "") or row.get("profile_url", "")
        source_type = row.get("source_type", "csv_import")
        note_parts = [
            row.get("post_text", ""),
            row.get("author_name", ""),
            row.get("company_name", ""),
            row.get("participant_name", ""),
            row.get("participant_role", ""),
            row.get("note", ""),
        ]
        signals.append(UrlSignalInput(source_url=source_url, source_type=source_type, note=" | ".join(part for part in note_parts if part)))
    result = ingest_url_signals(session, workspace_id, signals)
    result.source = "csv"
    return result


def ingest_visible_capture(session: Session, workspace_id: str, request: VisibleCaptureIngestionRequest) -> SignalInboxIngestionResult:
    raw_ids: list[str] = []
    normalized_ids: list[str] = []
    for item in request.items:
        payload = {
            "page_url": request.page_url,
            "page_type": request.page_type,
            "source_type": request.source_type,
            "captured_at": (request.captured_at or datetime.utcnow()).isoformat(),
            "item": item.model_dump(),
        }
        raw = ResearchItemRaw(
            workspace_id=workspace_id,
            source_type=request.source_type,
            external_id=str(uuid4()),
            url=item.source_url or request.page_url,
            payload_json=payload,
            captured_at=request.captured_at or datetime.utcnow(),
        )
        session.add(raw)
        session.flush()
        normalized = ResearchItemNormalized(
            workspace_id=workspace_id,
            raw_item_id=raw.id,
            item_type="comment" if item.item_type == "participant" else "post" if item.item_type == "post" else "article",
            canonical_url=item.source_url or request.page_url,
            title=item.text[:120] or item.item_type,
            author_name=item.author_name,
            company_name=item.company_name,
            text_excerpt=item.text,
            normalized_json={
                "source_type": request.source_type,
                "external_id": raw.external_id,
                "url": item.source_url or request.page_url,
                "title": item.text[:120] or item.item_type,
                "author_name": item.author_name,
                "company_name": item.company_name,
                "text_excerpt": item.text,
                "item_type": "post" if item.item_type in {"post", "company_page"} else "comment",
                "matched_keywords": [],
                "matched_competitors": [],
                "engagement_type": item.engagement_type,
                "recency_days": 1,
                "comments": [item.text] if item.item_type == "comment" else [],
                "engagers": [
                    {
                        "name": item.author_name,
                        "title": item.role,
                        "company": item.company_name,
                    }
                ]
                if item.author_name
                else [],
            },
        )
        session.add(normalized)
        session.flush()
        raw_ids.append(raw.id)
        normalized_ids.append(normalized.id)
    return SignalInboxIngestionResult(
        raw_items_created=len(raw_ids),
        normalized_items_created=len(normalized_ids),
        raw_item_ids=raw_ids,
        normalized_item_ids=normalized_ids,
        source="visible_capture",
    )
