"""Structured audit logging helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from oh_my_gtm.models import AuditLog


def emit_audit_log(
    session: Session,
    *,
    workspace_id: str | None,
    correlation_id: str,
    event_type: str,
    severity: str = "info",
    actor_type: str = "system",
    actor_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditLog:
    log = AuditLog(
        workspace_id=workspace_id,
        correlation_id=correlation_id,
        event_type=event_type,
        severity=severity,
        actor_type=actor_type,
        actor_id=actor_id,
        payload_json=payload or {},
    )
    session.add(log)
    session.flush()
    return log
