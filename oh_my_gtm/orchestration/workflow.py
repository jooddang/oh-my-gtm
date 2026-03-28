"""Resumable autonomous workflow engine."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from oh_my_gtm.config import AppSettings
from oh_my_gtm.models import (
    AssumptionLog,
    CandidateTarget,
    EnrichmentRecord,
    ExperimentAssignment,
    Hypothesis,
    MetricSnapshot,
    OptimizationDecision,
    OutboundAction,
    ResearchItemNormalized,
    ResearchItemRaw,
    ResearchPlan,
    ResearchQuery,
    ResponseClassification,
    TargetCluster,
    WorkflowRun,
    WorkflowStageRun,
    Workspace,
)
from oh_my_gtm.schemas import GTMContextInput, ResearchItem, WorkflowRunResponse, WorkflowStageSummary
from oh_my_gtm.services.analytics import compute_metrics, compute_variant_uplift
from oh_my_gtm.services.audit import emit_audit_log
from oh_my_gtm.services.context import normalize_context
from oh_my_gtm.services.execution import execute_assignments
from oh_my_gtm.services.llm import LLMNotConfiguredError, OpenAIResponsesClient, llm_classify_reply, llm_enrich_candidate, llm_generate_hypotheses, llm_generate_message_variants
from oh_my_gtm.services.messaging import allocate_experiments, generate_initial_variants
from oh_my_gtm.services.optimization import optimize_hypotheses
from oh_my_gtm.services.replies import classify_reply
from oh_my_gtm.services.research import create_research_plan, run_mock_research, score_research_items
from oh_my_gtm.services.targeting import cluster_candidates, enrich_candidate, evaluate_exclusions, extract_candidates, generate_hypotheses, rank_hypotheses, score_candidate


STAGES = [
    "collect_or_refresh_context",
    "create_research_plan",
    "fetch_research_items",
    "score_items",
    "extract_targets",
    "enrich_targets",
    "generate_hypotheses",
    "allocate_experiments",
    "generate_messages",
    "execute_outbound",
    "ingest_responses",
    "compute_metrics",
    "optimize_strategy",
]


class WorkflowEngine:
    """Sequential workflow runner with persistent stage state."""

    def __init__(self, session_factory: sessionmaker[Session], settings: AppSettings) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.llm_client = OpenAIResponsesClient(settings)

    def run(self, workspace_id: str, *, dry_run: bool = True) -> WorkflowRunResponse:
        correlation_id = str(uuid4())
        with self.session_factory() as session:
            workspace = session.get(Workspace, workspace_id)
            if workspace is None:
                raise ValueError(f"Workspace {workspace_id} not found.")
            workflow = WorkflowRun(
                workspace_id=workspace_id,
                status="running",
                stage_order_json=STAGES,
                current_stage=STAGES[0],
                correlation_id=correlation_id,
                budget_json={
                    "max_daily_email_sends": self.settings.max_daily_email_sends,
                    "max_daily_linkedin_preps": self.settings.max_daily_linkedin_preps,
                },
            )
            session.add(workflow)
            session.flush()

            emit_audit_log(
                session,
                workspace_id=workspace_id,
                correlation_id=correlation_id,
                event_type="workflow.started",
                payload={"workflow_run_id": workflow.id},
            )

            for stage_name in STAGES:
                workflow.current_stage = stage_name
                stage = WorkflowStageRun(workflow_run_id=workflow.id, stage_name=stage_name, status="running")
                session.add(stage)
                session.flush()
                details = self._run_stage(session, workspace, workflow, stage_name, dry_run=dry_run)
                stage.status = "completed"
                stage.completed_at = datetime.utcnow()
                stage.details_json = details
                emit_audit_log(
                    session,
                    workspace_id=workspace_id,
                    correlation_id=correlation_id,
                    event_type=f"workflow.stage.{stage_name}",
                    payload=details,
                )
                session.flush()

            workflow.status = "completed"
            session.commit()
            return describe_workflow_run(session, workflow.id)

    def _run_stage(self, session: Session, workspace: Workspace, workflow: WorkflowRun, stage_name: str, *, dry_run: bool) -> dict:
        context = GTMContextInput.model_validate(workspace.context_json)
        normalized, assumptions, missing = normalize_context(context)
        if stage_name == "collect_or_refresh_context":
            workspace.normalized_context_json = normalized.model_dump()
            workspace.missing_fields_json = missing
            workspace.readiness_to_research = normalized.readiness_to_research
            workspace.assumption_summary_json = [assumption.model_dump() for assumption in assumptions]
            for assumption in assumptions:
                session.add(
                    AssumptionLog(
                        workspace_id=workspace.id,
                        field_name=assumption.field_name,
                        inferred_value_json={"value": assumption.inferred_value},
                        confidence=assumption.confidence,
                        rationale=assumption.rationale,
                    )
                )
            return {"missing_fields": missing, "readiness_to_research": normalized.readiness_to_research}

        if stage_name == "create_research_plan":
            plan = create_research_plan(normalized, context)
            plan_row = ResearchPlan(workspace_id=workspace.id, status="active", plan_json=plan.model_dump())
            session.add(plan_row)
            session.flush()
            for query in plan.all_queries:
                session.add(
                    ResearchQuery(
                        plan_id=plan_row.id,
                        family=query.family,
                        query_text=query.query,
                        expected_precision=query.expected_precision,
                        expected_recall=query.expected_recall,
                        priority=query.priority,
                        filters_json=query.filters,
                    )
                )
            return {"queries_created": len(plan.all_queries)}

        plan_row = session.scalars(
            select(ResearchPlan).where(ResearchPlan.workspace_id == workspace.id).order_by(ResearchPlan.created_at.desc())
        ).first()
        plan = create_research_plan(normalized, context) if plan_row is None else plan_row.plan_json

        if stage_name == "fetch_research_items":
            existing = session.scalars(select(ResearchItemNormalized).where(ResearchItemNormalized.workspace_id == workspace.id)).all()
            if existing:
                return {"items_created": 0, "source": "signal_inbox", "existing_items": len(existing)}
            items = run_mock_research(create_research_plan(normalized, context))
            for item in items:
                raw = ResearchItemRaw(
                    workspace_id=workspace.id,
                    source_type=item.source_type,
                    external_id=item.external_id,
                    url=item.url,
                    payload_json=item.model_dump(),
                )
                session.add(raw)
                session.flush()
                session.add(
                    ResearchItemNormalized(
                        workspace_id=workspace.id,
                        raw_item_id=raw.id,
                        item_type=item.item_type,
                        canonical_url=item.url,
                        title=item.title,
                        author_name=item.author_name,
                        company_name=item.company_name,
                        text_excerpt=item.text_excerpt,
                        normalized_json=item.model_dump(),
                    )
                )
            return {"items_created": len(items)}

        normalized_rows = session.scalars(select(ResearchItemNormalized).where(ResearchItemNormalized.workspace_id == workspace.id)).all()
        scored_items = score_research_items(
            [ResearchItem.model_validate(row.normalized_json) for row in normalized_rows],
            normalized,
        )
        if stage_name == "score_items":
            by_url = {entry.item.url: entry for entry in scored_items}
            for row in normalized_rows:
                entry = by_url[row.canonical_url]
                row.relevance_score = entry.score
                row.explanation_json = entry.explanation
            return {"scored_items": len(scored_items), "top_score": scored_items[0].score if scored_items else 0}

        if stage_name == "extract_targets":
            candidates = extract_candidates(scored_items)
            for candidate in candidates:
                session.add(
                    CandidateTarget(
                        workspace_id=workspace.id,
                        person_name=candidate.person_name,
                        linkedin_url=candidate.linkedin_url,
                        company_name=candidate.company_name,
                        title=candidate.title,
                        seniority=candidate.seniority,
                        department=candidate.department,
                        location=candidate.location,
                        source_type=candidate.source_type,
                        source_url=candidate.source_url,
                        evidence_snippet=candidate.evidence_snippet,
                        matched_keywords_json=candidate.matched_keywords,
                        matched_competitors_json=candidate.matched_competitors,
                        recent_signals_json=candidate.recent_signals,
                    )
                )
            return {"candidates_created": len(candidates)}

        candidate_rows = session.scalars(select(CandidateTarget).where(CandidateTarget.workspace_id == workspace.id)).all()
        candidate_models = []
        for row in candidate_rows:
            candidate_models.append(
                type(
                    "CandidateProxy",
                    (),
                    {
                        "person_name": row.person_name,
                        "linkedin_url": row.linkedin_url,
                        "company_name": row.company_name,
                        "title": row.title,
                        "seniority": row.seniority,
                        "department": row.department,
                        "location": row.location,
                        "source_type": row.source_type,
                        "source_url": row.source_url,
                        "evidence_snippet": row.evidence_snippet,
                        "matched_keywords": row.matched_keywords_json,
                        "matched_competitors": row.matched_competitors_json,
                        "recent_signals": row.recent_signals_json,
                        "fit_score": row.fit_score,
                        "intent_score": row.intent_score,
                        "data_quality_score": row.data_quality_score,
                        "policy_risk_score": row.policy_risk_score,
                        "priority_score": row.priority_score,
                        "exclusion_reason": row.exclusion_reason,
                        "qualification_status": row.qualification_status,
                    },
                )()
            )

        if stage_name == "enrich_targets":
            qualified_count = 0
            for row, candidate in zip(candidate_rows, candidate_models, strict=True):
                enrichment = enrich_candidate(candidate, normalized)
                try:
                    enrichment = llm_enrich_candidate(self.llm_client, candidate, normalized, enrichment)
                except (LLMNotConfiguredError, Exception):
                    pass
                scored = score_candidate(candidate, enrichment, normalized)
                excluded, reasons = evaluate_exclusions(scored, context.exclusion_rules, normalized.competitor_names)
                row.fit_score = scored.fit_score
                row.intent_score = scored.intent_score
                row.data_quality_score = scored.data_quality_score
                row.policy_risk_score = scored.policy_risk_score
                row.priority_score = scored.priority_score
                row.qualification_status = "Reject" if excluded else scored.qualification_status
                row.exclusion_reason = ", ".join(reasons) if reasons else None
                session.add(
                    EnrichmentRecord(
                        workspace_id=workspace.id,
                        candidate_id=row.id,
                        enrichment_json=enrichment.model_dump(),
                        confidence_json=enrichment.confidence,
                    )
                )
                if row.qualification_status != "Reject":
                    qualified_count += 1
            return {"qualified_candidates": qualified_count, "total_candidates": len(candidate_rows)}

        if stage_name == "generate_hypotheses":
            eligible_rows = [row for row in candidate_rows if row.qualification_status != "Reject"]
            candidates_for_clusters = [
                type(
                    "CandidateProxy",
                    (),
                    {
                        "person_name": row.person_name,
                        "company_name": row.company_name,
                        "title": row.title,
                        "seniority": row.seniority,
                        "department": row.department,
                        "evidence_snippet": row.evidence_snippet,
                        "recent_signals": row.recent_signals_json,
                    },
                )()
                for row in eligible_rows
            ]
            clusters = cluster_candidates(candidates_for_clusters)
            created = 0
            for cluster in clusters:
                cluster_row = TargetCluster(
                    workspace_id=workspace.id,
                    cluster_name=cluster.cluster_name,
                    lead_count=cluster.lead_count,
                    primary_persona=cluster.primary_persona,
                    primary_signal=cluster.primary_signal,
                    why_now_type=cluster.why_now_type,
                    company_band=cluster.company_band,
                    recommended_channel_mix=cluster.recommended_channel_mix,
                    sample_evidence_json=cluster.sample_evidence,
                    status="active" if cluster.lead_count >= 1 else "draft",
                )
                session.add(cluster_row)
                session.flush()
                generated_hypotheses = generate_hypotheses(cluster, normalized, context)
                try:
                    generated_hypotheses = llm_generate_hypotheses(self.llm_client, cluster.model_dump(), normalized, generated_hypotheses)
                except (LLMNotConfiguredError, Exception):
                    pass
                for hypothesis in rank_hypotheses(generated_hypotheses)[:3]:
                    session.add(
                        Hypothesis(
                            workspace_id=workspace.id,
                            cluster_id=cluster_row.id,
                            title=hypothesis.title,
                            statement=hypothesis.statement,
                            target_problem=hypothesis.target_problem,
                            why_now_reason=hypothesis.why_now_reason,
                            supporting_signals_json=hypothesis.supporting_signals,
                            recommended_proof_points_json=hypothesis.recommended_proof_points,
                            recommended_channel=hypothesis.recommended_channel,
                            recommended_cta=hypothesis.recommended_cta,
                            disqualifiers_json=hypothesis.disqualifiers,
                            confidence_score=hypothesis.confidence_score,
                            status="approved" if hypothesis.confidence_score >= 0.65 else "draft",
                            score_card_json={"counterargument": hypothesis.counterargument},
                        )
                    )
                    created += 1
            return {"clusters_created": len(clusters), "hypotheses_created": created}

        hypothesis_rows = session.scalars(select(Hypothesis).where(Hypothesis.workspace_id == workspace.id)).all()
        if stage_name == "allocate_experiments":
            approved_hypothesis = next((hypothesis for hypothesis in hypothesis_rows if hypothesis.status == "approved"), None)
            eligible_rows = [row for row in candidate_rows if row.qualification_status in {"Tier A", "Tier B", "Tier C"}]
            if approved_hypothesis is None:
                return {"assignments_created": 0}
            hypothesis_record = type(
                "HypothesisProxy",
                (),
                {
                    "title": approved_hypothesis.title,
                    "statement": approved_hypothesis.statement,
                    "target_problem": approved_hypothesis.target_problem,
                    "recommended_proof_points": approved_hypothesis.recommended_proof_points_json,
                    "recommended_cta": approved_hypothesis.recommended_cta,
                    "counterargument": approved_hypothesis.score_card_json.get("counterargument", ""),
                },
            )()
            candidate_records = [
                type(
                    "CandidateProxy",
                    (),
                    {
                        "person_name": row.person_name,
                        "company_name": row.company_name,
                        "priority_score": row.priority_score,
                        "seniority": row.seniority,
                    },
                )()
                for row in eligible_rows
            ]
            variants = generate_initial_variants(hypothesis_record, context, channel="email")
            assignments = allocate_experiments(candidate_records, variants, channel="email")
            for assignment in assignments:
                candidate = next(row for row in eligible_rows if row.person_name == assignment.candidate_name)
                session.add(
                    ExperimentAssignment(
                        workspace_id=workspace.id,
                        candidate_id=candidate.id,
                        hypothesis_id=approved_hypothesis.id,
                        message_variant_id=None,
                        channel=assignment.channel,
                        stage=assignment.stage,
                        cohort_key=f"{candidate.seniority}:{candidate.company_name}",
                        assignment_group=assignment.variant_label,
                        holdout=assignment.holdout,
                    )
                )
            return {"assignments_created": len(assignments)}

        assignment_rows = session.scalars(select(ExperimentAssignment).where(ExperimentAssignment.workspace_id == workspace.id)).all()
        if stage_name == "generate_messages":
            generated = 0
            for hypothesis_row in hypothesis_rows[:2]:
                hypothesis_record = type(
                    "HypothesisProxy",
                    (),
                    {
                        "title": hypothesis_row.title,
                        "statement": hypothesis_row.statement,
                        "target_problem": hypothesis_row.target_problem,
                        "recommended_proof_points": hypothesis_row.recommended_proof_points_json,
                        "recommended_cta": hypothesis_row.recommended_cta,
                        "counterargument": hypothesis_row.score_card_json.get("counterargument", ""),
                    },
                )()
                variants_to_store = generate_initial_variants(hypothesis_record, context, channel="email")
                try:
                    variants_to_store = llm_generate_message_variants(self.llm_client, hypothesis_record, "email", variants_to_store)
                except (LLMNotConfiguredError, Exception):
                    pass
                for variant in variants_to_store:
                    from oh_my_gtm.models import MessageVariant

                    session.add(
                        MessageVariant(
                            workspace_id=workspace.id,
                            hypothesis_id=hypothesis_row.id,
                            channel=variant.channel,
                            stage=variant.stage,
                            variant_label=variant.variant_label,
                            objective="reply",
                            opener_text=variant.opener_text,
                            body_text=variant.body_text,
                            cta_text=variant.cta_text,
                            proof_points_used_json=variant.proof_points_used,
                            prohibited_claim_check="pass" if not any("forbidden" in flag for flag in variant.risk_flags) else "fail",
                            readability_score=variant.quality_score,
                            personalization_mode="light",
                            metadata_json={"risk_flags": variant.risk_flags},
                        )
                    )
                    generated += 1
            return {"message_variants_created": generated}

        message_rows = session.execute(
            select(Hypothesis.id, Hypothesis.title, CandidateTarget.person_name, CandidateTarget.company_name, CandidateTarget.priority_score, CandidateTarget.seniority)
            .join(ExperimentAssignment, ExperimentAssignment.hypothesis_id == Hypothesis.id)
            .join(CandidateTarget, CandidateTarget.id == ExperimentAssignment.candidate_id)
            .where(Hypothesis.workspace_id == workspace.id)
        ).all()

        if stage_name == "execute_outbound":
            assignments = [
                type(
                    "AssignmentProxy",
                    (),
                    {
                        "candidate_name": row.person_name,
                        "company_name": row.company_name,
                        "variant_label": "A",
                        "channel": "email",
                        "stage": "first_touch",
                        "holdout": False,
                    },
                )()
                for row in message_rows[: min(len(message_rows), self.settings.max_daily_email_sends)]
            ]
            variants = generate_initial_variants(
                type(
                    "HypothesisProxy",
                    (),
                    {
                        "statement": hypothesis_rows[0].statement if hypothesis_rows else "Helpful GTM automation",
                        "target_problem": hypothesis_rows[0].target_problem if hypothesis_rows else "manual work",
                        "recommended_proof_points": hypothesis_rows[0].recommended_proof_points_json if hypothesis_rows else ["fast setup"],
                        "recommended_cta": context.messaging_constraints.demo_cta_text,
                    },
                )(),
                context,
                channel="email",
            )
            candidates_by_name = {
                row.person_name: type(
                    "CandidateProxy",
                    (),
                    {
                        "person_name": row.person_name,
                        "linkedin_url": row.linkedin_url,
                        "company_name": row.company_name,
                        "qualification_status": "Tier B",
                        "exclusion_reason": None,
                        "policy_risk_score": 10,
                        "evidence_snippet": row.evidence_snippet,
                    },
                )()
                for row in candidate_rows
            }
            email_results = execute_assignments(
                candidates_by_name,
                assignments,
                variants,
                channel="email",
                dry_run=dry_run,
                auto_send=context.messaging_constraints.email_mode == "auto_send",
            )
            linkedin_assignments = [
                type(
                    "AssignmentProxy",
                    (),
                    {
                        "candidate_name": row.person_name,
                        "company_name": row.company_name,
                        "variant_label": "A",
                        "channel": "linkedin",
                        "stage": "first_touch",
                        "holdout": False,
                        "details": {},
                    },
                )()
                for row in candidate_rows[: self.settings.max_daily_linkedin_preps]
                if row.qualification_status in {"Tier A", "Tier B"}
            ]
            linkedin_variants = generate_initial_variants(
                type(
                    "HypothesisProxy",
                    (),
                    {
                        "statement": hypothesis_rows[0].statement if hypothesis_rows else "Helpful GTM automation",
                        "target_problem": hypothesis_rows[0].target_problem if hypothesis_rows else "manual work",
                        "recommended_proof_points": hypothesis_rows[0].recommended_proof_points_json if hypothesis_rows else ["fast setup"],
                        "recommended_cta": context.messaging_constraints.demo_cta_text,
                        "counterargument": hypothesis_rows[0].score_card_json.get("counterargument", "") if hypothesis_rows else "",
                    },
                )(),
                context,
                channel="linkedin",
            )
            linkedin_results = execute_assignments(
                candidates_by_name,
                linkedin_assignments,
                linkedin_variants,
                channel="linkedin",
                dry_run=True,
                auto_send=False,
                linkedin_mode=context.messaging_constraints.linkedin_mode,
            )
            results = email_results + linkedin_results
            for result in results:
                candidate = next(row for row in candidate_rows if row.person_name == result.candidate_name)
                session.add(
                    OutboundAction(
                        workspace_id=workspace.id,
                        candidate_id=candidate.id,
                        message_variant_id=None,
                        provider=result.provider,
                        stage=result.stage,
                        mode="dry_run" if dry_run else "auto_send",
                        scheduled_at=datetime.utcnow(),
                        sent_at=None if result.outcome == "queued" else datetime.utcnow(),
                        outcome=result.outcome,
                        retry_count=0,
                        dry_run=dry_run,
                        requires_human_approval=result.requires_human_approval,
                        details_json=result.details,
                    )
                )
            return {
                "outbound_actions_created": len(results),
                "email_actions_created": len(email_results),
                "linkedin_actions_prepared": len(linkedin_results),
            }

        action_rows = session.scalars(select(OutboundAction).where(OutboundAction.workspace_id == workspace.id)).all()
        if stage_name == "ingest_responses":
            if not action_rows:
                return {"classified_responses": 0}
            classifications = []
            synthetic_texts = [
                "Interesting. Can you send a couple times next week?",
                "We already have something in place, so timing is not great.",
            ]
            for index, text in enumerate(synthetic_texts[: max(1, min(2, len(action_rows)))]):
                classification = classify_reply(text)
                if classification.confidence < 0.9:
                    try:
                        classification = llm_classify_reply(self.llm_client, text, classification)
                    except (LLMNotConfiguredError, Exception):
                        pass
                action = action_rows[index]
                session.add(
                    ResponseClassification(
                        workspace_id=workspace.id,
                        response_id=str(uuid4()),
                        label=classification.label,
                        sentiment=classification.sentiment,
                        urgency=classification.urgency,
                        objection_type=classification.objection_type,
                        next_step_requested=classification.next_step_requested,
                        confidence=classification.confidence,
                        evidence_snippet=classification.evidence_snippet,
                        details_json={},
                    )
                )
                classifications.append(classification)
            return {"classified_responses": len(classifications)}

        classification_rows = session.scalars(
            select(ResponseClassification).where(ResponseClassification.workspace_id == workspace.id)
        ).all()
        classifications = [
            classify_reply(row.evidence_snippet)
            if not row.label
            else type(
                "ClassificationProxy",
                (),
                {
                    "label": row.label,
                    "sentiment": row.sentiment,
                    "urgency": row.urgency,
                    "objection_type": row.objection_type,
                    "next_step_requested": row.next_step_requested,
                    "confidence": row.confidence,
                    "evidence_snippet": row.evidence_snippet,
                },
            )()
            for row in classification_rows
        ]
        execution_results = [
            type(
                "ExecutionProxy",
                (),
                {
                    "candidate_name": next((candidate.person_name for candidate in candidate_rows if candidate.id == action.candidate_id), "Unknown"),
                    "provider": action.provider,
                    "channel": "email",
                    "stage": action.stage,
                    "outcome": action.outcome,
                    "details": action.details_json,
                },
            )()
            for action in action_rows
        ]

        if stage_name == "compute_metrics":
            metrics = compute_metrics(execution_results, classifications)
            for metric in metrics:
                session.add(
                    MetricSnapshot(
                        workspace_id=workspace.id,
                        metric_name=metric.metric_name,
                        time_window="all_time",
                        slice_key="all",
                        value=metric.value,
                        details_json=metric.details,
                    )
                )
            return {"metrics_created": len(metrics)}

        if stage_name == "optimize_strategy":
            variant_performance = compute_variant_uplift(
                execution_results,
                {result.candidate_name: classifications[index] for index, result in enumerate(execution_results[: len(classifications)])},
            )
            hypothesis_records = [
                type(
                    "HypothesisProxy",
                    (),
                    {
                        "title": row.title,
                        "statement": row.statement,
                        "target_problem": row.target_problem,
                        "recommended_proof_points": row.recommended_proof_points_json,
                        "recommended_cta": row.recommended_cta,
                        "counterargument": row.score_card_json.get("counterargument", ""),
                    },
                )()
                for row in hypothesis_rows
            ]
            decisions = optimize_hypotheses(hypothesis_records, variant_performance, classifications)
            for decision in decisions:
                session.add(
                    OptimizationDecision(
                        workspace_id=workspace.id,
                        decision_type=decision.decision_type,
                        subject_type=decision.subject_type,
                        subject_id=decision.subject_id[:36],
                        reason=decision.reason,
                        recommendation_json=decision.recommendation,
                    )
                )
            return {"decisions_created": len(decisions)}

        return {"status": "skipped", "plan_keys": list(plan.keys()) if isinstance(plan, dict) else []}


def describe_workflow_run(session: Session, workflow_id: str) -> WorkflowRunResponse:
    workflow = session.get(WorkflowRun, workflow_id)
    if workflow is None:
        raise ValueError(f"Workflow run {workflow_id} not found.")
    stages = session.scalars(
        select(WorkflowStageRun).where(WorkflowStageRun.workflow_run_id == workflow.id).order_by(WorkflowStageRun.started_at.asc())
    ).all()
    return WorkflowRunResponse(
        workflow_run_id=workflow.id,
        workspace_id=workflow.workspace_id,
        status=workflow.status,
        current_stage=workflow.current_stage,
        stages=[WorkflowStageSummary(stage_name=stage.stage_name, status=stage.status, details=stage.details_json) for stage in stages],
        created_at=workflow.created_at,
    )
