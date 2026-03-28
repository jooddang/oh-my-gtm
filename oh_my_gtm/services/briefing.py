"""Turn a single operator brief into GTM context and LinkedIn search specs."""

from __future__ import annotations

import re

from oh_my_gtm.schemas import AutopilotBriefSpec, CompanyProfile, ExclusionRules, ExperimentGoals, GTMContextInput, IdealCustomerProfile, LinkedInSearchSpec, MessagingConstraints, ProductProfile


KOREAN_GLOSSARY = {
    "스테이블 코인": "stablecoin",
    "스테이블코인": "stablecoin",
    "결제": "payments",
    "인프라": "infrastructure",
    "경쟁 업체": "competitors",
    "경쟁업체": "competitors",
    "찾고": "find",
    "어프로치": "approach",
    "도와줘": "help",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "approach",
    "can",
    "find",
    "for",
    "get",
    "help",
    "i",
    "like",
    "me",
    "please",
    "that",
    "the",
    "to",
    "with",
}


def _translate_known_phrases(brief: str) -> str:
    translated = brief
    for korean, english in KOREAN_GLOSSARY.items():
        translated = translated.replace(korean, english)
    return translated


def _normalize_brief(brief: str) -> str:
    translated = _translate_known_phrases(brief)
    translated = re.sub(r"\s+", " ", translated).strip()
    return translated


def _keywordize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-/+]*", text.lower())
    seen: list[str] = []
    for token in tokens:
        if token in STOPWORDS or len(token) <= 2:
            continue
        if token not in seen:
            seen.append(token)
    return seen


def _market_label(normalized_brief: str) -> str:
    lowered = normalized_brief.lower()
    stripped = re.sub(r"\b(find|help|approach|competitors?|companies?|people)\b", " ", lowered)
    stripped = re.sub(r"\s+", " ", stripped).strip(" ,.")
    return stripped or normalized_brief


def build_autopilot_brief(brief: str) -> AutopilotBriefSpec:
    normalized = _normalize_brief(brief)
    market_label = _market_label(normalized)
    keywords = _keywordize(market_label)
    search_terms = [" ".join(keywords[:3]) or market_label]
    if "stablecoin" in normalized.lower():
        search_terms.append("stablecoin payments infrastructure")
    if "payment" in normalized.lower() or "payments" in normalized.lower():
        search_terms.append("payment infrastructure")
    search_terms = [term for term in search_terms if term]
    assumptions = [
        "Used a discovery-style outreach stance because no first-party product details were provided.",
        "Defaulted target personas to founders, partnerships, and revenue leaders for market-mapping outreach.",
    ]
    return AutopilotBriefSpec(
        original_brief=brief,
        normalized_brief=normalized,
        market_label=market_label,
        outreach_goal="Find relevant companies and people, then draft discovery outreach.",
        company_name="Operator Research Desk",
        product_name=market_label.title()[:80] or "Market Mapping",
        one_line_pitch=f"Researching {market_label} and starting discovery conversations with relevant operators.",
        target_personas=["Founder", "Head of Partnerships", "Revenue Operations Leader"],
        target_seniority=["executive", "manager"],
        geographies=["United States"],
        problem_keywords=keywords[:6] or [market_label],
        competitor_names=[],
        search_terms=search_terms[:3],
        assumptions=assumptions,
    )


def build_context_from_brief(spec: AutopilotBriefSpec) -> GTMContextInput:
    return GTMContextInput(
        company_profile=CompanyProfile(
            workspace_name=f"Autopilot - {spec.market_label[:48]}",
            company_name=spec.company_name,
            product_name=spec.product_name,
            one_line_pitch=spec.one_line_pitch,
            product_description=(
                f"Autonomous research and outbound discovery around {spec.market_label}, "
                "with LinkedIn signal collection and operator-ready email drafts."
            ),
            target_market=spec.market_label,
            proof_points=["fast market mapping", "operator-ready outreach drafts", "policy-aware workflow"],
            approved_claims=["fast market mapping", "operator-ready outreach drafts"],
            forbidden_claims=["guaranteed meetings", "guaranteed response"],
            booking_link="https://example.com/discovery",
        ),
        product_profile=ProductProfile(
            category="market-mapping",
            value_props=["finds relevant operators quickly", "turns search signals into drafts"],
            differentiation=["policy-aware browser research", "closed-loop workflow"],
            adjacent_tools=["LinkedIn", "Apollo", "Clay"],
            pain_points=spec.problem_keywords[:4] or ["manual market mapping", "slow outreach setup"],
        ),
        icp_profile=IdealCustomerProfile(
            target_personas=spec.target_personas,
            industries=["Fintech", "Payments", "B2B SaaS"],
            company_size_ranges=["11-200", "201-1000"],
            geographies=spec.geographies,
            target_seniority=spec.target_seniority,
        ),
        exclusion_rules=ExclusionRules(rules=[]),
        messaging_constraints=MessagingConstraints(
            demo_cta_text="Open to a short discovery conversation next week?",
            linkedin_mode="compliance_manual",
            email_mode="auto_send",
            human_review_required_for_high_risk_claims=True,
        ),
        experiment_goals=ExperimentGoals(),
        competitor_names=spec.competitor_names,
        problem_keywords=spec.problem_keywords,
    )


def build_linkedin_search_specs(spec: AutopilotBriefSpec, *, max_queries: int = 4, limit: int = 5) -> list[LinkedInSearchSpec]:
    people_roles = ["founder", "head of partnerships", "revenue operations"]
    queries: list[LinkedInSearchSpec] = []
    for term in spec.search_terms:
        queries.append(LinkedInSearchSpec(query=term, vertical="companies", limit=limit))
        for role in people_roles:
            queries.append(LinkedInSearchSpec(query=f"{term} {role}", vertical="people", limit=limit))
    return queries[:max_queries]
