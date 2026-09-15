
from typing import TypedDict


class NewsState(TypedDict):
    # ① 자료 수집
    raw_articles: list
    normalized_articles: list

    # ② 자료 선별
    prefiltered_articles: list
    ranked_articles: list
    selected_articles: list

    # ③ 본문 확인 + 요약 + 인사이트
    article_contents: list
    summaries: list

    # ④ 자동 검수 / 예외 처리
    validated_articles: list
    failed_articles: list
    retry_count: int

    # ⑤ 최종 발행
    newsletter: str
    publish_result: str
