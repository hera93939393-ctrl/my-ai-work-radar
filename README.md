# 🤖 My AI Work Radar

AI Agent와 업무자동화에 관심 있는 실무자를 위한
**LangGraph 기반 맞춤형 AI 뉴스레터 에이전트**입니다.

여러 AI 기술 블로그에서 뉴스를 수집하고,
관심 주제와 실무 활용성을 기준으로 핵심 기사 5개를 선별합니다.

선별된 기사는 단순 요약에 그치지 않고 다음 구조로 가공됩니다.

**Fact → Meaning → Relevance → Action**

- 📰 (요약) 무슨 일이 있었나?
- 💡 왜 중요한가?
- 🏢 실무자에게는?
- 🛠 오늘 적용해 볼 것

## 🎯 Target Reader

- AI Agent를 배우고 있는 실무자
- 업무자동화에 관심 있는 실무자
- AI를 실제 업무에 적용하고 싶은 비개발자

## 📰 Data Sources

최종 채택 소스:

- Google Cloud Blog
- AWS Machine Learning Blog
- NVIDIA Blog
- Cloudflare Blog

후보 소스의 실제 수집 가능 여부와 관심 키워드 적중률을
측정한 뒤 최종 소스를 선정했습니다.

## 🔄 Pipeline

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

## 🛡 Validation & Fail-safe

검수는 두 단계로 수행합니다.

1. Python 코드 기반 형식 검증
2. LLM 기반 원문 의미 검증

**FAIL → 1회 자동 재작성 → 재검수**

재검수도 실패하면 해당 기사만 SKIP하여
하나의 기사 오류가 전체 뉴스레터 발행을 중단시키지 않도록 설계했습니다.

## 📊 Successful Run

실제 End-to-End 실행 결과:

- Collected: 78
- Normalized: 78
- Prefiltered: 34
- Ranked: 34
- Selected: 5
- Validated: 5
- Skipped: 0
- Retry Count: 0
- Publish: SUCCESS

## ⏰ Automation

GitHub Actions를 이용해
**매일 오전 8시 (Asia/Seoul)** 자동 실행하도록 구성했습니다.

## 📁 Project Structure

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

## 🔐 Environment Variables

실행 시 다음 Secret이 필요합니다.

- OPENAI_API_KEY
- EMAIL_ADDRESS
- EMAIL_APP_PASSWORD

API Key와 이메일 앱 비밀번호는 소스코드에 직접 저장하지 않습니다.

## 🚀 Run

pip install -r requirements.txt
python run.py

---

### 🤖 My AI Work Radar

**AI 뉴스를 읽는 것에서 끝내지 않고 실제 업무에 적용할 수 있는 행동으로 연결하는 뉴스레터 에이전트**