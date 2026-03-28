"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oh_my_gtm.database import Base


def _uuid() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    context_json: Mapped[dict] = mapped_column(JSON, default=dict)
    normalized_context_json: Mapped[dict] = mapped_column(JSON, default=dict)
    missing_fields_json: Mapped[list] = mapped_column(JSON, default=list)
    readiness_to_research: Mapped[bool] = mapped_column(Boolean, default=False)
    assumption_summary_json: Mapped[list] = mapped_column(JSON, default=list)

    assumptions: Mapped[list["AssumptionLog"]] = relationship(back_populates="workspace")


class AssumptionLog(Base):
    __tablename__ = "assumption_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    inferred_value_json: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    rationale: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workspace: Mapped[Workspace] = relationship(back_populates="assumptions")


class ExclusionRule(Base, TimestampMixin):
    __tablename__ = "exclusion_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    rule_type: Mapped[str] = mapped_column(String(50))
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    is_hard: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ResearchPlan(Base, TimestampMixin):
    __tablename__ = "research_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    plan_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ResearchQuery(Base, TimestampMixin):
    __tablename__ = "research_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(ForeignKey("research_plans.id"), index=True)
    family: Mapped[str] = mapped_column(String(80))
    query_text: Mapped[str] = mapped_column(Text)
    expected_precision: Mapped[float] = mapped_column(Float, default=0.5)
    expected_recall: Mapped[float] = mapped_column(Float, default=0.5)
    priority: Mapped[float] = mapped_column(Float, default=0.5)
    filters_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ResearchItemRaw(Base):
    __tablename__ = "research_items_raw"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(60))
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    url: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ResearchItemNormalized(Base):
    __tablename__ = "research_items_normalized"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    raw_item_id: Mapped[str] = mapped_column(ForeignKey("research_items_raw.id"), index=True)
    item_type: Mapped[str] = mapped_column(String(60))
    canonical_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    author_name: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str] = mapped_column(String(255), default="")
    text_excerpt: Mapped[str] = mapped_column(Text, default="")
    normalized_json: Mapped[dict] = mapped_column(JSON, default=dict)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    explanation_json: Mapped[dict] = mapped_column(JSON, default=dict)


class CandidateTarget(Base, TimestampMixin):
    __tablename__ = "candidate_targets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    person_name: Mapped[str] = mapped_column(String(255))
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), default="")
    company_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    seniority: Mapped[str] = mapped_column(String(80), default="")
    department: Mapped[str] = mapped_column(String(80), default="")
    location: Mapped[str] = mapped_column(String(120), default="")
    source_type: Mapped[str] = mapped_column(String(60), default="")
    source_url: Mapped[str] = mapped_column(Text, default="")
    evidence_snippet: Mapped[str] = mapped_column(Text, default="")
    matched_keywords_json: Mapped[list] = mapped_column(JSON, default=list)
    matched_competitors_json: Mapped[list] = mapped_column(JSON, default=list)
    recent_signals_json: Mapped[list] = mapped_column(JSON, default=list)
    fit_score: Mapped[float] = mapped_column(Float, default=0.0)
    intent_score: Mapped[float] = mapped_column(Float, default=0.0)
    data_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    policy_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    exclusion_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification_status: Mapped[str] = mapped_column(String(50), default="draft")
    segment_key: Mapped[str] = mapped_column(String(255), default="")
    cluster_id: Mapped[str | None] = mapped_column(ForeignKey("target_clusters.id"), nullable=True)


class EnrichmentRecord(Base, TimestampMixin):
    __tablename__ = "enrichment_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_targets.id"), index=True)
    enrichment_json: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence_json: Mapped[dict] = mapped_column(JSON, default=dict)


class TargetCluster(Base, TimestampMixin):
    __tablename__ = "target_clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    cluster_name: Mapped[str] = mapped_column(String(255))
    lead_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_persona: Mapped[str] = mapped_column(String(120), default="")
    primary_signal: Mapped[str] = mapped_column(String(120), default="")
    why_now_type: Mapped[str] = mapped_column(String(120), default="")
    company_band: Mapped[str] = mapped_column(String(120), default="")
    recommended_channel_mix: Mapped[str] = mapped_column(String(120), default="")
    sample_evidence_json: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="draft")


class Hypothesis(Base, TimestampMixin):
    __tablename__ = "hypotheses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    cluster_id: Mapped[str] = mapped_column(ForeignKey("target_clusters.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    statement: Mapped[str] = mapped_column(Text)
    target_problem: Mapped[str] = mapped_column(Text)
    why_now_reason: Mapped[str] = mapped_column(Text)
    supporting_signals_json: Mapped[list] = mapped_column(JSON, default=list)
    recommended_proof_points_json: Mapped[list] = mapped_column(JSON, default=list)
    recommended_channel: Mapped[str] = mapped_column(String(80))
    recommended_cta: Mapped[str] = mapped_column(String(255))
    disqualifiers_json: Mapped[list] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    score_card_json: Mapped[dict] = mapped_column(JSON, default=dict)


class HypothesisEvidence(Base):
    __tablename__ = "hypothesis_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("hypotheses.id"), index=True)
    candidate_id: Mapped[str | None] = mapped_column(ForeignKey("candidate_targets.id"), nullable=True)
    evidence_snippet: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(Text, default="")
    evidence_type: Mapped[str] = mapped_column(String(60), default="")


class MessageVariant(Base, TimestampMixin):
    __tablename__ = "message_variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("hypotheses.id"), index=True)
    channel: Mapped[str] = mapped_column(String(60))
    stage: Mapped[str] = mapped_column(String(60))
    variant_label: Mapped[str] = mapped_column(String(10))
    objective: Mapped[str] = mapped_column(String(80))
    opener_text: Mapped[str] = mapped_column(Text, default="")
    body_text: Mapped[str] = mapped_column(Text, default="")
    cta_text: Mapped[str] = mapped_column(Text, default="")
    proof_points_used_json: Mapped[list] = mapped_column(JSON, default=list)
    prohibited_claim_check: Mapped[str] = mapped_column(String(20), default="pass")
    readability_score: Mapped[float] = mapped_column(Float, default=0.0)
    personalization_mode: Mapped[str] = mapped_column(String(40), default="light")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ExperimentAssignment(Base, TimestampMixin):
    __tablename__ = "experiment_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_targets.id"), index=True)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("hypotheses.id"), index=True)
    message_variant_id: Mapped[str | None] = mapped_column(ForeignKey("message_variants.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50))
    stage: Mapped[str] = mapped_column(String(50))
    cohort_key: Mapped[str] = mapped_column(String(255), default="")
    assignment_group: Mapped[str] = mapped_column(String(20), default="")
    holdout: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default="assigned")


class OutboundAction(Base, TimestampMixin):
    __tablename__ = "outbound_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_targets.id"), index=True)
    message_variant_id: Mapped[str | None] = mapped_column(ForeignKey("message_variants.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(60))
    stage: Mapped[str] = mapped_column(String(50))
    mode: Mapped[str] = mapped_column(String(60))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    outcome: Mapped[str] = mapped_column(String(50), default="queued")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)


class InboundResponse(Base):
    __tablename__ = "inbound_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_targets.id"), index=True)
    channel: Mapped[str] = mapped_column(String(60))
    thread_id: Mapped[str] = mapped_column(String(255))
    message_text: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    parsed_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ResponseClassification(Base):
    __tablename__ = "response_classifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    response_id: Mapped[str] = mapped_column(ForeignKey("inbound_responses.id"), index=True)
    label: Mapped[str] = mapped_column(String(50))
    sentiment: Mapped[str] = mapped_column(String(50), default="")
    urgency: Mapped[str] = mapped_column(String(50), default="")
    objection_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    next_step_requested: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    evidence_snippet: Mapped[str] = mapped_column(Text, default="")
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    metric_name: Mapped[str] = mapped_column(String(80))
    time_window: Mapped[str] = mapped_column(String(80))
    slice_key: Mapped[str] = mapped_column(String(255), default="all")
    value: Mapped[float] = mapped_column(Float, default=0.0)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OptimizationDecision(Base):
    __tablename__ = "optimization_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    decision_type: Mapped[str] = mapped_column(String(80))
    subject_type: Mapped[str] = mapped_column(String(80))
    subject_id: Mapped[str] = mapped_column(String(36))
    reason: Mapped[str] = mapped_column(Text)
    recommendation_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WorkflowRun(Base, TimestampMixin):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="running")
    stage_order_json: Mapped[list] = mapped_column(JSON, default=list)
    current_stage: Mapped[str] = mapped_column(String(80), default="")
    correlation_id: Mapped[str] = mapped_column(String(100), index=True)
    budget_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class WorkflowStageRun(Base):
    __tablename__ = "workflow_stage_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workflow_run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id"), index=True)
    stage_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20), default="info")
    correlation_id: Mapped[str] = mapped_column(String(100), index=True)
    actor_type: Mapped[str] = mapped_column(String(50), default="system")
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AutonomyJob(Base, TimestampMixin):
    __tablename__ = "autonomy_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    brief_text: Mapped[str] = mapped_column(Text, default="")
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True, index=True)
    request_json: Mapped[dict] = mapped_column(JSON, default=dict)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    artifact_dir: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
