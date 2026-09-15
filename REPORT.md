# 🤖 My AI Work Radar

## LangGraph 기반 AI 업무 뉴스레터 에이전트

---

## 1. 프로젝트 개요

### 1.1 프로젝트 목적

My AI Work Radar는 AI Agent와 업무자동화에 관심 있는
비개발자 실무자를 위한 맞춤형 AI 뉴스레터 에이전트이다.

단순히 최신 AI 기사를 모아 요약하는 것이 아니라,
여러 기술 블로그에서 기사를 자동 수집하고
독자에게 실제로 유용한 기사를 선별한 뒤
원문 기반 요약과 실무 인사이트를 생성한다.

최종 결과는 자동 검수를 거쳐 이메일 뉴스레터로 발행된다.

핵심 정보 가공 구조는 다음과 같다.

**Fact → Meaning → Relevance → Action**

- Fact: 무슨 일이 있었는가?
- Meaning: 왜 중요한가?
- Relevance: 실무자에게 어떤 의미가 있는가?
- Action: 오늘 무엇을 적용해 볼 수 있는가?


### 1.2 대상 독자

주요 독자는 다음과 같이 정의하였다.

- AI Agent를 배우고 있는 비개발자
- 업무자동화에 관심 있는 직장인
- AI 기술을 실제 업무에 적용하고 싶은 실무자
- 공공기관 및 일반 사무 업무에서 AI 활용 가능성을 찾는 사용자

따라서 단순 기술 뉴스의 화제성보다
**실제 업무 활용 가능성**을 중요한 선별 기준으로 설정하였다.

---

## 2. 전체 시스템 구조

LangGraph를 이용해 다음 파이프라인을 구성하였다.

START
→ Collect
→ Normalize & Dedupe
→ Prefilter
→ LLM Ranking
→ Fetch Article Content
→ Summary & Insight
→ Validation
→ Compose Newsletter
→ Publish Email
→ END

각 단계의 역할은 다음과 같다.

| 단계 | 역할 |
|---|---|
| Collect | 여러 RSS 소스에서 기사 수집 |
| Normalize | HTML 제거 및 데이터 형식 통일 |
| Dedupe | URL 및 제목 기준 중복 제거 |
| Prefilter | 관심 키워드 기반 1차 예선 |
| Rank | LLM 기반 실무 가치 평가 |
| Fetch Content | 최종 후보 기사 본문 수집 |
| Summary | 원문 기반 요약 및 인사이트 생성 |
| Validation | 코드 + LLM 기반 자동 검수 |
| Compose | HTML 뉴스레터 생성 |
| Publish | Gmail을 통한 이메일 발행 |

---

## 3. 자료 수집 및 소스 선정

### 3.1 소스 선정 방식

소스는 사전 인지도나 주관적인 선호만으로 결정하지 않았다.

각 후보 RSS를 실제로 호출한 뒤 다음 항목을 측정하였다.

1. RSS가 정상적으로 자동 수집되는가?
2. 최근 게시물이 존재하는가?
3. 관심 키워드가 포함된 기사 비율은 어느 정도인가?
4. 최종 뉴스레터의 주제 다양성에 기여하는가?

소스 간 비교의 공정성을 높이기 위해
평가 시 최대 30개 기사로 표본 수를 제한하였다.


### 3.2 후보 소스 측정 결과

| 후보 소스 | 관심 주제 적중률 | 판단 |
|---|---:|---|
| Google Cloud Blog | 95.0% | 채택 |
| AWS Machine Learning Blog | 40.0% | 채택 |
| NVIDIA Blog | 22.2% | 채택 |
| Cloudflare Blog | 15.0% | 채택 |
| Hugging Face Blog | 10.0% | 제외 |
| LangChain Blog | 수집 0건 | 제외 |
| Microsoft AI Blog | 수집 0건 | 제외 |


### 3.3 최종 채택 소스

최종적으로 다음 4개 소스를 채택하였다.

- Google Cloud Blog
- AWS Machine Learning Blog
- NVIDIA Blog
- Cloudflare Blog

Google Cloud와 AWS는 AI Agent 및 Enterprise AI 관련성이 높았고,
NVIDIA는 Local AI와 AI Infrastructure 관점을 보완하였다.

Cloudflare는 MCP, 보안, 자동화 관련 주제를 보완하여
소스의 주제 다양성을 확보하기 위해 포함하였다.

Hugging Face는 RSS 자체는 안정적이었지만
관심 주제 적중률이 10%로 상대적으로 낮아 제외하였다.

LangChain Blog와 Microsoft AI Blog는 실험 당시
RSS 자동 수집 결과가 0건이었기 때문에
End-to-End 자동화의 안정성을 고려하여 제외하였다.

---

## 4. 예선 필터 개선

### 4.1 초기 문제

초기 키워드 필터는 단순 부분 문자열 검색 방식으로 구현하였다.

그러나 실제 테스트 과정에서 NVIDIA의 일반 기사에 포함된
`WARDOGS`라는 문자열 내부의 `rag`가 관심 키워드 RAG로
잘못 인식되는 False Positive를 발견하였다.

즉 다음과 같은 문제가 발생하였다.

`WARDOGS` → `rag` 포함으로 잘못 판정


### 4.2 개선 방법

단순 문자열 포함 검색 대신
**정규식의 단어 경계(word boundary)**를 사용하도록 수정하였다.

개선 후:

- `New RAG system` → RAG 탐지
- `WARDOGS` → RAG로 탐지하지 않음
- `multi-agent workflow` → agent, workflow, multi-agent 탐지

이를 통해 예선 단계에서 발생하는 키워드 오탐을 줄였다.

이 실험을 통해 단순히 LLM에 모든 판단을 맡기기보다
명확한 규칙으로 해결할 수 있는 부분은
Python 코드로 처리하는 것이 안정적임을 확인하였다.

---

## 5. 자료 선별 로직

자료 선별은 비용과 정확성을 고려하여
**예선 + 본선의 2단계 구조**로 설계하였다.


### 5.1 예선: 코드 기반 Prefilter

수집된 기사 전체를 바로 LLM에 전달하지 않고
먼저 관심 키워드가 포함된 기사만 통과시켰다.

주요 관심 키워드는 다음과 같다.

- AI Agent
- Agentic AI
- LangGraph
- MCP
- Model Context Protocol
- Automation
- Workflow
- RAG
- Local LLM
- Document AI
- Tool Use
- Multi-Agent

실제 실행에서는:

**78개 수집 → 34개 예선 통과**

즉 전체 기사의 약 43.6%만 LLM 본선 평가 대상으로 전달되었다.

이를 통해 불필요한 LLM 호출 비용을 줄이고
평가 대상의 주제 관련성을 높였다.


### 5.2 본선: LLM 기반 Ranking

예선을 통과한 기사에 대해 LLM이 다음 기준으로 평가하였다.

| 평가 기준 | 배점 |
|---|---:|
| 실무 활용성 | 0~5 |
| AI Agent 관련성 | 0~5 |
| 새로움 | 0~3 |
| 영향력 | 0~3 |
| 신뢰도 | 0~2 |
| 합계 | 18점 |

총점 기준으로 정렬한 뒤 최종 TOP 5 기사를 선정하였다.


### 5.3 LLM 산술 오류 방지

LLM은 각 항목의 의미적 점수만 판단하도록 하고
총점 계산은 Python 코드에서 다시 수행하였다.

즉:

**정성적 의미 판단 → LLM**

**결정적 계산 및 검증 → Python**

으로 역할을 분리하였다.

이를 통해 LLM의 단순 산술 오류가
최종 기사 순위에 영향을 주지 않도록 설계하였다.

---

## 6. 본문 확인 및 요약·인사이트 생성

최종 선정된 기사에 대해서는 RSS의 짧은 설명만 사용하지 않고
실제 기사 본문을 다시 수집하였다.

본문에서 script, style, nav, footer 등의 불필요한 요소를 제거한 뒤
LLM이 원문을 근거로 뉴스레터 콘텐츠를 생성하도록 하였다.

각 기사는 다음 4단계 구조로 가공된다.

### 📰 (요약) 무슨 일이 있었나?

원문에서 확인 가능한 사실을 2~3문장으로 요약한다.

### 💡 왜 중요한가?

해당 기술이나 사건이 AI 및 업무자동화 흐름에서
어떤 의미를 가지는지 해석한다.

### 🏢 실무자에게는?

비개발자와 일반 업무 담당자의 관점에서
실제 업무에 어떤 영향을 줄 수 있는지 설명한다.

### 🛠 오늘 적용해 볼 것

독자가 실제로 테스트하거나 적용할 수 있는
구체적인 행동 아이디어를 한 가지 제안한다.

따라서 본 프로젝트는 단순 기사 요약에서 그치지 않고
**사실 요약 → 중요성 해석 → 독자 업무 관점 → 실행 제안**의
4단계 정보 가공 구조를 적용하였다.

---

## 7. 자동 검수

LLM이 생성한 문장은 자연스럽더라도
원문에 없는 내용을 추가하는 Hallucination이 발생할 수 있다.

이를 방지하기 위해 검수 단계를 두 단계로 설계하였다.


### 7.1 1차: Python 코드 검수

다음 항목을 코드로 확인한다.

- 필수 필드 존재 여부
- 기사 본문 존재 여부
- 원문 URL 존재 여부
- 생성 결과의 기본 형식


### 7.2 2차: LLM 의미 검수

원문과 생성 결과를 함께 제공하고 다음 오류를 검사한다.

- unsupported_claim: 원문에 없는 주장
- number_error: 숫자 또는 날짜 오류
- entity_error: 고유명사 오류
- meaning_distortion: 의미 왜곡
- fact_insight_confusion: 사실과 해석의 혼동

---

## 8. Fault Injection 검증

검수 노드가 실제 오류를 잡는지 확인하기 위해
의도적으로 정상 요약문에 잘못된 정보를 삽입하는
**Fault Injection Test**를 수행하였다.

정상 원문의 GA 날짜:

**2026-06-01**

테스트를 위해 이를 다음과 같이 변경하였다.

**2027-12-31**

검수 결과:

**FAIL / number_error**

검수기는 원문의 정확한 날짜인 2026-06-01을 근거로
변조된 날짜가 잘못되었음을 탐지하였다.

정상 데이터는 PASS, 변조 데이터는 FAIL 처리됨을 확인하여
검수 노드가 단순 형식 검사가 아니라
원문 근거 기반의 의미·수치 검증을 수행함을 확인하였다.

---

## 9. 예외 처리 및 Fail-safe

하나의 기사 오류 때문에 전체 뉴스레터가 중단되지 않도록
다음과 같은 예외 처리 구조를 적용하였다.

**PASS → 최종 발행 대상 포함**

**FAIL → 문제 내용을 전달하여 1회 자동 재작성**

**재작성 → 다시 코드 검수 + LLM 검수**

**2차 PASS → 발행**

**2차 FAIL → 해당 기사만 SKIP**

즉 검수 실패가 전체 서비스 실패로 이어지지 않도록 설계하였다.

실제 최종 실행에서는 모든 기사 품질이 정상으로 판정되어
Retry Count는 0회였다.

그러나 Fault Injection Test를 통해
FAIL 탐지 기능이 실제 작동함을 별도로 검증하였다.

---

## 10. 최종 뉴스레터 발행

검수를 통과한 기사만 HTML 뉴스레터로 구성하였다.

각 기사는 연노랑, 연초록, 연파랑, 연보라, 연주황의
파스텔 카드 형태로 구분하여 가독성을 높였다.

최종 뉴스레터는 Gmail SMTP를 이용해 실제 이메일로 발행하였다.

API Key와 Gmail 앱 비밀번호는 코드에 직접 저장하지 않고
Secret 또는 환경변수로 관리하도록 구성하였다.

---

## 11. End-to-End 실행 결과

최종 전체 파이프라인 실행 결과는 다음과 같다.

| 항목 | 결과 |
|---|---:|
| Collected | 78 |
| Normalized | 78 |
| Prefiltered | 34 |
| Ranked | 34 |
| Selected | 5 |
| Validated | 5 |
| Skipped | 0 |
| Retry Count | 0 |
| Publish Result | SUCCESS |

실행 흐름:

**78개 수집 → 34개 예선 통과 → 34개 LLM 평가 → TOP 5 선정
→ 5개 본문 분석 → 5개 검수 PASS → 이메일 발행 SUCCESS**

이를 통해 Collect부터 Publish까지
전체 End-to-End 파이프라인이 정상 작동함을 확인하였다.

실행 기록은 `store/metrics.jsonl`에 저장하였다.

최종 HTML 결과는 `output/newsletter.html`에 저장하였다.

---

## 12. 자동 실행

GitHub Actions Workflow를 구성하여
**매일 오전 8시(Asia/Seoul)** 뉴스레터가 자동 실행되도록 설계하였다.

GitHub Secrets에는 다음 값을 저장한다.

- OPENAI_API_KEY
- EMAIL_ADDRESS
- EMAIL_APP_PASSWORD

따라서 민감정보를 GitHub 코드에 직접 노출하지 않고
자동 실행할 수 있도록 구성하였다.

---

## 13. 프로젝트 파일 구조

my-ai-work-radar/
├── state.py
├── nodes.py
├── graph.py
├── run.py
├── requirements.txt
├── README.md
├── REPORT.md
├── store/
│   └── metrics.jsonl
├── output/
│   └── newsletter.html
└── .github/
    └── workflows/
        └── daily-newsletter.yml

---

## 14. 평가 기준과 구현 대응

| 평가 요소 | 구현 및 증거 |
|---|---|
| 3개 이상 자료 수집 경로 | Google Cloud, AWS, NVIDIA, Cloudflare 4개 소스 |
| 소스 선정 근거 | 실제 RSS 수집 및 관심 키워드 적중률 측정 |
| 명확한 선별 기준 | 코드 예선 + 18점 LLM 본선 평가 |
| 선별 근거 기록 | score 및 selected 결과 기록 |
| 원문 기반 요약 | 최종 기사 본문을 직접 수집하여 생성 |
| 독자 맞춤 인사이트 | Meaning, Relevance, Action 구조 |
| 자동 검수 | Python + LLM Hybrid Validation |
| 오류 탐지 검증 | 날짜 변조 Fault Injection → number_error 탐지 |
| 예외 처리 | FAIL → 1회 재작성 → 재검수 → SKIP |
| E2E 실행 | 78 → 34 → 5 → 5 → Publish SUCCESS |
| 실행 증거 | metrics.jsonl 및 newsletter.html |
| 최종 발행 | Gmail 실제 이메일 수신 성공 |

---

## 15. 프로젝트 회고

이번 프로젝트에서 가장 중요하게 배운 점은
AI Agent를 단순히 LLM을 여러 번 호출하는 프로그램으로
구성해서는 안 된다는 점이었다.

명확한 규칙으로 처리할 수 있는 부분은 Python 코드가 담당하고,
문맥과 의미 판단이 필요한 부분은 LLM이 담당하도록
역할을 분리하는 것이 중요했다.

특히 키워드 False Positive, LLM 산술 오류 가능성,
Hallucination 검수와 같은 문제를 실제 테스트 과정에서 발견하고
이를 코드와 검수 구조로 개선하였다.

또한 정상 데이터만 실행해 보는 것에서 그치지 않고
의도적으로 잘못된 날짜를 삽입하는 Fault Injection Test를 통해
검수 기능이 실제 오류를 탐지하는지 확인하였다.

향후에는 다음 기능을 추가할 수 있다.

- 동일 출처 기사 편중 방지를 위한 Source Diversity 제약
- 독자 피드백을 반영한 개인화 Ranking
- 기사별 관심도 학습
- 다양한 발행 채널 지원
- 장기 Metrics 분석 및 품질 모니터링

My AI Work Radar는 AI 뉴스를 단순히 읽고 요약하는 것을 넘어
**실무자가 이해하고, 의미를 판단하고, 실제 행동으로 옮길 수 있도록
정보를 가공하는 AI Agent**를 목표로 설계하였다.