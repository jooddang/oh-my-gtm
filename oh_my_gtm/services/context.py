"""Context intake and normalization logic."""

from __future__ import annotations

import re
from collections import OrderedDict
from copy import deepcopy
from typing import Any

from oh_my_gtm.schemas import AssumptionItem, GTMContextInput, NormalizedContext

ROLE_KEYWORDS = OrderedDict(
    {
        "RevOps Leader": ["revops", "revenue operations", "pipeline", "sales ops"],
        "Growth Leader": ["growth", "demand gen", "performance marketing", "growth ops"],
        "Founder": ["founder", "cofounder", "startup"],
        "Security Leader": ["security", "compliance", "soc 2", "risk"],
        "Sales Leader": ["sales", "sdr", "bdr", "account executive"],
    }
)

CATEGORY_KEYWORDS = OrderedDict(
    {
        "gtm-automation": ["outbound", "prospecting", "gtm", "pipeline", "sales automation"],
        "revops": ["revops", "revenue operations", "crm", "forecast"],
        "security": ["security", "compliance", "risk"],
        "developer-tooling": ["developer", "engineering", "api", "developer workflow"],
    }
)

PAIN_KEYWORDS = OrderedDict(
    {
        "manual follow-up": ["manual follow-up", "manual", "slow follow-up", "follow up"],
        "tool sprawl": ["tool sprawl", "too many tools", "fragmented", "sprawl"],
        "poor visibility": ["visibility", "reporting", "blind spot", "forecast"],
        "slow experimentation": ["experiment", "testing", "iteration", "learn quickly"],
        "compliance friction": ["compliance", "audit", "privacy", "risk"],
    }
)

SENIORITY_KEYWORDS = OrderedDict(
    {
        "executive": ["vp", "head", "chief", "founder", "director"],
        "manager": ["manager", "lead", "principal"],
        "operator": ["specialist", "analyst", "coordinator"],
    }
)


def _tokenize(*parts: str) -> str:
    return " ".join(part.strip().lower() for part in parts if part).strip()


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = item.strip()
        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            ordered.append(normalized)
    return ordered


def _infer_from_keywords(text: str, mapping: OrderedDict[str, list[str]]) -> list[str]:
    matches = []
    for label, keywords in mapping.items():
        if any(keyword in text for keyword in keywords):
            matches.append(label)
    return matches


def merge_context(existing: GTMContextInput | None, patch: dict[str, Any]) -> GTMContextInput:
    base = existing.model_dump() if existing else {}
    for key, value in patch.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged = deepcopy(base[key])
            merged.update(value)
            base[key] = merged
        else:
            base[key] = value
    return GTMContextInput.model_validate(base)


def normalize_context(context: GTMContextInput) -> tuple[NormalizedContext, list[AssumptionItem], list[str]]:
    """Normalize raw business context into a research-ready shape."""

    assumptions: list[AssumptionItem] = []
    text_blob = _tokenize(
        context.company_profile.one_line_pitch,
        context.company_profile.product_description,
        " ".join(context.problem_keywords),
        " ".join(context.product_profile.pain_points),
    )

    product_category = context.product_profile.category
    if not product_category:
        inferred = _infer_from_keywords(text_blob, CATEGORY_KEYWORDS)
        product_category = inferred[0] if inferred else "gtm-automation"
        assumptions.append(
            AssumptionItem(
                field_name="product_category",
                inferred_value=product_category,
                confidence=0.72 if inferred else 0.45,
                rationale="Derived from product description and pitch keywords.",
            )
        )

    buyer_personas = _dedupe(context.icp_profile.target_personas)
    if not buyer_personas:
        inferred = _infer_from_keywords(text_blob, ROLE_KEYWORDS) or ["RevOps Leader", "Growth Leader"]
        buyer_personas = inferred[:2]
        assumptions.append(
            AssumptionItem(
                field_name="buyer_personas",
                inferred_value=buyer_personas,
                confidence=0.71,
                rationale="Inferred from role keywords in the pitch and problem statements.",
            )
        )

    pain_points = _dedupe(context.problem_keywords + context.product_profile.pain_points)
    if not pain_points:
        pain_points = _infer_from_keywords(text_blob, PAIN_KEYWORDS) or ["manual follow-up", "poor visibility"]
        assumptions.append(
            AssumptionItem(
                field_name="pain_points",
                inferred_value=pain_points,
                confidence=0.68,
                rationale="Inferred from problem and workflow language in the source context.",
            )
        )

    value_props = _dedupe(context.product_profile.value_props)
    if not value_props:
        candidate_props = re.split(r"[.;\n]", context.company_profile.one_line_pitch or "")
        value_props = _dedupe([prop.strip() for prop in candidate_props if prop.strip()])[:3]
        if not value_props:
            value_props = ["reduces manual GTM work", "improves experiment velocity"]
        assumptions.append(
            AssumptionItem(
                field_name="value_props",
                inferred_value=value_props,
                confidence=0.61,
                rationale="Collapsed the one-line pitch into reusable value propositions.",
            )
        )

    differentiation = _dedupe(context.product_profile.differentiation + context.company_profile.approved_claims)
    if not differentiation:
        differentiation = ["policy-aware automation", "closed-loop learning"]
        assumptions.append(
            AssumptionItem(
                field_name="differentiation",
                inferred_value=differentiation,
                confidence=0.56,
                rationale="No explicit differentiation was supplied, so platform-safe autonomy was used as the default.",
            )
        )

    geographies = _dedupe(context.icp_profile.geographies)
    if not geographies:
        geographies = ["United States"]
        assumptions.append(
            AssumptionItem(
                field_name="geographies",
                inferred_value=geographies,
                confidence=0.88,
                rationale="The product brief is explicitly US-focused.",
            )
        )

    target_seniority = _dedupe(context.icp_profile.target_seniority)
    if not target_seniority:
        inferred = _infer_from_keywords(" ".join(buyer_personas).lower(), SENIORITY_KEYWORDS) or ["executive", "manager"]
        target_seniority = inferred
        assumptions.append(
            AssumptionItem(
                field_name="target_seniority",
                inferred_value=target_seniority,
                confidence=0.63,
                rationale="Mapped target personas to default B2B buying seniority bands.",
            )
        )

    excluded_personas = []
    for rule in context.exclusion_rules.rules:
        keywords = rule.config.get("keywords", [])
        excluded_personas.extend(keyword for keyword in keywords if keyword)
    excluded_personas = _dedupe(excluded_personas)

    unresolved = []
    if not context.company_profile.proof_points:
        unresolved.append("proof_points")
    if not context.company_profile.booking_link:
        unresolved.append("booking_link")

    missing_fields = list_missing_fields(context, pain_points, buyer_personas, product_category)
    normalized = NormalizedContext(
        product_category=product_category,
        buyer_personas=buyer_personas,
        pain_points=pain_points,
        value_props=value_props,
        differentiation=differentiation,
        geographies=geographies,
        target_seniority=target_seniority,
        excluded_personas=excluded_personas,
        competitor_names=_dedupe(context.competitor_names),
        adjacent_tools=_dedupe(context.product_profile.adjacent_tools),
        readiness_to_research=len([field for field in missing_fields if field not in {"proof_points", "booking_link"}]) == 0,
        unresolved_questions=unresolved,
    )
    return normalized, assumptions, missing_fields


def list_missing_fields(
    context: GTMContextInput,
    pain_points: list[str] | None = None,
    buyer_personas: list[str] | None = None,
    product_category: str | None = None,
) -> list[str]:
    """Return the high-signal fields still missing for autonomous execution."""

    missing = []
    if not context.company_profile.product_name:
        missing.append("company_profile.product_name")
    if not context.company_profile.one_line_pitch:
        missing.append("company_profile.one_line_pitch")
    if not (buyer_personas or context.icp_profile.target_personas):
        missing.append("icp_profile.target_personas")
    if not (pain_points or context.problem_keywords or context.product_profile.pain_points):
        missing.append("problem_keywords")
    if not (product_category or context.product_profile.category):
        missing.append("product_profile.category")
    if not context.icp_profile.geographies:
        missing.append("icp_profile.geographies")
    if not context.messaging_constraints.demo_cta_text:
        missing.append("messaging_constraints.demo_cta_text")
    if not context.company_profile.proof_points:
        missing.append("company_profile.proof_points")
    return missing
