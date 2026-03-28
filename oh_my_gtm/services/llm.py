"""Actual LLM integration using the OpenAI Responses API with safe fallbacks."""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from oh_my_gtm.config import AppSettings
from oh_my_gtm.schemas import CandidateRecord, EnrichmentResult, HypothesisRecord, LLMRequest, LLMResponse, MessageVariantRecord, NormalizedContext, ResponseClassificationResult


class LLMNotConfiguredError(RuntimeError):
    """Raised when an actual LLM call is requested without credentials."""


@dataclass
class OpenAIResponsesClient:
    settings: AppSettings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.llm_enabled and self.settings.openai_api_key)

    def generate(self, request: LLMRequest) -> LLMResponse:
        if not self.enabled:
            raise LLMNotConfiguredError("OpenAI API key is not configured.")
        payload = {
            "model": self.settings.openai_model,
            "instructions": request.system_prompt,
            "input": request.user_prompt,
            "text": {"format": {"type": "text"}},
        }
        response = httpx.post(
            f"{self.settings.openai_base_url.rstrip('/')}/responses",
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        parts = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    parts.append(content.get("text", ""))
        content = "\n".join(parts).strip()
        parsed_json = None
        if request.response_format == "json":
            parsed_json = json.loads(content)
        return LLMResponse(content=content, parsed_json=parsed_json, model=self.settings.openai_model, provider="openai_responses")


def _to_payload(obj) -> dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return {key: value for key, value in vars(obj).items() if not key.startswith("_")}
    return dict(obj)


def llm_enrich_candidate(
    client: OpenAIResponsesClient,
    candidate: CandidateRecord,
    normalized: NormalizedContext,
    heuristic: EnrichmentResult,
) -> EnrichmentResult:
    schema = {
        "role_category": "string",
        "likely_pain_points": ["string"],
        "company_size_bucket": "string",
        "industry": "string",
        "growth_stage": "string",
        "tooling_maturity": "string",
        "buying_authority": "string",
        "confidence": {"role_category": 0.0},
        "evidence": ["string"],
    }
    request = LLMRequest(
        system_prompt="You enrich B2B outbound candidate records. Return JSON only.",
        user_prompt=json.dumps(
            {
                "candidate": _to_payload(candidate),
                "normalized_context": normalized.model_dump(),
                "heuristic_enrichment": heuristic.model_dump(),
                "required_schema": schema,
            }
        ),
        response_format="json",
    )
    response = client.generate(request)
    return EnrichmentResult.model_validate(response.parsed_json)


def llm_generate_hypotheses(
    client: OpenAIResponsesClient,
    cluster_payload: dict,
    normalized: NormalizedContext,
    existing: list[HypothesisRecord],
) -> list[HypothesisRecord]:
    request = LLMRequest(
        system_prompt="Generate 5 cluster-level B2B outbound hypotheses as strict JSON array under key hypotheses.",
        user_prompt=json.dumps(
            {
                "cluster": cluster_payload,
                "normalized_context": normalized.model_dump(),
                "existing_hypotheses": [item.model_dump() for item in existing],
            }
        ),
        response_format="json",
    )
    response = client.generate(request)
    items = response.parsed_json.get("hypotheses", [])
    return [HypothesisRecord.model_validate(item) for item in items]


def llm_generate_message_variants(
    client: OpenAIResponsesClient,
    hypothesis: HypothesisRecord,
    channel: str,
    existing: list[MessageVariantRecord],
) -> list[MessageVariantRecord]:
    request = LLMRequest(
        system_prompt="Generate message variants for B2B outbound. Return JSON array under key variants.",
        user_prompt=json.dumps(
            {
                "hypothesis": _to_payload(hypothesis),
                "channel": channel,
                "existing_variants": [_to_payload(item) for item in existing],
            }
        ),
        response_format="json",
    )
    response = client.generate(request)
    return [MessageVariantRecord.model_validate(item) for item in response.parsed_json.get("variants", [])]


def llm_classify_reply(
    client: OpenAIResponsesClient,
    message_text: str,
    heuristic: ResponseClassificationResult,
) -> ResponseClassificationResult:
    request = LLMRequest(
        system_prompt="Classify the inbound B2B outreach reply. Return JSON only.",
        user_prompt=json.dumps({"message_text": message_text, "heuristic": heuristic.model_dump()}),
        response_format="json",
    )
    response = client.generate(request)
    return ResponseClassificationResult.model_validate(response.parsed_json)
