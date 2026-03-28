"""Research connectors, planning, and ranking logic."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict

from oh_my_gtm.schemas import GTMContextInput, NormalizedContext, ResearchItem, ResearchPlanOut, ScoredResearchItem, SearchQueryPlan


class SourceConnector(ABC):
    """Abstract research source connector."""

    @abstractmethod
    def search(self, query: str, filters: dict | None = None) -> list[ResearchItem]:
        raise NotImplementedError

    @abstractmethod
    def fetch_item(self, item_id: str) -> ResearchItem | None:
        raise NotImplementedError

    @abstractmethod
    def list_comments(self, item_id: str) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def list_engagers(self, item_id: str) -> list[dict[str, str]]:
        raise NotImplementedError


class MockConnector(SourceConnector):
    """Deterministic connector used for local automation and tests."""

    source_type = "web"

    def search(self, query: str, filters: dict | None = None) -> list[ResearchItem]:
        filters = filters or {}
        query_slug = query.replace(" ", "-")[:40]
        company = filters.get("company_hint", "SignalFlow")
        role = filters.get("role_hint", "RevOps Lead")
        return [
            ResearchItem(
                source_type=self.source_type,
                external_id=f"{self.source_type}-{query_slug}-1",
                url=f"https://example.com/{query_slug}/1",
                title=f"{role} discussing {query}",
                author_name="Jordan Lee",
                company_name=company,
                text_excerpt=f"We're evaluating options because {query} keeps slowing our team down.",
                item_type="post",
                matched_keywords=query.split()[:2],
                comments=["This has become painful after our latest tool rollout."],
                engagers=[
                    {"name": "Avery Kim", "title": "Head of RevOps", "company": company},
                    {"name": "Taylor Park", "title": "Revenue Operations Manager", "company": company},
                ],
            ),
            ResearchItem(
                source_type=self.source_type,
                external_id=f"{self.source_type}-{query_slug}-2",
                url=f"https://example.com/{query_slug}/2",
                title=f"Buyer thread about {query}",
                author_name="Morgan Diaz",
                company_name=f"{company} Labs",
                text_excerpt=f"Anyone replaced their stack after running into {query} issues?",
                item_type="discussion",
                matched_keywords=query.split()[:2],
                comments=["We're hiring because demand has outgrown our process."],
                engagers=[
                    {"name": "Casey Song", "title": "VP Growth", "company": f"{company} Labs"},
                ],
            ),
        ]

    def fetch_item(self, item_id: str) -> ResearchItem | None:
        query = item_id.split("-")[1].replace("-", " ")
        return self.search(query)[0]

    def list_comments(self, item_id: str) -> list[str]:
        item = self.fetch_item(item_id)
        return item.comments if item else []

    def list_engagers(self, item_id: str) -> list[dict[str, str]]:
        item = self.fetch_item(item_id)
        return item.engagers if item else []


class LinkedInConnector(SourceConnector):
    """Policy-safe stub. It does not automate or scrape LinkedIn."""

    source_type = "linkedin_stub"

    def search(self, query: str, filters: dict | None = None) -> list[ResearchItem]:
        return []

    def fetch_item(self, item_id: str) -> ResearchItem | None:
        return None

    def list_comments(self, item_id: str) -> list[str]:
        return []

    def list_engagers(self, item_id: str) -> list[dict[str, str]]:
        return []


def create_research_plan(normalized: NormalizedContext, context: GTMContextInput) -> ResearchPlanOut:
    """Expand GTM context into prioritized research queries."""

    competitor_queries = [
        SearchQueryPlan(
            family="competitor_mentions",
            query=f'"{competitor}" customer pain revops',
            expected_precision=0.82,
            expected_recall=0.61,
            priority=0.88,
            filters={"company_hint": competitor, "role_hint": normalized.buyer_personas[0]},
        )
        for competitor in normalized.competitor_names[:5]
    ]

    pain_point_queries = [
        SearchQueryPlan(
            family="pain_point",
            query=f'"{pain}" {normalized.buyer_personas[0]} saas',
            expected_precision=0.77,
            expected_recall=0.72,
            priority=0.84,
            filters={"company_hint": context.company_profile.company_name or "SignalFlow"},
        )
        for pain in normalized.pain_points[:5]
    ]

    tool_comparison_queries = [
        SearchQueryPlan(
            family="tool_comparison",
            query=f'"{tool}" vs alternative review',
            expected_precision=0.65,
            expected_recall=0.55,
            priority=0.63,
            filters={"role_hint": normalized.buyer_personas[0]},
        )
        for tool in normalized.adjacent_tools[:4]
    ]

    hiring_signal_queries = [
        SearchQueryPlan(
            family="hiring_signal",
            query=f'"{persona}" hiring ops manager',
            expected_precision=0.58,
            expected_recall=0.67,
            priority=0.59,
            filters={"role_hint": persona},
        )
        for persona in normalized.buyer_personas[:3]
    ]

    trigger_event_terms = ["budget increase", "new head of revenue", "migration", "replatforming", "tool consolidation"]
    trigger_event_queries = [
        SearchQueryPlan(
            family="trigger_event",
            query=f'"{term}" {normalized.product_category}',
            expected_precision=0.66,
            expected_recall=0.53,
            priority=0.68,
        )
        for term in trigger_event_terms
    ]

    excluded_terms = normalized.excluded_personas + ["student", "intern", "agency"]
    return ResearchPlanOut(
        competitor_queries=competitor_queries,
        pain_point_queries=pain_point_queries,
        tool_comparison_queries=tool_comparison_queries,
        hiring_signal_queries=hiring_signal_queries,
        trigger_event_queries=trigger_event_queries,
        excluded_terms=excluded_terms,
    )


def run_mock_research(plan: ResearchPlanOut, connector: SourceConnector | None = None) -> list[ResearchItem]:
    connector = connector or MockConnector()
    gathered: dict[str, ResearchItem] = {}
    for query in plan.all_queries[:8]:
        for item in connector.search(query.query, query.filters):
            gathered[item.url] = item
    return list(gathered.values())


def score_research_items(items: list[ResearchItem], normalized: NormalizedContext) -> list[ScoredResearchItem]:
    """Score research items for ICP relevance and outreach value."""

    scored: list[ScoredResearchItem] = []
    for item in items:
        text = f"{item.title} {item.text_excerpt} {' '.join(item.comments)}".lower()
        persona_score = 25 if any(persona.lower().split()[0] in text for persona in normalized.buyer_personas) else 10
        problem_score = min(25, sum(7 for pain in normalized.pain_points if pain.lower().split()[0] in text))
        buying_signal_score = 0
        for signal in ["evaluating", "replace", "migration", "hiring", "painful", "budget"]:
            if signal in text:
                buying_signal_score += 6
        recency_score = max(5, 15 - item.recency_days)
        engagement_score = min(10, len(item.comments) * 3 + len(item.engagers) * 2)
        discussion_depth = min(10, len(item.comments) * 4)
        total = min(100, persona_score + problem_score + buying_signal_score + recency_score + engagement_score + discussion_depth)
        explanation = {
            "icp_match": persona_score,
            "problem_relevance": problem_score,
            "buying_signal_strength": min(buying_signal_score, 20),
            "recency": recency_score,
            "engagement_quality": engagement_score,
            "discussion_depth": discussion_depth,
            "expected_outreach_value": "high" if total >= 70 else "medium" if total >= 50 else "low",
        }
        scored.append(ScoredResearchItem(item=item, score=float(total), explanation=explanation))
    return sorted(scored, key=lambda entry: entry.score, reverse=True)


def summarize_query_families(plan: ResearchPlanOut) -> dict[str, int]:
    counts = defaultdict(int)
    for query in plan.all_queries:
        counts[query.family] += 1
    return dict(counts)
