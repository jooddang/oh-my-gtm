"""Lead extraction, enrichment, exclusions, clusters, and hypotheses."""

from __future__ import annotations

from collections import defaultdict
from itertools import cycle

from oh_my_gtm.schemas import CandidateRecord, ClusterRecord, EnrichmentResult, ExclusionRules, GTMContextInput, HypothesisRecord, NormalizedContext, ResearchItem, ScoredResearchItem
from oh_my_gtm.services.linkedin_agent import default_linkedin_url


def _infer_seniority(title: str) -> str:
    lower = title.lower()
    if any(token in lower for token in ["chief", "head", "vp", "director", "founder"]):
        return "executive"
    if any(token in lower for token in ["manager", "lead", "principal"]):
        return "manager"
    return "operator"


def _infer_department(title: str) -> str:
    lower = title.lower()
    if "rev" in lower or "sales" in lower:
        return "revenue"
    if "growth" in lower or "marketing" in lower:
        return "growth"
    if "security" in lower:
        return "security"
    return "operations"


def _infer_signal(item: ResearchItem) -> str:
    text = f"{item.title} {item.text_excerpt}".lower()
    if "hiring" in text:
        return "hiring_signal"
    if "replace" in text or "migration" in text:
        return "migration_signal"
    if item.matched_competitors:
        return "competitor_mention"
    return "pain_point_signal"


def extract_candidates(scored_items: list[ScoredResearchItem]) -> list[CandidateRecord]:
    """Extract and deduplicate candidate targets from research items."""

    candidates: dict[tuple[str, str], CandidateRecord] = {}
    for scored in scored_items:
        item = scored.item
        seed_people = [
            {
                "name": item.author_name,
                "title": "Head of RevOps" if "rev" in item.title.lower() else "VP Growth",
                "company": item.company_name,
            },
            *item.engagers,
        ]
        for person in seed_people:
            key = (person["name"].strip().lower(), person.get("company", "").strip().lower())
            if key not in candidates:
                title = person.get("title", "")
                seniority = _infer_seniority(title)
                department = _infer_department(title)
                candidates[key] = CandidateRecord(
                    person_name=person["name"],
                    linkedin_url=default_linkedin_url(person["name"]),
                    company_name=person.get("company", ""),
                    title=title,
                    seniority=seniority,
                    department=department,
                    location="United States",
                    source_type=item.source_type,
                    source_url=item.url,
                    evidence_snippet=item.text_excerpt[:220],
                    matched_keywords=item.matched_keywords,
                    matched_competitors=item.matched_competitors,
                    recent_signals=[_infer_signal(item), item.engagement_type],
                )
            else:
                existing = candidates[key]
                existing.matched_keywords = sorted(set(existing.matched_keywords + item.matched_keywords))
                existing.recent_signals = sorted(set(existing.recent_signals + [_infer_signal(item)]))
    return list(candidates.values())


def enrich_candidate(candidate: CandidateRecord, normalized: NormalizedContext) -> EnrichmentResult:
    """Heuristic enrichment with explicit evidence and confidences."""

    role_category = candidate.department or "operations"
    likely_pain_points = [pain for pain in normalized.pain_points if pain.split()[0].lower() in candidate.evidence_snippet.lower()]
    if not likely_pain_points:
        likely_pain_points = normalized.pain_points[:2]
    company_size_bucket = "mid-market" if candidate.seniority in {"executive", "manager"} else "smb"
    industry = "B2B SaaS"
    growth_stage = "Series A/B" if any(signal == "hiring_signal" for signal in candidate.recent_signals) else "seed-to-series-a"
    tooling_maturity = "fragmented" if any(signal == "competitor_mention" for signal in candidate.recent_signals) else "emerging"
    buying_authority = "high" if candidate.seniority == "executive" else "medium" if candidate.seniority == "manager" else "low"
    confidence = {
        "role_category": 0.8,
        "likely_pain_points": 0.74,
        "company_size_bucket": 0.67,
        "buying_authority": 0.79,
    }
    evidence = [
        candidate.evidence_snippet,
        f"title={candidate.title}",
        f"signals={','.join(candidate.recent_signals)}",
    ]
    return EnrichmentResult(
        role_category=role_category,
        likely_pain_points=likely_pain_points,
        company_size_bucket=company_size_bucket,
        industry=industry,
        growth_stage=growth_stage,
        tooling_maturity=tooling_maturity,
        buying_authority=buying_authority,
        confidence=confidence,
        evidence=evidence,
    )


def score_candidate(
    candidate: CandidateRecord,
    enrichment: EnrichmentResult,
    normalized: NormalizedContext,
) -> CandidateRecord:
    """Apply fit, intent, quality, and policy scoring."""

    persona_match = 30 if any(persona.lower().split()[0] in candidate.title.lower() for persona in normalized.buyer_personas) else 15
    geography_match = 10 if candidate.location in normalized.geographies else 6
    seniority_match = 10 if candidate.seniority in normalized.target_seniority else 7
    company_match = 18 if enrichment.company_size_bucket in {"mid-market", "smb"} else 12
    environment_match = min(10, 5 + len(candidate.matched_keywords))
    fit_score = float(persona_match + geography_match + seniority_match + company_match + environment_match)

    signal_strength = min(25, 8 * len(set(candidate.recent_signals)))
    engagement_depth = 15 if "author" in candidate.recent_signals else 10
    recency = 12
    why_now = 20 if any(signal in {"migration_signal", "hiring_signal", "competitor_mention"} for signal in candidate.recent_signals) else 10
    intent_score = float(signal_strength + engagement_depth + recency + why_now)

    populated_fields = sum(bool(value) for value in [candidate.person_name, candidate.company_name, candidate.title, candidate.source_url])
    data_quality_score = float(min(100, populated_fields * 20 + len(candidate.matched_keywords) * 5))
    policy_risk_score = float(5 if candidate.source_url else 50)
    candidate.fit_score = fit_score
    candidate.intent_score = intent_score
    candidate.data_quality_score = data_quality_score
    candidate.policy_risk_score = policy_risk_score
    candidate.priority_score = round((fit_score * 0.4) + (intent_score * 0.4) + (data_quality_score * 0.2) - (policy_risk_score * 0.2), 2)
    candidate.qualification_status = classify_tier(candidate.priority_score)
    return candidate


def classify_tier(priority_score: float) -> str:
    if priority_score >= 80:
        return "Tier A"
    if priority_score >= 60:
        return "Tier B"
    if priority_score >= 40:
        return "Tier C"
    return "Reject"


def evaluate_exclusions(candidate: CandidateRecord, rules: ExclusionRules, competitors: list[str]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    title = candidate.title.lower()
    company = candidate.company_name.lower()
    if any(token in title for token in ["student", "intern", "recruiter"]):
        reasons.append("title_blocked")
    if any(competitor.lower() in company for competitor in competitors):
        reasons.append("competitor_employee")
    for rule in rules.rules:
        if rule.rule_type == "keyword_pattern":
            if any(keyword.lower() in title or keyword.lower() in company for keyword in rule.config.get("keywords", [])):
                reasons.append(rule.name)
        if rule.rule_type == "geography" and rule.config.get("exclude") == candidate.location:
            reasons.append(rule.name)
    return bool(reasons), reasons


def cluster_candidates(candidates: list[CandidateRecord]) -> list[ClusterRecord]:
    grouped: dict[tuple[str, str, str, str], list[CandidateRecord]] = defaultdict(list)
    for candidate in candidates:
        primary_signal = candidate.recent_signals[0] if candidate.recent_signals else "pain_point_signal"
        company_band = "mid-market" if candidate.seniority in {"manager", "executive"} else "smb"
        channel = "dual-channel" if candidate.seniority == "executive" else "email-first"
        key = (candidate.department or "operations", primary_signal, company_band, channel)
        grouped[key].append(candidate)

    clusters = []
    for (persona, signal, company_band, channel), members in grouped.items():
        cluster_name = f"{persona.title()} + {signal.replace('_', ' ')} + {company_band}"
        clusters.append(
            ClusterRecord(
                cluster_key="|".join([persona, signal, company_band, channel]),
                cluster_name=cluster_name,
                lead_count=len(members),
                primary_persona=persona,
                primary_signal=signal,
                why_now_type=signal,
                company_band=company_band,
                recommended_channel_mix=channel,
                sample_evidence=[member.evidence_snippet for member in members[:3]],
            )
        )
    return sorted(clusters, key=lambda cluster: cluster.lead_count, reverse=True)


def generate_hypotheses(
    cluster: ClusterRecord,
    normalized: NormalizedContext,
    context: GTMContextInput,
) -> list[HypothesisRecord]:
    """Generate five cluster-level hypotheses with counterarguments."""

    base_problem = normalized.pain_points[0]
    proof_points = context.company_profile.proof_points[:2] or ["fast setup", "safer automation"]
    templates = [
        ("competitor replacement", "are comparing tools and may respond to consolidation framing", "migration friction"),
        ("manual follow-up relief", "are feeling the cost of slow follow-up and will respond to speed-to-action proof", "manual follow-up"),
        ("visibility gap", "need clearer pipeline visibility after rising complexity", "poor visibility"),
        ("experimentation velocity", "want a faster way to test outbound angles without adding headcount", "slow experimentation"),
        ("policy-safe execution", "care about compliance-safe outreach more than raw send volume", "compliance friction"),
    ]
    hypotheses = []
    proof_cycle = cycle(proof_points or ["faster experiments"])
    for label, reason_tail, problem in templates:
        proof = next(proof_cycle)
        confidence = 0.74 if cluster.lead_count >= 3 else 0.61
        hypotheses.append(
            HypothesisRecord(
                title=f"{cluster.cluster_name} {label} hypothesis",
                statement=(
                    f"{cluster.primary_persona.title()} buyers in this cluster likely {reason_tail}, "
                    f"so an outreach angle centered on {problem} should outperform generic demos."
                ),
                target_problem=problem or base_problem,
                why_now_reason=f"Signals show {cluster.primary_signal} activity and recent operational change.",
                supporting_signals=[cluster.primary_signal, cluster.company_band],
                recommended_proof_points=[proof],
                recommended_channel=cluster.recommended_channel_mix,
                recommended_cta=context.messaging_constraints.demo_cta_text,
                disqualifiers=["student", "agency", "competitor_employee"],
                confidence_score=confidence,
                counterargument="The signal may reflect casual discussion rather than active buying intent.",
                invalidation_evidence="Repeated no-reply after balanced variant exposure or explicit disinterest.",
            )
        )
    return hypotheses


def rank_hypotheses(hypotheses: list[HypothesisRecord]) -> list[HypothesisRecord]:
    def score(record: HypothesisRecord) -> float:
        evidence_bonus = len(record.supporting_signals) * 0.05
        actionability_penalty = 0.12 if "generic" in record.statement.lower() else 0.0
        return record.confidence_score + evidence_bonus - actionability_penalty

    return sorted(hypotheses, key=score, reverse=True)
