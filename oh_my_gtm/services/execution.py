"""Outbound execution layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from oh_my_gtm.schemas import AssignmentRecord, CandidateRecord, MessageVariantRecord
from oh_my_gtm.services.guardrails import validate_automation_plan
from oh_my_gtm.services.linkedin_agent import build_linkedin_agent_plan


@dataclass
class ExecutionResult:
    candidate_name: str
    provider: str
    channel: str
    stage: str
    outcome: str
    requires_human_approval: bool
    details: dict


class Provider:
    name = "provider"

    def send(self, assignment: AssignmentRecord, variant: MessageVariantRecord, dry_run: bool) -> ExecutionResult:
        outcome = "queued" if dry_run else "sent"
        return ExecutionResult(
            candidate_name=assignment.candidate_name,
            provider=self.name,
            channel=assignment.channel,
            stage=assignment.stage,
            outcome=outcome,
            requires_human_approval=False,
            details={"variant_label": assignment.variant_label, "timestamp": datetime.utcnow().isoformat()},
        )


class EmailProvider(Provider):
    name = "email"


class CRMTaskProvider(Provider):
    name = "crm_task"


class ManualBrowserProvider(Provider):
    name = "user_approved_browser"

    def send(self, assignment: AssignmentRecord, variant: MessageVariantRecord, dry_run: bool) -> ExecutionResult:
        candidate = assignment.details["candidate"]
        plan = build_linkedin_agent_plan(candidate, variant, mode="compliance_manual")
        return ExecutionResult(
            candidate_name=assignment.candidate_name,
            provider=self.name,
            channel=assignment.channel,
            stage=assignment.stage,
            outcome="prepared",
            requires_human_approval=True,
            details={
                "variant_label": assignment.variant_label,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_plan": plan.model_dump(),
            },
        )


class LinkedInCopilotProvider(Provider):
    name = "linkedin_copilot"

    def send(self, assignment: AssignmentRecord, variant: MessageVariantRecord, dry_run: bool) -> ExecutionResult:
        candidate = assignment.details["candidate"]
        plan = build_linkedin_agent_plan(candidate, variant, mode="assisted_semi_auto")
        return ExecutionResult(
            candidate_name=assignment.candidate_name,
            provider=self.name,
            channel=assignment.channel,
            stage=assignment.stage,
            outcome="prepared",
            requires_human_approval=True,
            details={
                "variant_label": assignment.variant_label,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_plan": plan.model_dump(),
            },
        )


class LinkedInApiOnlyProvider(Provider):
    name = "linkedin_api_only"

    def send(self, assignment: AssignmentRecord, variant: MessageVariantRecord, dry_run: bool) -> ExecutionResult:
        return ExecutionResult(
            candidate_name=assignment.candidate_name,
            provider=self.name,
            channel=assignment.channel,
            stage=assignment.stage,
            outcome="blocked",
            requires_human_approval=False,
            details={
                "variant_label": assignment.variant_label,
                "timestamp": datetime.utcnow().isoformat(),
                "blocking": ["linkedin_api_not_configured"],
            },
        )


def execute_assignments(
    candidates_by_name: dict[str, CandidateRecord],
    assignments: list[AssignmentRecord],
    variants: list[MessageVariantRecord],
    *,
    channel: str,
    dry_run: bool,
    auto_send: bool,
    linkedin_mode: str = "compliance_manual",
    prior_attempts: dict[str, int] | None = None,
    opted_out_names: set[str] | None = None,
) -> list[ExecutionResult]:
    prior_attempts = prior_attempts or {}
    opted_out_names = opted_out_names or set()
    variants_by_label = {variant.variant_label: variant for variant in variants}
    provider: Provider
    if channel == "email" and auto_send:
        provider = EmailProvider()
    elif channel == "linkedin":
        if linkedin_mode == "assisted_semi_auto":
            provider = LinkedInCopilotProvider()
        elif linkedin_mode == "api_only":
            provider = LinkedInApiOnlyProvider()
        else:
            provider = ManualBrowserProvider()
    else:
        provider = CRMTaskProvider()

    results: list[ExecutionResult] = []
    for assignment in assignments:
        if assignment.holdout:
            continue
        candidate = candidates_by_name[assignment.candidate_name]
        if not hasattr(assignment, "details") or assignment.details is None:
            assignment.details = {}
        assignment.details["candidate"] = candidate
        blocking, warnings = validate_automation_plan(
            candidate,
            prior_attempts.get(candidate.person_name, 0),
            candidate.person_name in opted_out_names,
        )
        if blocking:
            results.append(
                ExecutionResult(
                    candidate_name=assignment.candidate_name,
                    provider=provider.name,
                    channel=assignment.channel,
                    stage=assignment.stage,
                    outcome="blocked",
                    requires_human_approval=False,
                    details={"blocking": blocking, "warnings": warnings},
                )
            )
            continue
        results.append(provider.send(assignment, variants_by_label[assignment.variant_label], dry_run=dry_run))
    return results
