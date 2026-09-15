
from graph import graph


def main():
    print("🚀 My AI Work Radar 실행 시작")
    print("=" * 65)

    final_result = graph.invoke({})

    print()
    print("=" * 65)
    print("🎉 전체 파이프라인 실행 완료")
    print(f"📥 수집: {len(final_result['raw_articles'])}개")
    print(f"🎯 최종 선정: {len(final_result['selected_articles'])}개")
    print(f"✅ 검수 통과: {len(final_result['validated_articles'])}개")
    print(f"⏭️ 제외: {len(final_result['failed_articles'])}개")
    print(f"🔄 재작성: {final_result['retry_count']}회")
    print(f"📧 발행 결과: {final_result['publish_result']}")


if __name__ == "__main__":
    main()
