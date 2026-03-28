"""Pydantic schemas used by the services and API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field


class AssumptionItem(BaseModel):
    field_name: str
    inferred_value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class CompanyProfile(BaseModel):
    workspace_name: str
    company_name: str
    product_name: str
    one_line_pitch: str = ""
    product_description: str = ""
    target_market: str = "US B2B SaaS"
    proof_points: list[str] = Field(default_factory=list)
    approved_claims: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    booking_link: str | None = None


class ProductProfile(BaseModel):
    category: str = ""
    value_props: list[str] = Field(default_factory=list)
    differentiation: list[str] = Field(default_factory=list)
    adjacent_tools: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)


class IdealCustomerProfile(BaseModel):
    target_personas: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    company_size_ranges: list[str] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=lambda: ["United States"])
    target_seniority: list[str] = Field(default_factory=list)


class ExclusionRuleInput(BaseModel):
    name: str
    rule_type: str
    config: dict[str, Any] = Field(default_factory=dict)
    is_hard: bool = True


class ExclusionRules(BaseModel):
    rules: list[ExclusionRuleInput] = Field(default_factory=list)


class MessagingConstraints(BaseModel):
    demo_cta_text: str = "Open to a 15-minute demo?"
    linkedin_mode: Literal["compliance_manual", "assisted_semi_auto", "api_only"] = (
        "compliance_manual"
    )
    email_mode: Literal["manual_review", "auto_send"] = "auto_send"
    human_review_required_for_high_risk_claims: bool = True


class ExperimentGoals(BaseModel):
    primary_metric: str = "booked_demo_rate"
    target_reply_rate: float = 0.08
    target_positive_reply_rate: float = 0.03
    target_meeting_rate: float = 0.02


class GTMContextInput(BaseModel):
    company_profile: CompanyProfile
    product_profile: ProductProfile = Field(default_factory=ProductProfile)
    icp_profile: IdealCustomerProfile = Field(default_factory=IdealCustomerProfile)
    exclusion_rules: ExclusionRules = Field(default_factory=ExclusionRules)
    messaging_constraints: MessagingConstraints = Field(default_factory=MessagingConstraints)
    experiment_goals: ExperimentGoals = Field(default_factory=ExperimentGoals)
    competitor_names: list[str] = Field(default_factory=list)
    problem_keywords: list[str] = Field(default_factory=list)


class NormalizedContext(BaseModel):
    product_category: str
    buyer_personas: list[str]
    pain_points: list[str]
    value_props: list[str]
    differentiation: list[str]
    geographies: list[str]
    target_seniority: list[str]
    excluded_personas: list[str]
    competitor_names: list[str]
    adjacent_tools: list[str]
    readiness_to_research: bool
    unresolved_questions: list[str] = Field(default_factory=list)


class WorkspaceCreateRequest(BaseModel):
    workspace_name: str


class ContextPatchRequest(BaseModel):
    company_profile: CompanyProfile | None = None
    product_profile: ProductProfile | None = None
    icp_profile: IdealCustomerProfile | None = None
    exclusion_rules: ExclusionRules | None = None
    messaging_constraints: MessagingConstraints | None = None
    experiment_goals: ExperimentGoals | None = None
    competitor_names: list[str] | None = None
    problem_keywords: list[str] | None = None


class WorkspaceResponse(BaseModel):
    workspace_id: str
    name: str
    context: dict[str, Any]
    normalized_context: dict[str, Any]
    missing_fields: list[str]
    readiness_to_research: bool
    assumptions: list[AssumptionItem]


class UrlSignalInput(BaseModel):
    source_url: str
    source_type: str
    note: str = ""


class CSVSignalIngestionRequest(BaseModel):
    csv_text: str


class VisibleCaptureItem(BaseModel):
    item_type: Literal["post", "participant", "comment", "profile", "company_page"]
    text: str = ""
    author_name: str = ""
    company_name: str = ""
    role: str = ""
    profile_url: str | None = None
    source_url: str | None = None
    engagement_type: str = "visible"
    metadata: dict[str, Any] = Field(default_factory=dict)


class VisibleCaptureIngestionRequest(BaseModel):
    page_url: str
    source_type: str = "linkedin_visible_capture"
    page_type: str = "linkedin_capture"
    items: list[VisibleCaptureItem]
    captured_at: datetime | None = None


class SignalInboxIngestionResult(BaseModel):
    raw_items_created: int
    normalized_items_created: int
    raw_item_ids: list[str] = Field(default_factory=list)
    normalized_item_ids: list[str] = Field(default_factory=list)
    source: str


class AutopilotBriefSpec(BaseModel):
    original_brief: str
    normalized_brief: str
    market_label: str
    outreach_goal: str
    company_name: str
    product_name: str
    one_line_pitch: str
    target_personas: list[str] = Field(default_factory=list)
    target_seniority: list[str] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=lambda: ["United States"])
    problem_keywords: list[str] = Field(default_factory=list)
    competitor_names: list[str] = Field(default_factory=list)
    search_terms: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class LinkedInSearchSpec(BaseModel):
    query: str
    vertical: Literal["people", "companies"]
    limit: int = Field(default=5, ge=1, le=25)


class LinkedInCollectedItem(BaseModel):
    vertical: Literal["people", "companies"]
    entity_name: str
    entity_url: str
    raw_text: str
    lines: list[str] = Field(default_factory=list)
    title: str = ""
    company_name: str = ""
    location: str = ""
    action_label: str = ""


class LinkedInSearchResult(BaseModel):
    query: str
    vertical: Literal["people", "companies"]
    search_url: str
    page_title: str = ""
    items: list[LinkedInCollectedItem] = Field(default_factory=list)
    captured_at: datetime | None = None
    artifact_path: str | None = None


class EmailDraftArtifact(BaseModel):
    candidate_name: str
    company_name: str
    subject: str
    body: str
    evidence_snippet: str
    source_url: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchQueryPlan(BaseModel):
    family: str
    query: str
    expected_precision: float = Field(ge=0.0, le=1.0)
    expected_recall: float = Field(ge=0.0, le=1.0)
    priority: float = Field(ge=0.0, le=1.0)
    filters: dict[str, Any] = Field(default_factory=dict)


class ResearchPlanOut(BaseModel):
    competitor_queries: list[SearchQueryPlan] = Field(default_factory=list)
    pain_point_queries: list[SearchQueryPlan] = Field(default_factory=list)
    tool_comparison_queries: list[SearchQueryPlan] = Field(default_factory=list)
    hiring_signal_queries: list[SearchQueryPlan] = Field(default_factory=list)
    trigger_event_queries: list[SearchQueryPlan] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def all_queries(self) -> list[SearchQueryPlan]:
        return (
            self.competitor_queries
            + self.pain_point_queries
            + self.tool_comparison_queries
            + self.hiring_signal_queries
            + self.trigger_event_queries
        )


class ResearchItem(BaseModel):
    source_type: str
    external_id: str
    url: str
    title: str
    author_name: str
    company_name: str = ""
    text_excerpt: str
    item_type: Literal["post", "discussion", "article", "comment"]
    matched_keywords: list[str] = Field(default_factory=list)
    matched_competitors: list[str] = Field(default_factory=list)
    engagement_type: str = "author"
    recency_days: int = 7
    comments: list[str] = Field(default_factory=list)
    engagers: list[dict[str, str]] = Field(default_factory=list)


class ScoredResearchItem(BaseModel):
    item: ResearchItem
    score: float
    explanation: dict[str, Any]


class CandidateRecord(BaseModel):
    person_name: str
    linkedin_url: str | None = None
    company_name: str = ""
    title: str = ""
    seniority: str = ""
    department: str = ""
    location: str = ""
    source_type: str = ""
    source_url: str = ""
    evidence_snippet: str = ""
    matched_keywords: list[str] = Field(default_factory=list)
    matched_competitors: list[str] = Field(default_factory=list)
    recent_signals: list[str] = Field(default_factory=list)
    fit_score: float = 0.0
    intent_score: float = 0.0
    data_quality_score: float = 0.0
    policy_risk_score: float = 0.0
    priority_score: float = 0.0
    exclusion_reason: str | None = None
    qualification_status: str = "draft"


class EnrichmentResult(BaseModel):
    role_category: str
    likely_pain_points: list[str]
    company_size_bucket: str
    industry: str
    growth_stage: str
    tooling_maturity: str
    buying_authority: str
    confidence: dict[str, float]
    evidence: list[str]


class ClusterRecord(BaseModel):
    cluster_key: str
    cluster_name: str
    lead_count: int
    primary_persona: str
    primary_signal: str
    why_now_type: str
    company_band: str
    recommended_channel_mix: str
    sample_evidence: list[str]


class HypothesisRecord(BaseModel):
    title: str
    statement: str
    target_problem: str
    why_now_reason: str
    supporting_signals: list[str]
    recommended_proof_points: list[str]
    recommended_channel: str
    recommended_cta: str
    disqualifiers: list[str]
    confidence_score: float
    counterargument: str
    invalidation_evidence: str


class MessageVariantRecord(BaseModel):
    angle: str
    channel: str
    stage: str
    variant_label: str
    opener_text: str
    body_text: str
    cta_text: str
    expected_risk: str
    expected_reply_likelihood: float
    proof_points_used: list[str]
    risk_flags: list[str] = Field(default_factory=list)
    quality_score: float = 0.0


class AssignmentRecord(BaseModel):
    candidate_name: str
    company_name: str
    variant_label: str
    channel: str
    stage: str
    holdout: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class LinkedInPrepareRequest(BaseModel):
    candidate_name: str
    company_name: str = ""
    linkedin_url: str | None = None
    title: str = ""
    evidence_snippet: str = ""
    variant_label: str = "A"
    angle: str = "pain-led"
    stage: str = "first_touch"
    opener_text: str
    body_text: str = ""
    cta_text: str = ""
    proof_points_used: list[str] = Field(default_factory=list)
    mode: Literal["compliance_manual", "assisted_semi_auto", "api_only"] = "compliance_manual"


class LinkedInAgentPlan(BaseModel):
    mode: str
    target_profile_url: str
    fallback_search_url: str
    stage: str
    candidate_name: str
    company_name: str
    note_text: str
    playwright_commands: list[str]
    operator_steps: list[str]
    completion_requirements: list[str]
    final_send_blocked: bool
    evidence_snippet: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class LinkedInExecuteRequest(BaseModel):
    plan: LinkedInAgentPlan
    dry_run: bool = True


class LinkedInExecutionResult(BaseModel):
    status: str
    dry_run: bool
    executed_steps: list[str]
    outputs: list[dict[str, Any]] = Field(default_factory=list)
    artifact_dir: str | None = None
    final_send_blocked: bool = True


class LLMRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    response_format: Literal["text", "json"] = "text"
    json_schema: dict[str, Any] | None = None


class LLMResponse(BaseModel):
    content: str
    parsed_json: dict[str, Any] | None = None
    model: str
    provider: str


class ResponseClassificationResult(BaseModel):
    label: str
    sentiment: str
    urgency: str
    objection_type: str | None = None
    next_step_requested: str | None = None
    confidence: float
    evidence_snippet: str


class MetricResult(BaseModel):
    metric_name: str
    value: float
    details: dict[str, Any] = Field(default_factory=dict)


class OptimizationDecisionResult(BaseModel):
    decision_type: str
    subject_type: str
    subject_id: str
    reason: str
    recommendation: dict[str, Any]


class WorkflowStageSummary(BaseModel):
    stage_name: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunResponse(BaseModel):
    workflow_run_id: str
    workspace_id: str
    status: str
    current_stage: str
    stages: list[WorkflowStageSummary]
    created_at: datetime | None = None
