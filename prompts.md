아래는 “AI가 자동으로 돌아가는 GTM agent”를 Codex로 구현하기 위한 프롬프트 세트다.

구성 원칙:
	•	각 프롬프트는 바로 Codex에 붙여 넣을 수 있게 작성
	•	가능한 한 사람 개입 없이 길게 돌아가도록 설계
	•	다만 LinkedIn 등 외부 플랫폼은 이용약관, rate limit, opt-out, 개인정보 처리 준수를 전제로 함
	•	stealth scraping, 탐지 회피, 계정 제재 회피 같은 방향은 제외
	•	가능하면 공식 API, 합법적 데이터 소스, 또는 사용자가 로그인한 브라우저 상의 명시적 자동화만 사용

권장 개발 방식:
	1.	먼저 “전체 아키텍처 골격”을 만든다
	2.	이후 각 flow별 worker를 분리 구현한다
	3.	마지막에 orchestration loop와 evaluation loop를 붙인다


⸻

1. Flow A - 사용자 비즈니스 컨텍스트 수집

목표:
	•	제품/서비스/ICP/금지 타겟/메시지 톤/CTA/실험 목표를 구조화
	•	질문을 너무 많이 하지 않고, 부족한 정보는 합리적으로 가정하되 assumption_log에 기록

Prompt A1 - 컨텍스트 수집 API + 스키마

Build the business-context intake module for the autonomous GTM agent.

Requirements:
- Create a FastAPI service for collecting and updating GTM context
- Define Pydantic models for:
  - CompanyProfile
  - ProductProfile
  - IdealCustomerProfile
  - ExclusionRules
  - MessagingConstraints
  - ExperimentGoals
  - AssumptionLog
- Create endpoints to:
  - create a GTM workspace
  - submit context
  - patch context
  - retrieve normalized context
  - list missing fields
- Add a normalization layer that converts messy user input into structured fields:
  - product category
  - buyer persona
  - pain points
  - value props
  - differentiation
  - geographies
  - target seniority
  - excluded personas
- Add a function that infers missing fields from partial context and stores all inferred items in assumption_log with confidence scores
- Store everything in PostgreSQL
- Include unit tests for normalization and missing-field detection

Output:
1. project tree
2. schema design
3. complete code
4. migration/model setup
5. sample requests/responses

Prompt A2 - 최소 질문으로 충분한 컨텍스트 확보하는 intake agent

Implement an intake agent that asks the minimum number of high-yield questions needed to start GTM research.

Requirements:
- The agent should maximize information gain per question
- It should stop asking questions once it has enough information to begin research
- It should ask no more than 5 questions in the first pass unless confidence remains too low
- Missing details should be inferred with explicit uncertainty tracking
- The agent should output:
  - normalized GTM context
  - unresolved questions
  - inferred assumptions with confidence
  - readiness_to_research boolean

Implement:
- question selection logic
- confidence scoring
- stop condition
- Pydantic schemas
- tests with example user inputs for vague startup descriptions

Return production-grade Python code, not pseudocode.


⸻

2. Flow B - 경쟁사/제품/주제 관련 포스트 탐색

목표:
	•	LinkedIn, 웹, 블로그, 뉴스, 회사 페이지 등에서 relevant discourse 수집
	•	키워드 확장, 경쟁사 확장, 토픽 클러스터링

주의:
	•	LinkedIn 직접 scraping은 정책 리스크가 있으므로, 공식 API/허용된 통합 또는 사용자 브라우저 수동 세션 기반 자동화로 추상화

Prompt B1 - 리서치 소스 추상화 계층

Design and implement a source-connector abstraction for GTM research.

Goal:
Search for posts, discussions, and public signals related to:
- competitors
- adjacent products
- category keywords
- pain-point keywords
- buyer-role keywords

Requirements:
- Create a connector interface that supports:
  - search(query, filters)
  - fetch_item(item_id)
  - list_comments(item_id)
  - list_engagers(item_id)
- Implement mock connectors for:
  - WebSearchConnector
  - NewsConnector
  - BlogConnector
  - LinkedInConnector as an abstract or stubbed integration layer only
- Create a query planner that expands input GTM context into:
  - competitor queries
  - problem-aware queries
  - job-title-aware queries
  - product-category queries
- Rank results by relevance to ICP and buying intent
- Store raw items and normalized items separately
- Add deduplication and canonicalization

Output:
- connector interface
- query planner
- ranking logic
- DB models
- tests

Prompt B2 - 리서치 플래너와 키워드 확장 엔진

Build a research planning engine for the GTM agent.

Input:
- normalized GTM context

Output:
- prioritized search plan containing:
  - competitor names
  - alternative product names
  - category terms
  - pain-point terms
  - trigger-event terms
  - buying-intent phrases
  - excluded terms

Requirements:
- derive search terms from product value proposition and ICP
- create multiple query families:
  1. direct competitor mentions
  2. pain-point complaints
  3. tool comparison posts
  4. hiring signals
  5. team expansion and budget signals
  6. migration / dissatisfaction signals
- score each query by expected precision and recall
- store search plans in DB
- include a refresh strategy so the agent can re-run research periodically

Implement as Python service with unit tests and example outputs.

Prompt B3 - 포스트 relevance scoring

Implement a relevance scoring pipeline for discovered posts and discussions.

Requirements:
- Score each post on:
  - ICP match
  - problem relevance
  - buying signal strength
  - recency
  - engagement quality
  - discussion depth
  - expected outreach value
- Produce both:
  - numerical score
  - structured explanation
- Add configurable weights
- Persist scores and explanations
- Add reranking function that prioritizes high-value, lower-competition opportunities

Provide complete code with schema definitions and tests.


⸻

3. Flow C - 게시자와 참여자 리스트업

목표:
	•	포스트 작성자
	•	댓글 참여자
	•	반응한 사람
	•	회사/직무 기반 enrichment

Prompt C1 - 대상 추출 파이프라인

Build the target extraction pipeline for the GTM agent.

Input:
- normalized research items such as posts, comments, authors, and participants

Output:
- candidate target records

Requirements:
- Extract:
  - author
  - commenters
  - engagers
  - mentioned companies
  - mentioned products
- Normalize entities:
  - full name
  - profile URL if available
  - company
  - title
  - seniority
  - functional area
  - geography
- Create identity resolution logic to merge duplicates
- Track provenance for every field
- Tag each candidate with:
  - source post id
  - engagement type
  - extracted signals
  - confidence score
- Save to PostgreSQL
- Add tests for entity normalization and deduplication

Deliver runnable code.

Prompt C2 - person/company enrichment

Implement an enrichment service for candidate targets.

Requirements:
- Given a candidate person or company, enrich with:
  - inferred role category
  - likely pain points
  - company size bucket
  - industry
  - growth stage
  - likely tooling maturity
  - likely buying authority
- Use heuristic rules plus pluggable LLM enrichment
- Every inferred field must include:
  - confidence score
  - evidence list
  - source type
- Keep raw data separate from inferred data
- Add caching and idempotency
- Include tests for deterministic rule-based enrichment

Return:
- schema
- service code
- tests
- example enriched records


⸻

4. Flow D - 니즈 분석 및 가설 생성

목표:
	•	포스트별 또는 세그먼트별 가설 5개 생성
	•	너무 개인 단위로 니치해지지 않게 “cluster hypothesis”를 기본값으로
	•	필요시 account-level hypothesis로 확장

Prompt D1 - 가설 생성 엔진

Build a hypothesis generation engine for GTM targeting.

Input:
- GTM context
- candidate targets
- related posts and discussions
- enrichment data

Output:
- for each target cluster, generate 5 need hypotheses

Hypothesis format:
- hypothesis_id
- cluster_id
- statement
- underlying pain
- observable evidence
- buying trigger
- why our product may fit
- counterargument
- estimated priority
- confidence score

Requirements:
- Default to cluster-level hypotheses rather than one-person-only hypotheses
- Cluster by role, company type, pain pattern, and observed discourse
- Generate at least one counter-hypothesis per cluster
- Include second-order reasoning:
  - why this may fail
  - what evidence would invalidate it
- Persist all hypotheses and link them to supporting evidence
- Add tests for clustering and hypothesis object validation

Return full implementation.

Prompt D2 - hypothesis ranking and pruning

Implement a hypothesis ranking and pruning module.

Requirements:
- Rank hypotheses by:
  - expected response rate
  - expected business value
  - confidence
  - strategic fit
  - novelty
- Penalize:
  - vague hypotheses
  - low evidence support
  - low actionability
  - high overlap with existing hypotheses
- Add pruning rules:
  - archive if repeated failure threshold reached
  - merge near-duplicate hypotheses
  - promote if multi-stage success observed
- Output explainable rankings and state transitions

Provide code, schema, and tests.


⸻

5. Flow E - 제외할 타겟 설정

예:
	•	학생
	•	경쟁사 재직자
	•	채용 담당자만 있고 buyer 아님
	•	컨설턴트/에이전시 제외
	•	특정 국가 제외

Prompt E1 - exclusion rules engine

Build an exclusion rules engine for GTM targeting.

Requirements:
- Rules should support:
  - exact match
  - keyword pattern
  - title/seniority filters
  - company blacklist
  - industry blacklist
  - geography restrictions
  - student / job seeker / competitor exclusions
  - custom user-defined predicates
- Each candidate should be evaluated with:
  - excluded boolean
  - exclusion reasons
  - rule ids matched
- Support both hard exclusion and soft penalty
- Add versioning for rules
- Persist evaluation results
- Include tests for rule evaluation

Return production-ready Python code.


⸻

6. Flow F - connect message 3종 생성 및 A/B 테스트

목표:
	•	connect 메시지 3 variants
	•	follow-up 3단계
	•	각 hypothesis에 맞는 message family 생성
	•	길이 제한, spam 방지, personalization depth 제어

Prompt F1 - connect message generator

Build a message generation service for initial connection requests.

Input:
- GTM context
- target cluster
- chosen hypothesis
- messaging constraints

Output:
- 3 distinct connection message variants

Requirements:
- Each variant should differ on one primary dimension:
  1. pain-led
  2. curiosity-led
  3. credibility-led
- Enforce strict character limits configurable per platform
- Personalization must be evidence-based only
- Avoid fabricated familiarity
- Avoid manipulative language
- Generate metadata for each message:
  - angle
  - hypothesis_id
  - expected risk
  - expected reply likelihood
- Add quality checks:
  - too generic
  - too long
  - overclaims
  - spam risk
- Persist generated variants
- Add tests for validator logic

Return code and sample outputs.

Prompt F2 - 3단계 follow-up sequence generator

Build a follow-up sequence generator for outbound GTM messaging.

Requirements:
- Generate 3 sequential follow-up messages for a given target and hypothesis
- Sequence logic:
  - Follow-up 1: light continuation
  - Follow-up 2: sharper value articulation
  - Follow-up 3: low-friction close or graceful exit
- Every step must reference prior context correctly
- Support multiple tones:
  - direct
  - consultative
  - founder-to-founder
- Add stop conditions:
  - do not continue after negative reply
  - do not continue after explicit no-interest
  - do not continue after opt-out
- Add validation rules for politeness, compliance, and concision
- Store templates and rendered messages separately

Provide full code and tests.

Prompt F3 - experiment allocator

Implement an experiment allocation service for outbound testing.

Goal:
Send 3 message variants across target cohorts and measure outcomes fairly.

Requirements:
- Randomize targets across variants while preserving balance by:
  - seniority
  - company size
  - geography
  - target cluster
- Support holdout groups
- Prevent over-contacting the same company
- Track exposure counts and sequence stage
- Output assignment records and audit logs
- Include tests for balanced allocation and collision prevention

Return complete implementation.


⸻

7. Flow G - 메시지 발송

주의:
	•	실제 발송은 플랫폼 정책 준수
	•	공식 API, CRM 연동, 이메일, 사용자 승인된 브라우저 기반 조작 등 합법적 범위 내

Prompt G1 - outbound execution layer

Build the outbound execution layer for the GTM agent.

Requirements:
- Abstract the send action behind a provider interface
- Support providers such as:
  - email
  - CRM task creation
  - user-approved browser action stub
- Do not implement stealth automation or anti-detection tactics
- Every send action must include:
  - candidate id
  - message id
  - provider
  - timestamp
  - outcome
  - retry info
- Add rate limiting
- Add dry-run mode
- Add approval mode toggle:
  - manual approval
  - policy-safe autonomous send
- Include idempotency safeguards to avoid duplicate sends
- Persist action logs and errors

Return code, models, and tests.


⸻

8. Flow H - 답변률, connect 수락률, 단계별 성과 측정

목표:
	•	acceptance rate
	•	reply rate
	•	positive reply rate
	•	meeting booked rate
	•	time-to-reply
	•	stage drop-off
	•	hypothesis별/variant별 lift

Prompt H1 - experiment analytics pipeline

Build the analytics and measurement pipeline for the GTM agent.

Metrics:
- connection acceptance rate
- initial reply rate
- positive reply rate
- negative reply rate
- meeting-booked rate
- stage-by-stage conversion
- median time to reply
- hypothesis-level performance
- message-angle performance
- cluster-level performance

Requirements:
- Create a metrics service and materialized summary tables
- Support time windows and cohort slicing
- Distinguish between:
  - sent
  - delivered
  - seen if available
  - replied
  - positive reply
  - converted
- Add uplift calculations between A/B variants
- Add significance helpers or Bayesian estimates where appropriate
- Create API endpoints for dashboard use
- Include tests for metrics correctness

Return code and DB schema.

Prompt H2 - response classifier

Implement a reply classification service for inbound responses.

Classes:
- positive_interest
- neutral_interest
- objection
- referral
- no_interest
- opt_out
- unclear

Requirements:
- Provide rule-based baseline plus pluggable LLM classifier
- Extract structured fields:
  - sentiment
  - urgency
  - objection type
  - next step requested
- Must support confidence scores and evidence snippets
- Store classification outputs
- Add tests with realistic sample inbound messages

Return production-grade code.


⸻

9. Flow I - 전략 수정 loop

목표:
	•	답변 없으면 같은 hypothesis의 다른 strategy
	•	계속 실패하면 hypothesis 폐기
	•	실패 기반 신규 hypothesis 3개 생성
	•	성공하면 원리 추출하여 다음 message prompt에 반영

Prompt I1 - closed-loop optimizer

Build the closed-loop optimization engine for the GTM agent.

Inputs:
- message performance
- hypothesis performance
- reply classifications
- conversion outcomes

Core logic:
- If no reply:
  - try another message strategy within the same hypothesis up to configured limits
- If repeated failures:
  - deprecate or archive the hypothesis
  - generate 3 replacement hypotheses informed by failure patterns
- If success:
  - extract successful principles
  - update future message-generation guidance
- If objection patterns cluster:
  - propose product-positioning adjustments

Requirements:
- Implement explicit state transitions
- Keep a full audit trail of why a hypothesis or strategy changed
- Prevent oscillation and repeated low-value experiments
- Add configurable thresholds
- Produce machine-readable recommendations and next actions

Return complete Python implementation with tests.

Prompt I2 - success principle extractor

Implement a success-principle extraction module.

Goal:
Learn from high-performing outbound sequences and turn the patterns into reusable prompting guidance.

Requirements:
- Analyze winning messages and identify:
  - opening style
  - value framing
  - personalization depth
  - CTA style
  - message length pattern
  - target segment fit
- Output a structured principle set:
  - principle statement
  - supporting examples
  - confidence
  - safe scope of application
- Save principles with versioning
- Feed them into the message generator as guidance, not hard rules
- Add tests for schema and version management

Return code and examples.


⸻

10. Flow J - 오케스트레이션

목표:
	•	research -> extract -> enrich -> hypothesize -> exclude -> generate -> send -> measure -> optimize
	•	cron 또는 event-driven loop
	•	사람 개입 최소화

Prompt J1 - autonomous orchestration engine

Build the orchestration engine for the autonomous GTM agent.

Workflow stages:
1. collect_or_refresh_context
2. create_research_plan
3. fetch_research_items
4. score_items
5. extract_targets
6. enrich_targets
7. generate_hypotheses
8. apply_exclusions
9. allocate_experiments
10. generate_messages
11. execute_outbound
12. ingest_responses
13. compute_metrics
14. optimize_strategy

Requirements:
- Implement this as a resumable job workflow
- Support retries and partial failure recovery
- Every stage should be idempotent
- Persist workflow runs and stage states
- Add kill switch and per-stage toggles
- Add max-action budgets per day
- Add audit log entries at every stage
- Provide CLI commands and API endpoints to start or inspect runs
- Include tests for workflow state transitions and retry safety

Return production-ready code.


⸻

11. Flow K - 리뷰 가능한 대시보드 / Human override

사람 개입 최소화가 목적이어도 실제 운영에서는 override 지점이 있어야 한다.

Prompt K1 - operator console backend

Build the backend for an operator console for the GTM agent.

Requirements:
- Expose APIs for:
  - reviewing candidates
  - reviewing hypotheses
  - reviewing message variants
  - approving or rejecting outbound actions
  - viewing experiment results
  - viewing optimization decisions
- Include filters and pagination
- Add audit logs for all operator actions
- Include role support:
  - admin
  - operator
  - viewer
- Provide OpenAPI docs
- Add tests for permission boundaries

Return code and API examples.


⸻

12. Flow L - 데이터 모델 설계

이건 초기에 별도로 뽑아 두는 것이 좋다.

Prompt L1 - 전체 DB schema 설계

Design the full PostgreSQL schema for the autonomous GTM agent.

Entities should include:
- workspace
- company_profile
- product_profile
- icp_profile
- exclusion_rule
- research_plan
- research_query
- research_item_raw
- research_item_normalized
- candidate_target
- company_entity
- person_entity
- enrichment_record
- target_cluster
- hypothesis
- hypothesis_evidence
- message_template
- rendered_message
- experiment_assignment
- outbound_action
- inbound_response
- response_classification
- metric_snapshot
- optimization_decision
- workflow_run
- workflow_stage_run
- audit_log
- assumption_log

Requirements:
- Include primary keys, indexes, unique constraints, and foreign keys
- Add notes on which fields should be JSONB vs relational
- Explain tradeoffs
- Generate SQLAlchemy models and migration starter files
- Include a seed script for local development

Return full code and schema explanation.


⸻

13. Flow M - 로깅, 평가, 품질 제어

Prompt M1 - structured logging and audit

Implement structured logging and audit infrastructure for the GTM agent.

Requirements:
- Every major decision and action must emit structured logs
- Use correlation ids and workflow ids
- Separate:
  - application logs
  - outbound action logs
  - optimization decision logs
  - compliance/audit logs
- Add helpers for logging hypothesis generation reasons and exclusion reasons
- Persist critical audit events to DB
- Include tests for log payload structure

Return code and usage examples.

Prompt M2 - quality guardrails

Build a quality and compliance guardrail layer for the GTM agent.

Requirements:
- Validate generated messages for:
  - unsupported claims
  - fabricated personalization
  - excessive length
  - spammy wording
  - policy violations
- Validate automation plans for:
  - duplicate contact attempts
  - over-contacting one account
  - contacting excluded personas
  - sending after opt-out
- Output blocking errors vs warnings
- Integrate guardrails before outbound execution
- Add unit tests

Return full implementation.


⸻

14. Flow N - 환경설정과 배포

Prompt N1 - local dev + deployment skeleton

Set up the project for local development and deployment.

Requirements:
- Docker Compose for:
  - app
  - postgres
  - redis if needed
- .env.example
- alembic setup
- pytest setup
- Makefile
- minimal CI workflow
- README with:
  - setup
  - migrations
  - running tests
  - starting API
  - running a workflow
- Add sample fixture data for one demo workspace

Return full project scaffolding code.


⸻

15. 실제 Codex 운용 시 권장 순서

Codex에 한 번에 너무 큰 범위를 던지면 산출물이 퍼질 수 있다. 아래 순서가 효율적이다.

1단계
	•	공통 프롬프트
	•	L1 DB schema
	•	N1 infra
	•	A1 context intake

2단계
	•	B1 connector abstraction
	•	B2 research planner
	•	B3 relevance scoring

3단계
	•	C1 target extraction
	•	C2 enrichment
	•	E1 exclusion engine

4단계
	•	D1 hypothesis generation
	•	D2 hypothesis ranking

5단계
	•	F1 connect generator
	•	F2 follow-up generator
	•	F3 experiment allocator
	•	M2 quality guardrails

6단계
	•	G1 outbound execution
	•	H1 analytics
	•	H2 response classifier

7단계
	•	I1 optimizer
	•	I2 principle extractor
	•	J1 orchestration
	•	K1 operator console backend

⸻

16. Codex가 더 잘 작동하게 하는 추가 지시문

각 작업 프롬프트 끝에 아래 문장을 붙이면 품질이 올라간다.

Important:
- Do not give me a high-level essay.
- Write the code.
- When there is ambiguity, choose a practical default and document it.
- Keep module boundaries clean.
- Make the code runnable locally.
- Include at least 3 realistic tests.
- Show sample payloads and expected outputs.


⸻

17. 메시지 생성 자체를 위한 내부 LLM 프롬프트 템플릿

이건 나중에 agent 내부에서 메시지 생성용으로 사용할 프롬프트다.

Prompt template - initial connect message

You are generating a short outbound connection request for B2B outreach.

Inputs:
- product_summary: {{product_summary}}
- target_role: {{target_role}}
- target_company_type: {{target_company_type}}
- target_cluster_pain: {{target_cluster_pain}}
- evidence_from_discussion: {{evidence_from_discussion}}
- hypothesis: {{hypothesis}}
- angle: {{angle}}  # pain_led | curiosity_led | credibility_led
- max_chars: {{max_chars}}
- tone: {{tone}}

Rules:
- Be concise
- Use only evidence-based personalization
- Do not pretend to know the person
- Do not overclaim
- Avoid generic sales phrasing
- End with a low-friction CTA or soft curiosity hook
- Must fit within max_chars

Return JSON:
{
  "message": "...",
  "rationale": "...",
  "risks": ["..."],
  "quality_score": 0-100
}

Prompt template - follow-up sequence

You are generating a follow-up outbound message in a B2B outreach sequence.

Inputs:
- original_message: {{original_message}}
- previous_steps: {{previous_steps}}
- product_summary: {{product_summary}}
- target_cluster_pain: {{target_cluster_pain}}
- hypothesis: {{hypothesis}}
- step_number: {{step_number}}  # 1, 2, or 3
- tone: {{tone}}
- max_chars: {{max_chars}}

Rules:
- Step 1: gentle continuation
- Step 2: clearer value framing
- Step 3: low-friction close or graceful exit
- Do not sound repetitive
- Do not pressure the recipient
- Must remain evidence-based
- Must fit within max_chars

Return JSON:
{
  "message": "...",
  "goal": "...",
  "quality_score": 0-100,
  "stop_if_replied": true
}


⸻

18. 가장 중요한 설계 포인트

이 프로젝트에서 핵심은 단순 자동화가 아니다. 핵심은 아래 4개다.
	1.	Research-to-hypothesis 연결

	•	단순히 “관련 사람 많이 찾기”가 아니라
	•	“이 사람이 왜 지금 반응할 가능성이 있는가”까지 구조화해야 함

	2.	Hypothesis state machine

	•	성공/실패를 message 수준이 아니라 hypothesis 수준으로 학습해야 함

	3.	Auditability

	•	왜 이 사람에게 이 메시지를 이 시점에 보냈는지 추적 가능해야 함

	4.	Guardrails

	•	opt-out, exclusion, 중복 발송, 과도한 접촉을 강하게 통제해야 함

