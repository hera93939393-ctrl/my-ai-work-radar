
import os
import re
import json
import time
import smtplib
import feedparser
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from langchain_openai import ChatOpenAI

from state import NewsState


# ============================================
# Secret 가져오기
# Colab에서는 userdata, GitHub에서는 환경변수 사용
# ============================================

def get_secret(name):
    value = os.getenv(name)

    if value:
        return value

    try:
        from google.colab import userdata
        return userdata.get(name)
    except Exception:
        return None


OPENAI_API_KEY = get_secret("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-5-mini",
    api_key=OPENAI_API_KEY,
    temperature=0
)


# ============================================
# 뉴스 수집 소스
# ============================================

FINAL_SOURCES = [{'name': 'Google Cloud Blog', 'url': 'https://cloudblog.withgoogle.com/products/ai-machine-learning/rss/', 'role': 'Enterprise AI / Agent / RAG', 'match_rate': 95.0}, {'name': 'AWS Machine Learning Blog', 'url': 'https://aws.amazon.com/blogs/machine-learning/feed/', 'role': 'Enterprise AI / Agentic AI', 'match_rate': 40.0}, {'name': 'NVIDIA Blog', 'url': 'https://blogs.nvidia.com/feed/', 'role': 'Local AI / AI Infrastructure', 'match_rate': 22.2}, {'name': 'Cloudflare Blog', 'url': 'https://blog.cloudflare.com/rss/', 'role': 'MCP / Security / Automation', 'match_rate': 15.0}]


# ============================================
# 관심 키워드
# ============================================

INTEREST_KEYWORDS = ['agent', 'agentic', 'langgraph', 'mcp', 'model context protocol', 'automation', 'workflow', 'rag', 'local llm', 'document ai', 'tool use', 'multi-agent']

REQUIRED_FIELDS = [
    "korean_title",
    "what_happened",
    "why_important",
    "for_workers",
    "try_today",
]



def clean_html(text):
    """HTML 태그를 제거하고 일반 텍스트로 변환"""
    
    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")
    
    return soup.get_text(
        separator=" ",
        strip=True
    )


def find_keywords(text, keywords):
    text = text.lower()

    found = []

    for keyword in keywords:
        # 단어 경계 기반 검색
        pattern = rf"\b{re.escape(keyword.lower())}\b"

        if re.search(pattern, text):
            found.append(keyword)

    return found


def fetch_article_text(url):

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # 불필요한 요소 제거
        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside"
        ]):
            tag.decompose()

        # 우선 article 태그 탐색
        article_tag = soup.find("article")

        if article_tag:
            text = article_tag.get_text(
                separator=" ",
                strip=True
            )
        else:
            # article 태그가 없으면 전체 페이지 텍스트
            text = soup.get_text(
                separator=" ",
                strip=True
            )

        return text

    except Exception as e:

        print(
            f"⚠️ 본문 수집 실패: {url}"
        )
        print("   오류:", e)

        return ""


def code_validate_article(article):

    problems = []

    # ① 필수 필드 검사
    for field in REQUIRED_FIELDS:

        value = article.get(field, "")

        if not value or not value.strip():
            problems.append(
                f"필수 필드 누락: {field}"
            )

    # ② 원문 존재 여부
    if not article.get("content", "").strip():
        problems.append(
            "검수할 원문 본문이 없음"
        )

    # ③ URL 존재 여부
    if not article.get("url", "").strip():
        problems.append(
            "원문 URL이 없음"
        )

    # 문제가 없으면 PASS
    if len(problems) == 0:
        result = "PASS"
    else:
        result = "FAIL"

    return {
        "result": result,
        "problems": problems
    }


def llm_validate_article(article):

    prompt = f"""
너는 AI 뉴스레터의 엄격한 팩트체커다.

아래 원문과 뉴스레터 작성 결과를 비교하여 검수하라.

[검수 기준]

1. unsupported_claim
- 원문에 없는 사실을 사실처럼 추가했는가?

2. number_error
- 숫자, 날짜, 비율, 성능 수치 등이 원문과 다른가?

3. entity_error
- 회사명, 제품명, 기술명, 기관명 등 고유명사가 틀렸는가?

4. meaning_distortion
- 원문의 의미를 과장하거나 왜곡했는가?

5. fact_insight_confusion
- 해석이나 제안을 원문의 사실처럼 표현했는가?

[판정 원칙]

- what_happened는 원문 근거를 매우 엄격하게 검사한다.
- why_important와 for_workers는 합리적인 해석을 허용한다.
- try_today는 실행 제안이므로 원문에 없어도 된다.
- 단, 해석이나 제안이 원문 사실과 모순되면 문제다.
- 단순한 번역 표현 차이는 오류가 아니다.

실질적인 문제가 없으면 PASS,
하나라도 있으면 FAIL이다.

반드시 JSON 객체만 출력하라.

{{
    "result": "PASS 또는 FAIL",
    "problems": [
        {{
            "type": "오류 유형",
            "field": "문제가 발생한 필드",
            "description": "구체적인 문제"
        }}
    ]
}}

[원문]

{article['content'][:15000]}

[뉴스레터 작성 결과]

한국어 제목:
{article['korean_title']}

무슨 일이 있었나:
{article['what_happened']}

왜 중요한가:
{article['why_important']}

실무자에게는:
{article['for_workers']}

오늘 적용해 볼 것:
{article['try_today']}
"""

    response = llm.invoke(prompt)

    return json.loads(response.content)


def rewrite_article(article, problems):

    problems_text = json.dumps(
        problems,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
너는 'My AI Work Radar' 뉴스레터의 수정 에디터다.

팩트체커가 아래 뉴스레터에서 문제를 발견했다.

검수 결과를 반영하여 잘못된 부분을 수정하라.

[중요 규칙]

- 원문에 없는 사실을 새로 만들지 않는다.
- 숫자, 날짜, 회사명, 제품명은 원문과 일치시킨다.
- 기존 내용 중 문제가 없는 부분은 최대한 유지한다.
- what_happened는 원문에서 확인되는 사실만 작성한다.
- why_important와 for_workers는 합리적인 해석만 허용한다.
- try_today는 실행 제안으로 명확하게 작성한다.

반드시 아래 JSON 객체만 출력하라.

{{
    "korean_title": "",
    "what_happened": "",
    "why_important": "",
    "for_workers": "",
    "try_today": ""
}}

[팩트체커가 발견한 문제]

{problems_text}

[원문]

{article['content'][:15000]}

[기존 뉴스레터]

한국어 제목:
{article['korean_title']}

무슨 일이 있었나:
{article['what_happened']}

왜 중요한가:
{article['why_important']}

실무자에게는:
{article['for_workers']}

오늘 적용해 볼 것:
{article['try_today']}
"""

    response = llm.invoke(prompt)

    rewritten = json.loads(
        response.content
    )

    updated_article = article.copy()

    updated_article.update(rewritten)

    return updated_article


def collect(state: NewsState):

    raw_articles = []

    print("📡 뉴스 수집 시작")
    print("=" * 65)

    for source in FINAL_SOURCES:

        feed = feedparser.parse(source["url"])

        # 소스별 최신 20개까지만 수집
        entries = feed.entries[:20]

        print(
            f"📰 {source['name']}: "
            f"{len(entries)}개 수집"
        )

        for entry in entries:

            article = {
                "source": source["name"],
                "title": entry.get("title", ""),
                "url": entry.get(
                    "link",
                    entry.get("guid", "")
                ),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "")
            }

            raw_articles.append(article)

    print("=" * 65)
    print(f"📦 전체 수집 기사: {len(raw_articles)}개")

    return {
        "raw_articles": raw_articles
    }


def normalize_and_dedupe(state: NewsState):

    raw_articles = state["raw_articles"]

    normalized_articles = []

    # 중복 확인용
    seen_urls = set()
    seen_titles = set()

    removed_empty = 0
    removed_duplicate = 0

    print("🧹 기사 정규화 시작")
    print("=" * 65)

    for article in raw_articles:

        title = clean_html(article.get("title", "")).strip()
        url = article.get("url", "").strip()
        summary = clean_html(article.get("summary", "")).strip()

        # -----------------------------
        # ① 필수 데이터 없는 기사 제거
        # -----------------------------

        if not title or not url:
            removed_empty += 1
            continue

        # -----------------------------
        # ② 중복 기사 제거
        # URL 또는 제목이 같으면 중복 처리
        # -----------------------------

        normalized_title = title.lower()

        if (
            url in seen_urls
            or normalized_title in seen_titles
        ):
            removed_duplicate += 1
            continue

        seen_urls.add(url)
        seen_titles.add(normalized_title)

        # -----------------------------
        # ③ 정리된 기사 저장
        # -----------------------------

        normalized_articles.append({
            "source": article["source"],
            "title": title,
            "url": url,
            "published": article.get("published", ""),
            "summary": summary
        })

    print(f"원본 기사       : {len(raw_articles)}개")
    print(f"빈 데이터 제거  : {removed_empty}개")
    print(f"중복 제거       : {removed_duplicate}개")
    print(f"최종 기사       : {len(normalized_articles)}개")
    print("=" * 65)

    return {
        "normalized_articles": normalized_articles
    }


def prefilter(state: NewsState):

    articles = state["normalized_articles"]

    prefiltered_articles = []
    rejected_articles = []

    print("🔎 1차 기사 선별 시작")
    print("=" * 65)

    for article in articles:

        # 제목 + RSS 요약문을 함께 검사
        text = (
            article["title"]
            + " "
            + article["summary"]
        )

        # STEP 7에서 만든 개선형 키워드 함수
        found_keywords = find_keywords(
            text,
            INTEREST_KEYWORDS
        )

        if found_keywords:

            selected_article = article.copy()

            # 어떤 키워드 때문에 통과했는지 기록
            selected_article["matched_keywords"] = found_keywords
            selected_article["keyword_count"] = len(found_keywords)

            prefiltered_articles.append(
                selected_article
            )

        else:
            rejected_articles.append(article)

    print(f"정규화 기사       : {len(articles)}개")
    print(f"예선 통과         : {len(prefiltered_articles)}개")
    print(f"예선 탈락         : {len(rejected_articles)}개")

    if articles:
        pass_rate = (
            len(prefiltered_articles)
            / len(articles)
            * 100
        )
    else:
        pass_rate = 0

    print(f"예선 통과율       : {pass_rate:.1f}%")
    print("=" * 65)

    return {
        "prefiltered_articles": prefiltered_articles
    }


def rank(state: NewsState):

    articles = state["prefiltered_articles"]

    ranked_articles = []

    batch_size = 5

    print("🤖 LLM 본선 평가 시작")
    print("=" * 65)
    print(f"평가 대상 : {len(articles)}개")
    print(f"배치 크기 : {batch_size}개")

    for start in range(0, len(articles), batch_size):

        batch = articles[start:start + batch_size]

        articles_text = ""

        for local_id, article in enumerate(batch):

            articles_text += f"""
ARTICLE_ID: {local_id}
TITLE: {article['title']}
SOURCE: {article['source']}
SUMMARY: {article['summary'][:1500]}
---
"""

        prompt = f"""
너는 'My AI Work Radar' 뉴스레터의 뉴스 편집자다.

독자는 AI Agent와 업무자동화를 배우고 있으며,
개발자가 아니더라도 실제 업무에 AI를 적용하고 싶은 실무자다.

아래 기사들을 각각 평가하라.

[평가 기준]

1. practical_usefulness (0~5)
실제 업무에 적용하거나 아이디어를 얻는 데 얼마나 유용한가?

2. agent_relevance (0~5)
AI Agent, Agentic AI, MCP, RAG, workflow,
automation 등과 얼마나 직접적으로 관련되는가?

3. novelty (0~3)
새로운 기술, 기능, 사례 또는 변화가 있는가?

4. impact (0~3)
AI 활용 방식이나 업무자동화에 미칠 영향이 큰가?

5. credibility (0~2)
출처와 내용의 신뢰성이 높은가?

각 기사에 대해 한 문장의 평가 이유도 작성하라.

반드시 JSON 배열만 출력하라.
마크다운 코드블록은 사용하지 마라.

[
  {{
    "article_id": 0,
    "practical_usefulness": 0,
    "agent_relevance": 0,
    "novelty": 0,
    "impact": 0,
    "credibility": 0,
    "total": 0,
    "reason": "평가 이유"
  }}
]

평가할 기사:

{articles_text}
"""

        try:

            response = llm.invoke(prompt)

            evaluations = json.loads(
                response.content
            )

            for evaluation in evaluations:

                local_id = evaluation["article_id"]

                # 잘못된 ID 방지
                if local_id >= len(batch):
                    continue

                article = batch[local_id].copy()

                # --------------------------
                # Python이 총점 직접 계산
                # --------------------------

                calculated_total = (
                    evaluation["practical_usefulness"]
                    + evaluation["agent_relevance"]
                    + evaluation["novelty"]
                    + evaluation["impact"]
                    + evaluation["credibility"]
                )

                article.update({
                    "practical_usefulness":
                        evaluation["practical_usefulness"],

                    "agent_relevance":
                        evaluation["agent_relevance"],

                    "novelty":
                        evaluation["novelty"],

                    "impact":
                        evaluation["impact"],

                    "credibility":
                        evaluation["credibility"],

                    "total_score":
                        calculated_total,

                    "ranking_reason":
                        evaluation["reason"]
                })

                ranked_articles.append(article)

            print(
                f"✅ {start + 1}~"
                f"{start + len(batch)}번 기사 평가 완료"
            )

            # API 호출 간 짧은 간격
            time.sleep(1)

        except Exception as e:

            print(
                f"⚠️ {start + 1}~"
                f"{start + len(batch)}번 배치 실패:",
                e
            )

    # --------------------------
    # 점수 높은 순으로 정렬
    # --------------------------

    ranked_articles.sort(
        key=lambda x: x["total_score"],
        reverse=True
    )

    # 최종 TOP 5
    selected_articles = ranked_articles[:5]

    print("=" * 65)
    print(
        f"평가 완료 : {len(ranked_articles)}개"
    )
    print(
        f"최종 선정 : {len(selected_articles)}개"
    )

    return {
        "ranked_articles": ranked_articles,
        "selected_articles": selected_articles
    }


def fetch_content(state: NewsState):

    selected_articles = state[
        "selected_articles"
    ]

    article_contents = []

    print("🌐 TOP 5 기사 본문 수집 시작")
    print("=" * 65)

    for i, article in enumerate(
        selected_articles,
        1
    ):

        content = fetch_article_text(
            article["url"]
        )

        article_with_content = (
            article.copy()
        )

        # 너무 긴 본문은 이후 LLM 입력을 위해 제한
        article_with_content["content"] = (
            content[:15000]
        )

        article_with_content[
            "content_length"
        ] = len(content)

        article_contents.append(
            article_with_content
        )

        if content:
            status = "✅"
        else:
            status = "❌"

        print(
            f"{status} {i}. "
            f"{article['title'][:60]}"
        )

        print(
            f"   본문 길이: "
            f"{len(content):,}자"
        )

    return {
        "article_contents":
            article_contents
    }


def summarize(state: NewsState):

    articles = state["article_contents"]

    summaries = []

    print("🇰🇷 한국어 요약 및 인사이트 생성 시작")
    print("=" * 65)

    for i, article in enumerate(articles, 1):

        prompt = f"""
너는 'My AI Work Radar'의 뉴스레터 에디터다.

독자는 AI Agent와 업무자동화를 배우고 있으며,
개발자가 아니더라도 AI를 실제 업무에 적용하고 싶은 실무자다.

아래 영어 기사를 읽고 한국어 뉴스레터용 콘텐츠를 작성하라.

중요한 규칙:

1. korean_title
- 원문의 의미를 살린 자연스러운 한국어 제목
- 과장하거나 원문에 없는 사실을 추가하지 않는다.

2. what_happened
- 기사에서 실제로 확인되는 사실만 사용한다.
- 핵심 내용을 한국어 2~3문장으로 요약한다.
- 숫자, 회사명, 제품명 등은 원문과 정확히 일치해야 한다.

3. why_important
- 이 뉴스가 AI, AI Agent, 업무자동화 흐름에서
  왜 중요한지 2~3문장으로 설명한다.
- 사실과 해석을 혼동하지 않는다.

4. for_workers
- 비개발자 및 일반 업무 담당자의 관점에서
  이 뉴스가 어떤 의미가 있는지 2~3문장으로 설명한다.
- 지나친 기술 설명보다 실제 업무 관점을 우선한다.

5. try_today
- 독자가 오늘 직접 시험해볼 수 있는
  구체적인 행동 또는 아이디어를 1개 제안한다.
- 원문 사실이 아니라 '실행 제안'이라는 점이 명확해야 한다.

반드시 아래 JSON 객체만 출력하라.
마크다운 코드블록은 사용하지 마라.

{{
  "korean_title": "",
  "what_happened": "",
  "why_important": "",
  "for_workers": "",
  "try_today": ""
}}

[기사 정보]

원문 제목:
{article['title']}

출처:
{article['source']}

기사 본문:
{article['content'][:12000]}
"""

        try:

            response = llm.invoke(prompt)

            generated = json.loads(
                response.content
            )

            result = article.copy()

            result.update({
                "korean_title":
                    generated["korean_title"],

                "what_happened":
                    generated["what_happened"],

                "why_important":
                    generated["why_important"],

                "for_workers":
                    generated["for_workers"],

                "try_today":
                    generated["try_today"]
            })

            summaries.append(result)

            print(
                f"✅ {i}. "
                f"{generated['korean_title']}"
            )

        except Exception as e:

            print(
                f"❌ {i}. 요약 생성 실패"
            )
            print("   오류:", e)

    print("=" * 65)

    print(
        f"요약 완료 : "
        f"{len(summaries)}/{len(articles)}개"
    )

    return {
        "summaries": summaries
    }


def validate(state: NewsState):

    articles = state["summaries"]

    validated_articles = []
    failed_articles = []

    print("🛡️ 최종 자동 검수 시작")
    print("=" * 65)

    for i, article in enumerate(articles, 1):

        current_article = article.copy()

        print()
        print(f"📰 {i}. {current_article['korean_title']}")

        # --------------------------------
        # ① Python 코드 검수
        # --------------------------------
        code_result = code_validate_article(
            current_article
        )

        if code_result["result"] == "FAIL":

            print("   ❌ 코드 검수 FAIL")

            current_article["validation_result"] = "FAIL"
            current_article["validation_problems"] = (
                code_result["problems"]
            )
            current_article["retry_count"] = 0
            current_article["final_result"] = "SKIP"

            failed_articles.append(
                current_article
            )

            continue

        print("   ✅ 코드 검수 PASS")

        # --------------------------------
        # ② LLM 의미 검수
        # --------------------------------
        try:

            llm_result = llm_validate_article(
                current_article
            )

        except Exception as e:

            print("   ⚠️ LLM 검수 자체가 실패했습니다.")
            print("   오류:", e)

            current_article["validation_result"] = "ERROR"
            current_article["validation_problems"] = [
                str(e)
            ]
            current_article["retry_count"] = 0
            current_article["final_result"] = "SKIP"

            failed_articles.append(
                current_article
            )

            continue

        # --------------------------------
        # ③ 첫 검수 PASS
        # --------------------------------
        if llm_result["result"] == "PASS":

            print("   ✅ LLM 검수 PASS")

            current_article["validation_result"] = "PASS"
            current_article["validation_problems"] = []
            current_article["retry_count"] = 0
            current_article["final_result"] = "PASS"

            validated_articles.append(
                current_article
            )

            continue

        # --------------------------------
        # ④ 첫 검수 FAIL
        # --------------------------------
        print("   ❌ LLM 검수 FAIL")

        problems = llm_result.get(
            "problems",
            []
        )

        for problem in problems:
            print(
                "      ⚠️",
                problem.get(
                    "description",
                    problem
                )
            )

        print("   🔄 자동 재작성 1회 실행")

        # --------------------------------
        # ⑤ 문제 내용을 반영하여 재작성
        # --------------------------------
        try:

            rewritten_article = rewrite_article(
                current_article,
                problems
            )

        except Exception as e:

            print("   ⚠️ 재작성 실패:", e)

            current_article["validation_result"] = "FAIL"
            current_article["validation_problems"] = problems
            current_article["retry_count"] = 1
            current_article["final_result"] = "SKIP"

            failed_articles.append(
                current_article
            )

            continue

        # --------------------------------
        # ⑥ 재작성 결과 코드 검수
        # --------------------------------
        rewrite_code_result = code_validate_article(
            rewritten_article
        )

        if rewrite_code_result["result"] == "FAIL":

            print(
                "   ❌ 재작성 후 코드 검수 FAIL → SKIP"
            )

            rewritten_article["validation_result"] = "FAIL"
            rewritten_article["validation_problems"] = (
                rewrite_code_result["problems"]
            )
            rewritten_article["retry_count"] = 1
            rewritten_article["final_result"] = "SKIP"

            failed_articles.append(
                rewritten_article
            )

            continue

        # --------------------------------
        # ⑦ LLM 재검수
        # --------------------------------
        try:

            second_result = llm_validate_article(
                rewritten_article
            )

        except Exception as e:

            print(
                "   ⚠️ 재검수 오류 → SKIP:",
                e
            )

            rewritten_article["validation_result"] = "ERROR"
            rewritten_article["validation_problems"] = [
                str(e)
            ]
            rewritten_article["retry_count"] = 1
            rewritten_article["final_result"] = "SKIP"

            failed_articles.append(
                rewritten_article
            )

            continue

        # --------------------------------
        # ⑧ 재검수 결과
        # --------------------------------
        if second_result["result"] == "PASS":

            print(
                "   ✅ 재작성 후 검수 PASS"
            )

            rewritten_article["validation_result"] = "PASS"
            rewritten_article["validation_problems"] = problems
            rewritten_article["retry_count"] = 1
            rewritten_article["final_result"] = "PASS"

            validated_articles.append(
                rewritten_article
            )

        else:

            print(
                "   ❌ 재검수 FAIL → SKIP"
            )

            rewritten_article["validation_result"] = "FAIL"
            rewritten_article["validation_problems"] = (
                second_result.get(
                    "problems",
                    []
                )
            )
            rewritten_article["retry_count"] = 1
            rewritten_article["final_result"] = "SKIP"

            failed_articles.append(
                rewritten_article
            )

    print()
    print("=" * 65)
    print(
        f"✅ 최종 PASS : {len(validated_articles)}개"
    )
    print(
        f"⏭️ 최종 SKIP : {len(failed_articles)}개"
    )

    return {
        "validated_articles": validated_articles,
        "failed_articles": failed_articles,
        "retry_count": sum(
            article.get("retry_count", 0)
            for article in (
                validated_articles
                + failed_articles
            )
        )
    }


def compose(state: NewsState):

    articles = state["validated_articles"]

    today = datetime.now().strftime("%Y.%m.%d")

    # 기사별 파스텔 배경색
    pastel_colors = [
        "#FFF9D9",   # 1. 연노랑
        "#EAF8E8",   # 2. 연초록
        "#EAF4FF",   # 3. 연파랑
        "#F3ECFF",   # 4. 연보라
        "#FFF0E3",   # 5. 연주황
    ]

    article_blocks = ""

    for i, article in enumerate(articles, 1):

        score = article["total_score"]

        star_count = round(score / 18 * 5)
        stars = "⭐" * star_count

        # 기사 번호에 따라 배경색 지정
        bg_color = pastel_colors[
            (i - 1) % len(pastel_colors)
        ]

        article_blocks += f"""
        <div style="
            background-color:{bg_color};
            margin-bottom:28px;
            padding:30px;
            border-radius:16px;
            border:1px solid rgba(0,0,0,0.05);
        ">

            <div style="
                display:inline-block;
                background:#ffffff;
                padding:5px 10px;
                border-radius:20px;
                font-size:13px;
                font-weight:bold;
                color:#555555;
                margin-bottom:12px;
            ">
                NEWS {i:02d}
            </div>

            <h2 style="
                font-size:22px;
                line-height:1.45;
                margin:0 0 12px 0;
                color:#111111;
            ">
                {article['korean_title']}
            </h2>

            <div style="
                font-size:14px;
                color:#666666;
                margin-bottom:24px;
            ">
                {stars}
                &nbsp;
                <strong>{score}/18</strong>
                &nbsp; | &nbsp;
                {article['source']}
            </div>

            <div style="
                background:rgba(255,255,255,0.55);
                padding:18px;
                border-radius:12px;
                margin-bottom:14px;
            ">
                <h3 style="margin-top:0;">
                    📰 요약
                </h3>

                <p style="
                    line-height:1.75;
                    margin-bottom:0;
                ">
                    {article['what_happened']}
                </p>
            </div>

            <h3>
                💡 중요성
            </h3>

            <p style="line-height:1.75;">
                {article['why_important']}
            </p>

            <h3>
                🏢 시사점
            </h3>

            <p style="line-height:1.75;">
                {article['for_workers']}
            </p>

            <h3>
                🛠 실천안:)
            </h3>

            <p style="line-height:1.75;">
                {article['try_today']}
            </p>

            <div style="
                margin-top:22px;
            ">

                <a href="{article['url']}"
                   style="
                       display:inline-block;
                       background:#ffffff;
                       color:#2563eb;
                       text-decoration:none;
                       font-weight:bold;
                       padding:10px 16px;
                       border-radius:8px;
                   ">
                   🔗 원문 보기
                </a>

            </div>

        </div>
        """

    newsletter = f"""
    <!DOCTYPE html>

    <html>

    <body style="
        margin:0;
        padding:30px 10px;
        background:#f4f5f7;
        font-family:Arial, 'Noto Sans KR', sans-serif;
        color:#222222;
    ">

        <div style="
            max-width:720px;
            margin:0 auto;
            background:#ffffff;
            padding:40px;
            border-radius:18px;
        ">

            <div style="
                font-size:30px;
                font-weight:bold;
                margin-bottom:8px;
            ">
                🤖 MY AI WORK RADAR
            </div>

            <div style="
                color:#777777;
                margin-bottom:30px;
            ">
                {today}
            </div>

            <div style="
                background:#111111;
                color:#ffffff;
                padding:18px 20px;
                border-radius:12px;
                margin-bottom:30px;
                font-size:20px;
                font-weight:bold;
            ">
                🔥 오늘 꼭 볼 AI 소식 {len(articles)}
            </div>

            {article_blocks}

            <div style="
                margin-top:35px;
                padding-top:20px;
                border-top:1px solid #eeeeee;
                color:#999999;
                font-size:12px;
                text-align:center;
                line-height:1.7;
            ">
                🤖 My AI Work Radar<br>
                AI Agent · 업무자동화 맞춤형 뉴스레터
            </div>

        </div>

    </body>
    </html>
    """

    print(
        f"🎨 파스텔 뉴스레터 생성 완료: "
        f"{len(articles)}개 기사"
    )

    return {
        "newsletter": newsletter
    }


def publish(state: NewsState):

    newsletter = state["newsletter"]

    # Colab Secrets에서 가져오기
    email_address = get_secret("EMAIL_ADDRESS")
    email_app_password = get_secret("EMAIL_APP_PASSWORD")

    # 보내는 주소 = 받는 주소
    to_email = email_address

    today = datetime.now().strftime("%Y.%m.%d")
    subject = f"🤖 My AI Work Radar | {today}"

    print("📧 뉴스레터 이메일 발송 시작")
    print("=" * 65)

    try:
        # 이메일 만들기
        message = MIMEMultipart("alternative")

        message["Subject"] = subject
        message["From"] = email_address
        message["To"] = to_email

        # HTML 뉴스레터 넣기
        html_part = MIMEText(
            newsletter,
            "html",
            "utf-8"
        )

        message.attach(html_part)

        # Gmail로 발송
        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as server:

            server.login(
                email_address,
                email_app_password
            )

            server.sendmail(
                email_address,
                to_email,
                message.as_string()
            )

        print("✅ 이메일 발송 성공")
        print(f"📨 수신 주소: {to_email}")
        print(f"📰 제목: {subject}")

        publish_result = "SUCCESS"

    except Exception as e:

        print("❌ 이메일 발송 실패")
        print("오류:", e)

        publish_result = "FAIL"

    return {
        "publish_result": publish_result
    }
