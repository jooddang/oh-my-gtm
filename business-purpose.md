미국향 B2B SaaS 데모 콜 전환용 AI GTM 자동화 제품

문서 버전: v1.0  
문서 목적: AI 코딩 도구가 다른 방향으로 구현하지 않도록, 기능/동작/출력/제약조건을 과도할 정도로 구체적으로 정의한다.  
문서 언어: 한국어  
권장 산출물 형태: 웹앱 + 백엔드 워커 + 브라우저 확장(LinkedIn 캡처/준자동 발송) + 이메일 발송 모듈

---

## 0. 제품 한 줄 정의

이 제품은 **"미국 B2B SaaS 잠재고객의 공개/준공개 신호를 수집하고, 그 신호를 세그먼트-가설-메시지-실험-후속-학습 루프로 연결해, 최종적으로 온라인 데모 콜 예약 확률을 높이는 GTM 운영 시스템"**이다.

이 제품은 단순한 "메시지 생성기"가 아니다.  
이 제품은 다음 6개를 하나의 운영 루프로 묶어야 한다.

1. 타깃 발굴
2. 신호 기반 분류
3. 가설 생성
4. 메시지 생성 및 A/B 실험
5. 발송/후속/응답 처리
6. 성과 학습 및 전략 갱신

---

## 1. 문제 정의

현재 사용자는 한국인 스타트업 파운더이며, 미국 기업을 대상으로 제품 데모 콜을 잡고 싶다. 하지만 다음 문제가 있다.

1. 누가 진짜 잠재고객인지 판단하기 어렵다.
2. LinkedIn 포스트/참여자/경쟁사 언급처럼 **구매 가능성의 징후**는 많은데, 이를 수작업으로 수집/정리/우선순위화하기 어렵다.
3. 메시지를 많이 보내도, 어떤 세그먼트/가설/카피가 먹히는지 체계적으로 학습되지 않는다.
4. 이메일과 LinkedIn이 분리되어 운영되어, 관계 형성과 전환이 한 시스템 안에서 최적화되지 않는다.
5. 응답이 들어왔을 때 후속이 느려져서 기회를 놓친다.
6. LinkedIn 자동화/이메일 발송은 정책, 딜리버러빌리티, 프라이버시 리스크가 있어서 무작정 자동화하면 안 된다.

이 제품의 핵심 목표는 **"더 많은 메시지를 보내는 것"이 아니라, "올바른 사람에게, 올바른 이유로, 올바른 타이밍에, 올바른 메시지를 보내고, 그 결과를 학습해 점점 더 데모 콜 예약 가능성이 높은 운영 루프를 만드는 것"**이다.

---

## 2. 제품 목표 / 비목표

### 2.1 제품 목표

이 제품은 아래 목표를 달성해야 한다.

- 미국 B2B SaaS 잠재고객 발굴을 구조화한다.
- LinkedIn 기반 신호와 이메일/웹/CRM 신호를 하나의 우선순위 시스템으로 통합한다.
- 포스트/참여자/계정 데이터를 **세그먼트 단위 가설**로 변환한다.
- 가설별 메시지 A/B 테스트를 자동 운영한다.
- 후속(reply handling, next action)의 속도를 높인다.
- 세그먼트/가설/메시지/채널별 성과를 측정한다.
- 실패한 가설을 폐기하고, 새로운 가설을 자동 생성한다.
- 성공한 패턴을 프롬프트/메시지 전략에 재반영한다.
- 결과적으로 데모 콜 예약률을 높인다.

### 2.2 비목표

아래는 **명시적으로 제외**한다.

- LinkedIn에서 백그라운드로 무한 스크래핑하는 헤드리스 봇
- LinkedIn 자동 좋아요/자동 댓글/자동 활동 봇
- 사실 근거 없이 고객사/숫자/도입효과를 꾸며내는 생성 기능
- CRM 전체 대체 제품
- 범용 마케팅 자동화 제품
- 콜센터/음성 다이얼러 제품
- 광고 집행 제품
- 대규모 이메일 인프라 구축 SaaS 자체(본 제품은 발송 운영 계층이지 인프라 벤더가 아니다)

---

## 3. 핵심 설계 원칙

### 3.1 “사람별 가설”이 아니라 “세그먼트 가설 + 개인별 증거” 구조

사용자 질문:  
“가설을 사람별로 만드는 게 더 좋을까?”

정답: **아니다. 기본 단위는 사람별 가설이 아니라 세그먼트 가설이어야 한다.**  
단, 고가치 계정(Tier A)만 예외적으로 계정별/개인별 가설을 허용한다.

#### 이유

- 사람별 가설은 관리가 어렵다.
- 사람별 가설은 샘플 수가 작아 A/B 테스트가 성립하지 않는다.
- 성과 학습이 세그먼트 수준으로 축적되지 않는다.
- 운영자가 “무슨 메시지가 먹혔는지”가 아니라 “누구한테 우연히 먹혔는지”만 보게 된다.

#### 따라서 제품은 다음 2단 구조를 사용해야 한다.

1. **Campaign Hypothesis (실험 단위)**
   - 포스트 클러스터/세그먼트/페르소나/문제상황 기준으로 생성
   - 예: “최근 경쟁사 X를 언급한 RevOps 리더는 기존 운영 병목과 툴 스프롤 문제를 인식하고 있을 가능성이 높다”

2. **Prospect Angle (개인화 단위)**
   - 개인별로는 전체 가설을 새로 만들지 않고, 같은 가설 안에서 적용되는 **증거 스니펫/오프너/관찰 포인트**만 생성
   - 예: “이 사람은 경쟁사 X 도입 후 운영 문제를 언급했다”, “이 사람은 잡체인지 직후다”, “이 회사는 최근 펀딩을 받았다”

### 3.2 LinkedIn은 “관계 형성”, 이메일은 “전환” 역할로 분리

제품은 기본적으로 채널 역할을 나눠야 한다.

- LinkedIn: 연결, 신뢰 형성, 부드러운 첫 접점, 맥락 확인
- Email: 문제 정의, proof 전달, 데모 제안, 전환

즉, 제품은 단순히 두 채널 모두에 같은 문장을 보내면 안 된다.
채널별 목적이 달라야 한다.

### 3.3 개인화는 3단계 계층화

모든 계정을 1:1 수제 개인화하면 운영이 망가진다.  
제품은 기본적으로 아래 3단계 계층형 개인화를 사용해야 한다.

1. 세그먼트 템플릿
2. 신호 기반 1~2줄 개인 스니펫
3. 상위 고가치 계정만 휴먼 검수 강화

### 3.4 후속 자동화가 가장 중요한 자동화 구간

초기 발송만 잘 만드는 제품으로 개발하면 안 된다.  
이 제품은 **응답 이후의 다음 액션**을 더 중요하게 다뤄야 한다.

- 긍정 응답 → 데모 제안
- 반론 응답 → 반론 유형별 후속 초안
- 다른 담당자 추천 → 리다이렉트 루프
- 응답 없음 → 다음 실험 라운드로 편입
- opt-out/부정 반응 → 즉시 suppression

### 3.5 LinkedIn 기능은 “정책 준수형 운영모드”가 기본값

이 제품은 **LinkedIn 완전자동화 봇**으로 구현되면 안 된다.  
기본값은 아래여야 한다.

- 백그라운드 무한 스크래핑 금지
- 무인 자동 발송 금지
- 사용자가 명시적으로 연 페이지/리스트만 캡처
- 발송은 기본적으로 사람 승인 또는 준자동 모드

### 3.6 딜리버러빌리티를 제품 내부의 게이트로 다뤄야 함

이메일 발송 기능은 “연결만 되면 바로 발송”으로 구현되면 안 된다.  
아래 조건이 충족되기 전까지 캠페인을 차단해야 한다.

- 도메인 인증 상태 확인(SPF/DKIM/DMARC)
- 발송 메일박스 연결 상태 확인
- warm-up 상태 확인
- suppression/opt-out 설정 확인
- bounce 경고선 확인

---

## 4. 제품 성공 지표

### 4.1 북극성 지표

- **Booked Demo Rate** = `데모 예약 수 / 발송 완료된 적격 타깃 수`

### 4.2 핵심 운영 지표

- Qualified Leads Captured
- Send Queue Completion Rate
- LinkedIn Connect Acceptance Rate
- Reply Rate
- Positive Reply Rate
- Positive Reply to Meeting Conversion Rate
- Meeting Booked Rate
- Hypothesis Win Rate
- Variant Win Rate
- Follow-up Response Lift
- Lead-to-Meeting Cycle Time

### 4.3 가드레일 지표

- Email Bounce Rate
- Unsubscribe Rate
- Complaint Rate(연결 가능 시)
- LinkedIn Risk Event Count(차단/제한/실패 이벤트)
- Hallucination Flag Count(사실 검증 실패)
- Compliance Gate Failure Count

### 4.4 초기 벤치마크 기준(대시보드에 목표선으로 표시)

제품은 초기 벤치마크 목표선을 아래처럼 내장해야 한다.

- 건강한 이메일 오픈율 기준선: 20~30%
- 상위 캠페인 오픈율 기준선: 35%+
- 평균 콜드 이메일 응답률 기준선: 3~4.1%
- 강한 intent 프로그램 응답률 기준선: 8~15%
- 긍정 회신→미팅 전환 기준선: 20~30%
- 전체 발송→미팅 전환 기준선: 2~5%
- bounce 경고선: 2% 초과 시 즉시 경고/자동 일시정지
- spam complaint 경고선: 0.3% 근접 시 강한 경고

주의: 위 수치는 제품 내 “절대 보장 수치”가 아니라 **운영 건강도 벤치마크**로 표기해야 한다.

---

## 5. 사용자 유형

### 5.1 Primary User

- 미국 진출을 원하는 한국 스타트업 파운더
- 직접 세일즈를 하는 founder-led sales 운영자
- 소규모 GTM 팀 리드

### 5.2 Secondary User

- SDR/BDR 매니저
- RevOps 담당자
- Growth operator

### 5.3 사용자 목표

- 이번 주에 누구에게 연락해야 하는지 알고 싶다.
- 이 포스트/참여자가 진짜 타깃인지 알고 싶다.
- 어떤 가설로 접근해야 하는지 알고 싶다.
- 어떤 문구가 먹히는지 학습하고 싶다.
- 데모 콜을 더 많이 잡고 싶다.

---

## 6. 제품 범위

### 6.1 반드시 구현해야 하는 v1 범위

1. 워크스페이스/제품 맥락 설정
2. LinkedIn 포스트/참여자 캡처 입력
3. 리드 정규화/중복 제거/필터링
4. 세그먼트 가설 생성
5. 메시지/시퀀스 생성
6. A/B 테스트 할당
7. Email 자동 발송 큐
8. LinkedIn 준자동 발송 큐
9. 응답 분류 및 후속 초안
10. 성과 대시보드
11. 실패 학습 및 신규 가설 재생성
12. suppression/compliance gate

### 6.2 있어도 좋지만 v1 필수는 아닌 범위

- CRM 양방향 깊은 동기화
- website visitor identification
- full calendar integration
- direct mail
- voice call orchestration
- Slack alert
- data provider marketplace

---

## 7. 전체 사용자 플로우

### 7.1 전체 플로우 요약

1. 사용자가 판매할 제품 정보를 입력한다.
2. 사용자가 경쟁사/키워드/문제영역/제외대상 규칙을 설정한다.
3. 사용자가 LinkedIn 포스트 URL 또는 브라우저 캡처로 소스를 넣는다.
4. 시스템이 포스트/참여자를 추출하고 리드로 정규화한다.
5. 시스템이 fit / intent / data quality 기준으로 점수화한다.
6. 시스템이 포스트/시그널/페르소나 기준으로 클러스터를 만든다.
7. 시스템이 클러스터별 가설 5개를 생성한다.
8. 시스템이 각 가설에 대해 3개 first-touch 변형과 3단계 follow-up을 생성한다.
9. 시스템이 적격 리드 100명을 실험군으로 배정한다.
10. 이메일은 자동 큐에 올리고, LinkedIn은 준자동 큐에 올린다.
11. 응답이 오면 시스템이 분류하고 다음 액션 초안을 제안한다.
12. 데이터가 누적되면 가설/문구/채널 성과를 계산한다.
13. 실패한 가설은 폐기하고, 시스템이 신규 가설 3개를 생성한다.
14. 성공한 패턴은 프롬프트와 템플릿 라이브러리에 반영된다.

---

## 8. 정보 구조 / 화면 구조

제품은 최소 아래 화면을 제공해야 한다.

1. **Workspace Setup**
2. **Signal Inbox**
3. **Lead Review**
4. **Hypothesis Lab**
5. **Sequence Builder**
6. **Experiment Board**
7. **Send Queue**
8. **Inbox / Reply Triage**
9. **Insights Dashboard**
10. **Governance & Settings**

각 화면은 단순 요약이 아니라 실제 운영 액션이 가능해야 한다.

---

## 9. 기능 요구사항

# 9.1 Workspace Setup

### 목적

사용자의 제품, ICP, 메시지 근거, 경쟁사, 제외대상, 채널정책, CTA를 설정하는 화면이다.

### 입력 필드

- workspace_name
- product_name
- one_line_pitch
- product_description
- target_market
- target_personas[]
- industries[]
- company_size_ranges[]
- geographies[]
- problem_keywords[]
- competitor_names[]
- adjacent_tools[]
- proof_points[]
- approved_claims[]
- forbidden_claims[]
- demo_cta_text
- booking_link(optional)
- exclusion_rules[]
- linkedin_mode = `compliance_manual | assisted_semi_auto | api_only`
- email_mode = `manual_review | auto_send`
- human_review_required_for_high_risk_claims = boolean

### 시스템 동작

- 사용자가 제품 설명을 넣으면 시스템은 ICP 초안을 제안한다.
- 사용자가 경쟁사/문제영역을 넣으면 시스템은 검색 키워드 클러스터를 생성한다.
- 시스템은 proof_points를 별도 라이브러리로 저장한다.
- forbidden_claims가 있으면 이후 메시지 생성 시 절대 사용하면 안 된다.

### 출력

- ICP 카드 목록
- 검색 키워드 팩 목록
- proof point library
- exclusion policy summary
- launch readiness checklist

### 필수 제약

- proof point가 하나도 없으면 “성과/도입효과 주장형 메시지” 생성 금지
- competitor_names가 없더라도 problem_keywords 기반 탐색은 가능해야 함

---

# 9.2 Signal Inbox

### 목적

잠재고객 신호를 입력, 수집, 검토하는 화면이다.

### 지원 입력 방식

#### A. 수동 URL 입력 (v1 필수)
- LinkedIn post URL
- company page URL
- person profile URL
- comment thread URL

#### B. CSV 업로드 (v1 필수)
- columns 예시:
  - source_url
  - source_type
  - post_text
  - author_name
  - company_name
  - participant_name
  - participant_role
  - note

#### C. 브라우저 확장 캡처 (v1 필수)
- 사용자가 직접 연 LinkedIn 검색 결과 페이지/포스트 페이지/참여자 모달에서 visible DOM을 캡처한다.
- 시스템은 사용자가 보고 있는 현재 화면의 visible items만 가져온다.
- 백그라운드 전체 크롤링은 금지한다.

#### D. 웹/CRM/기타 시그널 API (v1 optional)
- webhook 또는 CSV 재업로드로 지원

### 추출 대상

- post
- author
- commenters
- likers/reactions(if available from input)
- repost participants(if available)
- matched_keyword
- matched_competitor
- engagement_type
- captured_at
- original_text
- evidence_snippet

### 시스템 동작

- URL/CSV/캡처 데이터를 구조화한다.
- 각 item에 source provenance를 저장한다.
- 포스트 단위와 참여자 단위를 분리 저장한다.
- 동일 person/company는 dedup 후보로 표시한다.

### 출력 UI

Signal Inbox 테이블 컬럼:

- Source
- Type(Post/Participant)
- Keyword Match
- Person
- Company
- Role
- Engagement Type
- Recency
- Evidence Snippet
- Extract Status
- Qualification Status
- Actions

### 액션

- Approve as lead
- Reject
- Merge duplicate
- Add note
- Create cluster
- Send to Hypothesis Lab

### 필수 제약

- provenance 없는 데이터는 outbound 실행 대상이 될 수 없다.
- 사용자가 직접 제공하지 않은 LinkedIn 데이터를 백그라운드에서 추가 수집하면 안 된다.

---

# 9.3 Lead Review / Enrichment / Qualification

### 목적

리드를 정규화하고, 제외대상을 필터링하며, 적합도와 구매의도 가능성을 점수화한다.

### 리드 데이터 구조

Lead는 최소 아래 필드를 가져야 한다.

- lead_id
- person_name
- linkedin_url(optional)
- company_name
- company_domain(optional)
- title
- seniority
- department
- location
- source_type
- source_url
- source_post_id(optional)
- evidence_snippet
- matched_keywords[]
- matched_competitors[]
- recent_signals[]
- fit_score
- intent_score
- data_quality_score
- policy_risk_score
- priority_score
- exclusion_reason(optional)
- qualification_status
- segment_id(optional)
- assigned_hypothesis_ids[]

### 필터링 규칙

기본 제외 규칙은 아래를 지원해야 한다.

- student
- competitor employee
- agency / consultant
- recruiter
- vendor / partner
- duplicate profile
- missing critical fields
- geography mismatch
- title mismatch

사용자는 규칙을 추가/삭제할 수 있어야 한다.

### 점수 계산

#### Fit Score (0~100)
- persona match: 0~35
- company size match: 0~20
- industry match: 0~15
- geography match: 0~10
- seniority match: 0~10
- adjacent tool / environment match: 0~10

#### Intent Score (0~100)
- source relevance: 0~25
- engagement depth: 0~20
- recency: 0~15
- why_now trigger: 0~25
- web/CRM/additional signal: 0~15

#### Data Quality Score (0~100)
- source completeness
- company/person match confidence
- title freshness
- duplicate risk inverse

#### Policy Risk Score (0~100, 높을수록 위험)
- source provenance missing
- uncertain scraping provenance
- unsupported claim dependency
- sensitive jurisdiction / privacy uncertainty

#### Priority Score

`priority_score = (fit_score * 0.4) + (intent_score * 0.4) + (data_quality_score * 0.2) - policy_penalty`

where:

`policy_penalty = policy_risk_score * 0.2`

### 등급 분류

- Tier A: priority >= 80
- Tier B: priority 60~79
- Tier C: priority 40~59
- Reject: < 40 또는 exclusion triggered

### 출력

- qualified lead list
- excluded lead list
- segment candidates
- explanation chips: “왜 이 리드인가?”

### UI 요구사항

각 리드 카드에 반드시 아래가 보여야 한다.

- 왜 타깃인지 설명 문장 1개
- 어떤 신호가 잡혔는지
- 어떤 제외 규칙을 통과했는지
- 어떤 가설에 배정될 예정인지

---

# 9.4 Segmentation & Cluster Engine

### 목적

리드를 사람 단위의 무작위 집합이 아니라, **실험 가능한 세그먼트/클러스터**로 묶는다.

### 세그먼트 기준

클러스터는 최소 아래 4개 축 조합으로 생성되어야 한다.

- persona
- signal theme
- company segment
- channel suitability

예시:

- RevOps + 경쟁사 언급 + SMB SaaS + LinkedIn-first
- Security leader + 잡체인지 + Mid-market + Email-first
- Founder + 펀딩 시그널 + Series A/B + dual-channel

### 클러스터 생성 로직

- 동일 키워드/문제영역/경쟁사 언급 패턴이면 같은 후보 클러스터
- 같은 역할/부서이면 같은 후보 클러스터
- 같은 why-now trigger면 같은 후보 클러스터
- 클러스터 최소 크기 미달 시 “draft cluster”로 유지

### 출력

Cluster object:

- cluster_id
- cluster_name
- lead_count
- primary_persona
- primary_signal
- why_now_type
- company_band
- recommended_channel_mix
- sample_evidence[]

### 제약

- 클러스터 크기가 너무 작으면(예: 5명 미만) 기본적으로 사람별 가설 생성 금지
- Tier A는 예외적으로 account-specific cluster 허용

---

# 9.5 Hypothesis Lab

### 목적

각 클러스터에 대해 **테스트 가능한 가설**을 생성하고 승인한다.

### 핵심 원칙

- 가설은 사람별이 아니라 클러스터별로 생성한다.
- 가설은 추상적이면 안 된다.
- 가설은 “이 사람들이 왜 지금 반응할 가능성이 있는가”를 설명해야 한다.
- 가설은 반드시 반증 가능해야 한다.

### 시스템 생성 규칙

각 클러스터마다 기본 5개 가설을 생성한다.

각 가설은 아래 필드를 포함해야 한다.

- hypothesis_id
- cluster_id
- title
- statement
- target_problem
- why_now_reason
- supporting_signals[]
- recommended_proof_points[]
- recommended_channel
- recommended_cta
- disqualifiers[]
- confidence_score
- status = `draft | approved | active | weak | retired | winning`

### 생성 예시 포맷

```json
{
  "title": "경쟁사 언급 후 운영 병목 가설",
  "statement": "최근 경쟁사 X를 언급한 RevOps 리더는 현재 운영 병목 또는 기존 툴 스프롤 문제를 인식하고 있어, 운영 단순화/성과 측정 자동화 메시지에 반응할 가능성이 높다.",
  "target_problem": "툴 스프롤, 수동 후속, 파이프라인 가시성 부족",
  "why_now_reason": "경쟁사 언급 직후 또는 비교 탐색 중인 시점",
  "supporting_signals": ["competitor_mention", "comment_on_relevant_post"],
  "recommended_proof_points": ["setup_speed", "meeting_conversion_improvement"],
  "recommended_channel": "linkedin_first_then_email",
  "recommended_cta": "15분 데모 제안",
  "disqualifiers": ["student", "agency", "competitor_employee"],
  "confidence_score": 0.76
}
```

### 사용자 액션

- approve
- edit
- merge hypotheses
- retire
- pin as control
- mark as high-risk claim review needed

### 필수 제약

- 숫자/고객사/효과를 포함하는 가설 문장은 proof point library에 근거가 없으면 생성 금지
- 특정 개인의 심리를 단정하는 문구 금지
- 지원 신호가 없는 가설 금지

---

# 9.6 Prospect Angle Generator

### 목적

같은 가설 안에서 사람별 오프너를 생성한다.

### 동작

각 리드에 대해 전체 새 가설을 만드는 대신, 승인된 가설 중 상위 1~2개에 대해 개인별 angle을 생성한다.

각 angle은 아래 필드를 갖는다.

- angle_id
- lead_id
- hypothesis_id
- opener_reason
- evidence_snippet
- risk_flags[]
- personalization_strength = `light | medium | heavy`

### 예시

- “최근 X 관련 포스트에 남기신 코멘트를 보고”
- “경쟁사 Y를 언급하신 문맥을 보면”
- “최근 역할 이동 직후라 운영 재정비를 고민하실 가능성이 있어 보여”

### 필수 제약

- evidence_snippet은 source provenance가 있어야 한다.
- 존재하지 않는 활동/발언을 만들어내면 안 된다.

---

# 9.7 Message Lab / Sequence Builder

### 목적

가설별/채널별 메시지와 follow-up 시퀀스를 생성하고 관리한다.

### 메시지 원칙

- 첫 접점 메시지는 짧아야 한다.
- 이메일 first touch는 기본적으로 링크를 넣지 않는다.
- 메시지는 BAR 구조를 사용한다.
- 각 메시지는 하나의 문제와 하나의 CTA만 가져야 한다.
- claim은 proof point library에 기반해야 한다.

### BAR 구조 요구사항

모든 이메일 first touch는 아래 구조를 가져야 한다.

1. Background
2. Action
3. Results
4. 매우 짧은 CTA

단, 실제 출력은 3~5문장 수준으로 압축해야 한다.

### 생성 대상

각 hypothesis × channel 조합마다 아래 메시지를 생성한다.

#### LinkedIn
- connection opener A/B/C
- post-accept follow-up step 1
- follow-up step 2
- follow-up step 3

#### Email
- first touch A/B/C
- follow-up step 1
- follow-up step 2
- follow-up step 3

### Message Variant 구조

- variant_id
- hypothesis_id
- channel
- stage
- variant_label (A/B/C)
- objective (`connect_accept | reply | positive_reply | meeting`)
- opener_text
- body_text
- cta_text
- proof_points_used[]
- prohibited_claim_check = pass/fail
- readability_score
- personalization_mode

### 단계별 기본 시퀀스 정의

#### LinkedIn sequence default
- Stage L0: connection message
- Stage L1: connection accepted 후 1차 follow-up
- Stage L2: 2 business days 후 짧은 pain + why-now follow-up
- Stage L3: 4 business days 후 soft close / referral ask

#### Email sequence default
- Stage E0: first touch
- Stage E1: 2 business days 후 짧은 reframe
- Stage E2: 4 business days 후 proof or case angle
- Stage E3: 5 business days 후 low-friction close

### 출력 UI

메시지 카드에는 아래를 보여줘야 한다.

- variant label
- channel / stage
- hypothesis tag
- opener
- proof point tag
- CTA
- risk flags
- predicted objective

### 필수 제약

- 하나의 메시지에 서로 다른 hypothesis 2개를 섞지 말 것
- unsupported claim 사용 금지
- first touch에 길고 복잡한 본문 금지
- connection message는 플랫폼 제한을 초과하지 않도록 별도 검증 로직 필요

---

# 9.8 Experiment Engine

### 목적

메시지 실험을 무작위가 아니라 **가설-세그먼트 단위 실험**으로 운영한다.

### 실험 단위

Experiment Unit = `segment x hypothesis x channel x stage`

### 기본 실험 규칙

- 첫 실험 배치는 적격 리드 100명 기준으로 시작
- A/B/C 3개 variant를 균등 배정
- 같은 리드는 같은 stage의 variant 하나만 받는다
- 서로 다른 세그먼트의 결과를 섞어 해석하지 않는다
- 비교는 동일 channel / 동일 stage / 동일 hypothesis 안에서만 수행한다

### 실험 상태

- draft
- running
- waiting_for_sample
- winner_selected
- paused
- closed

### 단계별 평가 지표

- LinkedIn connection stage: acceptance_rate
- first reply stage: reply_rate
- positive response stage: positive_reply_rate
- ultimate success: meeting_booked_rate

### 가중 점수

제품은 raw reply보다 meeting을 더 높게 평가해야 한다.

기본 가중 점수 예시:

`score = (meeting_booked * 5) + (positive_reply * 3) + (reply * 1) + (connect_accept * 0.5) - (negative_reply * 3) - (opt_out * 10) - (risk_event * 15)`

### 자동 판정 규칙

- variant별 최소 노출 수: 25
- variant별 최소 대기 시간: 5 business days
- 위 조건 충족 전에는 winner 선언 금지
- tie면 control 유지
- 리스크 이벤트가 발생한 variant는 즉시 pause 가능

### 실패 판정 규칙

- 한 hypothesis 아래의 A/B/C 3개 variant가 모두 최소 표본을 채운 후에도 positive_reply=0 이고 meeting=0 이면 hypothesis를 `weak`로 변경
- weak 상태가 2회 연속 발생하면 hypothesis를 `retired`로 변경
- retired 시 system이 sibling hypothesis 3개를 자동 생성

### 성공 판정 규칙

- 동일 hypothesis에서 meeting 2건 이상 또는 segment baseline 대비 25% 이상 개선 시 `winning`
- winning hypothesis는 prompt library에 반영

---

# 9.9 Send Queue / Execution Orchestrator

### 목적

승인된 메시지를 채널별 정책에 맞게 발송한다.

## 9.9.1 Email Execution

### 기능

- mailbox 연결
- domain health 표시
- queue scheduling
- send window 설정
- bounce/unsubscribe 처리
- auto pause

### 선행 조건

아래가 모두 완료되어야 이메일 campaign launch 가능

- mailbox connected = true
- SPF check = pass
- DKIM check = pass
- DMARC status != missing
- suppression list available = true
- launch gate passed = true

### 일시정지 조건

- bounce rate > workspace threshold
- unsubscribe spike
- complaint webhook threshold breach
- manual stop

### 출력

- queued
- sent
- delivered(if available)
- bounced
- replied
- unsubscribed
- complaint(if available)

## 9.9.2 LinkedIn Execution

### 기본 운영 모드

기본값은 `compliance_manual` 이어야 한다.

### 모드 정의

#### compliance_manual
- 시스템은 메시지와 다음 대상을 준비만 한다.
- 사용자가 직접 페이지에서 최종 send를 수행한다.

#### assisted_semi_auto
- 브라우저 확장이 다음 대상 이동, 메시지 프리필, 상태 저장을 돕는다.
- 최종 발송 클릭은 사용자 확인이 있어야 한다.

#### api_only
- 공식 허용 방식이 있을 때만 사용

### 금지 사항

- 무인 대량 발송
- 자동 좋아요/댓글/프로필 방문 봇
- 백그라운드 전체 스크래핑
- 계정 보존보다 생산성을 우선하는 모드

### Queue Item 구조

- queue_item_id
- lead_id
- channel
- stage
- message_variant_id
- scheduled_at
- mode
- requires_human_approval
- status
- sent_at
- failure_reason

### UX 요구사항

Send Queue 화면에는 반드시 아래가 보여야 한다.

- 다음 대상
- 왜 이 대상인지
- 사용될 가설
- 사용될 메시지
- 위험 플래그
- 승인 버튼 / 스킵 버튼 / 수정 후 보내기 버튼

---

# 9.10 Inbox / Reply Triage

### 목적

응답을 자동 분류하고, 다음 액션 초안을 제안한다.

### 지원 분류 카테고리

- positive_interest
- meeting_ready
- objection
- not_now
- wrong_person
- referral
- unsubscribe
- negative
- out_of_office
- unclear

### 시스템 동작

- 수신 메시지를 thread 단위로 읽는다.
- 분류 결과와 confidence를 저장한다.
- 카테고리별 recommended next action을 생성한다.

### 카테고리별 액션 예시

#### positive_interest
- 짧은 감사 + 2개 시간 제안 또는 booking link

#### meeting_ready
- 즉시 일정 연결

#### objection
- objection type 분류(가격/우선순위/기존 툴/타이밍/권한 없음)
- proof point 기반 대응 초안 생성

#### wrong_person
- 적절한 담당자 소개 요청 문구 생성

#### referral
- warm redirect 후속 생성

#### unsubscribe
- suppression 즉시 추가
- 모든 queue item 취소

### 필수 제약

- 가격/보안/법률/컴플라이언스 관련 답변은 고위험 클레임으로 분류 가능해야 함
- 고위험 답변은 human approval required

### 출력 UI

- thread summary
- classification tag
- confidence
- recommended next action
- draft reply
- proof points used
- approval status

---

# 9.11 Learning Loop Engine

### 목적

실패와 성공을 다음 라운드에 반영한다.

### 핵심 기능

1. 실패 패턴 요약
2. 신규 가설 생성
3. 승리 원리 추출
4. prompt memory 업데이트

### No Response 루프

응답이 없을 때는 다음 순서로 동작해야 한다.

1. 동일 hypothesis 내 다른 variant를 **새 타깃에게** 사용
2. 세 variant 모두 약하면 hypothesis를 weak 처리
3. weak 누적 시 retired
4. retired 시 실패 이유를 요약하여 신규 hypothesis 3개 생성

### Response 있음 루프

응답이 있을 때는 다음 순서로 동작해야 한다.

1. 응답 유형을 분류
2. 해당 hypothesis / channel / stage / persona 성과를 가중치 반영
3. 성공 메시지의 공통 구조를 추출
4. 이후 message prompt에 반영

### Winning Principle 구조

- winning_principle_id
- segment
- trigger_type
- best_opener_pattern
- best_pain_pattern
- best_proof_pattern
- best_cta_pattern
- avoid_patterns[]
- supporting_experiments[]

### 예시 출력

- “경쟁사 언급 직후 접근 + 운영 병목 framing + 짧은 CTA가 RevOps 세그먼트에서 가장 강했다.”
- “너무 광범위한 일반론 메시지는 acceptance는 나와도 meeting으로 이어지지 않았다.”

---

# 9.12 Insights Dashboard

### 목적

성과를 오픈/리플라이가 아니라 미팅과 파이프라인 관점으로 보여준다.

### 필수 위젯

1. Funnel Overview
2. Segment Performance
3. Hypothesis Performance
4. Variant Performance
5. Channel Split
6. Reply Classification Breakdown
7. Meeting Conversion View
8. Deliverability Health
9. Compliance Events
10. Weekly Learnings

### Funnel 단계

- signals captured
- leads qualified
- leads approved
- queue created
- sent
- accepted (LinkedIn)
- replied
- positive_replied
- meeting_booked

### 테이블 뷰 필수 컬럼

#### Hypothesis table
- hypothesis
- segment
- leads_sent
- reply_rate
- positive_reply_rate
- meeting_rate
- status
- best_variant
- risk_flags

#### Channel table
- channel
- first_touch_sent
- acceptance_rate / open_rate
- reply_rate
- meeting_rate
- avg_cycle_days

#### Deliverability table
- mailbox
- sent_today
- bounce_rate
- unsubscribe_rate
- complaint_rate
- status

### 필수 시각화 규칙

- vanity metrics만 크게 보여주면 안 된다.
- booked meeting과 positive reply가 오픈율보다 상단에 있어야 한다.
- guardrail breach는 항상 빨간 경고로 상단 표시

---

# 9.13 Governance & Compliance Center

### 목적

정책/법률/프라이버시/브랜드 리스크를 실행 전에 차단한다.

### 필수 기능

- suppression list 관리
- do-not-contact list
- exclusion rules
- source provenance log
- claim validation log
- compliance gate history
- LinkedIn mode setting
- email launch gate
- audit trail

### Launch Gate 항목

캠페인 launch 전 아래 항목을 체크해야 한다.

- source provenance complete
- required sender details complete
- opt-out path active
- proof points validated
- forbidden claims absent
- high risk claims reviewed
- domain/mailbox health acceptable
- LinkedIn mode confirmed

launch gate 실패 시 발송 버튼은 비활성화되어야 한다.

---

## 10. LLM 동작 명세

### 10.1 공통 원칙

모든 LLM 출력은 자유 텍스트만 반환하면 안 된다.  
항상 **구조화 JSON + 사용자 표시용 텍스트** 두 층으로 처리해야 한다.

### 10.2 LLM 금지 행동

- 존재하지 않는 고객명 생성
- 존재하지 않는 수치 생성
- 근거 없는 제품 기능 생성
- 리드가 하지 않은 발언을 한 것처럼 작성
- “당신 회사가 분명 이 문제를 겪고 있다” 식의 과도한 단정

### 10.3 LLM 프롬프트 입력 컨텍스트

최소 아래를 포함해야 한다.

- workspace product context
- approved proof points
- forbidden claims
- lead evidence snippet
- cluster definition
- hypothesis text
- channel
- stage
- tone rules
- CTA style
- risk mode

### 10.4 LLM 출력 스키마 예시

```json
{
  "channel": "email",
  "stage": "E0",
  "hypothesis_id": "hyp_123",
  "variant_label": "B",
  "opener": "최근 X 관련 논의를 보고 연락드립니다.",
  "body": "유사한 팀들이 Y 문제로 운영 병목을 겪는 경우가 많았습니다...",
  "cta": "짧게 15분 정도 이야기 나눠보실까요?",
  "proof_points_used": ["pp_1", "pp_4"],
  "risk_flags": [],
  "claim_validation_status": "pass"
}
```

### 10.5 Human Review 조건

다음 중 하나면 human review required:

- customer name claim
- performance number claim
- legal/compliance/security claim
- account value Tier A
- unclear provenance

---

## 11. 데이터 모델

### 핵심 엔터티 목록

- Workspace
- ProductProfile
- ICPDefinition
- ProofPoint
- ExclusionRule
- SignalSource
- SourcePost
- SourceParticipant
- Lead
- Company
- SegmentCluster
- Hypothesis
- ProspectAngle
- Sequence
- MessageVariant
- Experiment
- ExperimentAssignment
- SendQueueItem
- ConversationThread
- ReplyEvent
- ReplyClassification
- MeetingEvent
- LearningInsight
- SuppressionEntry
- AuditEvent

### 최소 관계

- Workspace 1:N ProductProfile
- Workspace 1:N SignalSource
- SignalSource 1:N SourcePost
- SourcePost 1:N SourceParticipant
- SourceParticipant N:1 Lead
- Lead N:1 Company
- Lead N:1 SegmentCluster
- SegmentCluster 1:N Hypothesis
- Hypothesis 1:N MessageVariant
- Experiment 1:N ExperimentAssignment
- Lead 1:N SendQueueItem
- Lead 1:N ConversationThread
- ConversationThread 1:N ReplyEvent
- ReplyEvent 1:1 ReplyClassification
- Lead 1:N MeetingEvent
- Workspace 1:N SuppressionEntry
- Workspace 1:N AuditEvent

---

## 12. 이벤트 택소노미

제품은 분석 가능하도록 아래 이벤트를 모두 기록해야 한다.

- source_captured
- source_parsed
- lead_created
- lead_qualified
- lead_rejected
- hypothesis_generated
- hypothesis_approved
- message_generated
- experiment_started
- experiment_assigned
- queue_created
- queue_sent
- queue_failed
- linkedin_approved
- linkedin_skipped
- email_bounced
- reply_received
- reply_classified
- meeting_booked
- opt_out_received
- suppression_added
- hypothesis_retired
- hypothesis_won
- learning_insight_created
- compliance_gate_failed
- campaign_paused

각 이벤트는 최소 아래 공통 필드를 가져야 한다.

- event_id
- event_type
- workspace_id
- actor_type (`user | system | worker`)
- actor_id
- related_entity_type
- related_entity_id
- metadata_json
- created_at

---

## 13. 구체적 비즈니스 로직

### 13.1 priority queue 생성 규칙

발송 큐는 priority_score만으로 만들면 안 된다.  
아래 조건을 모두 반영해야 한다.

- priority_score 높은 순
- 같은 회사 과접촉 방지
- 같은 세그먼트 과대표집 방지
- variant 균등 배정 유지
- suppression 제외
- recent contact cooldown 적용

### 13.2 cooldown 규칙

- 동일 lead에 대해 같은 채널 first touch 중복 발송 금지
- 동일 회사 다수 인물에게 같은 날 과도 접촉 금지
- exact cooldown 값은 설정 가능해야 함

### 13.3 same-account control

같은 회사의 여러 명을 동시에 실험군에 넣을 때는 아래를 지원해야 한다.

- company-level cap
- account owner note
- cluster collision warning

### 13.4 reply speed rule

positive_interest / meeting_ready / referral 은 **우선순위 상단**으로 올려야 한다.

Inbox는 단순 최신순이 아니라 아래 우선순위를 기본값으로 사용한다.

1. meeting_ready
2. positive_interest
3. referral
4. objection
5. wrong_person
6. not_now
7. unclear
8. out_of_office
9. unsubscribe / negative

### 13.5 failure-derived hypothesis generation

신규 가설 3개 생성 시 입력으로 아래를 사용한다.

- retired hypothesis 문장
- failed variants
- negative / no-response pattern
- segment traits
- winning patterns from adjacent segments

출력은 반드시 기존 가설과 구분되는 관점이어야 한다.

예:
- 기존: 경쟁사 교체 angle
- 신규1: 잡체인지 기반 운영 재설계 angle
- 신규2: 최근 채용 확장 기반 프로세스 스케일 angle
- 신규3: 툴 스프롤 통합 angle

---

## 14. UI 상세 요구사항

### 14.1 Signal Inbox

각 row 클릭 시 우측 drawer가 열려 아래를 보여야 한다.

- 원문 포스트/코멘트 텍스트
- source URL
- 추출된 인물/회사 정보
- matched keywords
- inferred signal tags
- qualification explanation
- approve / reject / edit 버튼

### 14.2 Hypothesis Lab

화면은 3컬럼이어야 한다.

- 좌측: cluster list
- 중앙: hypothesis cards
- 우측: selected hypothesis detail + sample messages

### 14.3 Experiment Board

칸반 또는 매트릭스 형태로 아래 상태를 보여야 한다.

- draft
- running
- winner
- weak
- retired

각 카드에는 다음이 있어야 한다.

- segment
- hypothesis
- lead count
- sent count
- reply rate
- positive rate
- meeting count
- best variant
- risk events

### 14.4 Send Queue

목록이 아니라 운영용 큐여야 한다.

필수 액션:
- approve and send
- edit before send
- skip
- suppress lead
- mark as not relevant

### 14.5 Dashboard

기간 필터:
- last 7 days
- last 30 days
- custom

세그먼트 필터:
- persona
- signal type
- channel
- hypothesis
- owner

---

## 15. 성능 요구사항

- 1000건의 lead import 후 60초 내 initial qualification 완료
- hypothesis generation은 cluster 1개당 30초 내 초안 반환
- message generation은 variant 1개당 10초 내 초안 반환
- reply classification은 수신 후 30초 내 완료
- dashboard aggregation은 최근 30일 기준 5초 내 로드

이 수치는 초기 목표이며, 비동기 작업 사용을 전제로 한다.

---

## 16. 권한 및 역할

### roles
- owner
- admin
- operator
- reviewer
- viewer

### 권한 예시

- owner/admin: settings, launch gate override, suppression 관리
- operator: source review, queue 처리, hypothesis 승인 요청
- reviewer: high risk claim 승인
- viewer: dashboard 보기만 가능

---

## 17. 오류 및 예외 처리

### 반드시 처리해야 하는 예외

- 동일 LinkedIn 프로필 중복 import
- 회사명 불일치
- 사람/회사 매칭 실패
- source provenance missing
- proof point 없음
- mailbox disconnected
- domain auth incomplete
- opt-out rule missing
- LinkedIn extension capture failure
- reply classification confidence low
- experiment sample size insufficient

### 사용자에게 보여줄 방식

오류는 단순 “실패”가 아니라 다음 액션과 함께 표시해야 한다.

예:
- “도메인 인증이 완료되지 않아 이메일 발송이 차단되었습니다. Settings > Email Health에서 SPF/DKIM/DMARC 상태를 확인하세요.”
- “이 리드는 source provenance가 없어 발송 대상이 될 수 없습니다. 수동 검토 또는 재캡처가 필요합니다.”

---

## 18. 보안 및 감사 요구사항

- 모든 발송/수정/삭제 액션은 audit log 기록
- suppression 변경도 audit 대상
- human review override 기록 필수
- proof point 수정 이력 저장
- source provenance 원본 보존
- 삭제된 리드도 최소 감사 메타데이터 보존

---

## 19. 추천 기술 구조(권장안)

이 섹션은 “필수 스택”이 아니라, 구현 방향을 흐리지 않기 위한 권장 구조다.

### 프론트엔드
- Next.js 또는 동급 SPA
- server-side rendering 가능한 구조 선호

### 백엔드
- API 서버 + worker 분리
- relational DB 기반
- queue/cron 지원

### DB
- PostgreSQL 권장
- audit/event table 필수
- vector search optional

### 비동기 작업
- Redis queue / Celery / BullMQ 등

### 브라우저 확장
- Chrome extension 또는 Chromium 계열 확장
- visible DOM capture only
- user action required for send

### AI 계층
- structured JSON output 강제
- prompt versioning 저장
- generation logs 저장

---

## 20. 출시 범위 정의

### Phase 1 (Hackathon MVP)

반드시 데모 가능한 범위:

- workspace setup
- LinkedIn post URL/CSV import
- visible capture extension MVP
- lead qualification
- segment clustering
- hypothesis 5개 생성
- message 3 variant 생성
- simple experiment assignment
- email send queue
- LinkedIn manual queue
- reply classification
- dashboard basic funnel
- suppression / compliance gate basic

### Phase 2

- richer follow-up automation
- learning memory 강화
- winning principle extraction
- calendar event sync
- CRM sync
- inbox approval workflow 개선

### Phase 3

- website/CRM signal ingestion
- cross-channel trigger orchestration
- advanced bandit optimization
- enterprise compliance controls

---

## 21. 수용 기준(Acceptance Criteria)

아래 시나리오가 모두 통과되어야 v1 완료로 간주한다.

### 시나리오 1: LinkedIn 포스트 기반 타깃 발굴

- 사용자가 LinkedIn post URL 10개를 입력한다.
- 시스템이 각 포스트에서 author/participants/evidence를 구조화한다.
- 중복 제거 후 적격 리드를 생성한다.
- 학생/경쟁사/에이전시 제외 규칙을 적용한다.
- 결과적으로 적격 리드 목록이 생성된다.

### 시나리오 2: 가설 생성

- 시스템이 리드를 3개 이상 클러스터로 묶는다.
- 각 클러스터마다 가설 5개를 생성한다.
- 각 가설에 why-now, supporting signal, recommended proof가 포함된다.

### 시나리오 3: 메시지 생성 및 실험

- 승인된 가설 1개에 대해 channel별 first touch A/B/C가 생성된다.
- 각 variant는 proof point 검증을 통과한다.
- 100명의 리드가 균등 배정된다.

### 시나리오 4: 발송 실행

- 이메일은 queue에서 자동 발송된다.
- LinkedIn은 Send Queue에서 사용자가 승인 후 발송한다.
- 발송 결과가 상태값으로 저장된다.

### 시나리오 5: 응답 처리

- reply가 들어오면 30초 내 분류된다.
- positive/reply/objection/unsubscribe가 구분된다.
- 다음 액션 초안이 생성된다.
- unsubscribe는 suppression에 자동 반영된다.

### 시나리오 6: 학습 루프

- 최소 1개 hypothesis가 weak 또는 winning 상태로 이동한다.
- weak hypothesis는 신규 hypothesis 3개 생성을 트리거한다.
- winning hypothesis는 learning insight를 만든다.

### 시나리오 7: 대시보드

- funnel, segment, hypothesis, variant, channel, guardrail이 모두 조회된다.
- vanity metric이 아니라 meeting booked가 상단 KPI로 보인다.

---

## 22. 구현 시 절대 어기면 안 되는 것

1. LinkedIn을 헤드리스 자동화 봇처럼 구현하지 말 것
2. 사람별 전체 가설을 기본 구조로 만들지 말 것
3. proof point 없는 claim을 허용하지 말 것
4. launch gate 없이 이메일 발송 버튼을 열지 말 것
5. dashboard를 오픈율 중심으로 만들지 말 것
6. 응답 처리 기능을 후순위로 미루지 말 것
7. source provenance를 저장하지 않는 구조로 만들지 말 것
8. suppression/opt-out를 나중에 붙이는 식으로 만들지 말 것
9. experiment를 세그먼트 구분 없이 전역 random test로 만들지 말 것
10. learning loop 없이 “메시지 생성기” 수준에서 끝내지 말 것

---

## 23. 최종 제품 정의

이 제품이 완성되었다는 것은 다음을 의미한다.

- 사용자는 포스트/참여자/시그널을 넣을 수 있다.
- 시스템은 누가 타깃인지 설명할 수 있다.
- 시스템은 왜 지금 연락해야 하는지 가설로 설명할 수 있다.
- 시스템은 채널별 메시지를 생성할 수 있다.
- 시스템은 실험군을 배정할 수 있다.
- 시스템은 이메일과 LinkedIn을 역할 분리해 운영할 수 있다.
- 시스템은 응답을 분류하고 후속을 제안할 수 있다.
- 시스템은 어떤 가설과 메시지가 데모 콜로 이어지는지 학습할 수 있다.
- 시스템은 실패로부터 다음 실험을 자동 설계할 수 있다.

즉, 완성된 제품은 **"리드 리스트 + 메시지 생성기"**가 아니라 **"신호 기반 데모 예약 운영체계"**여야 한다.
