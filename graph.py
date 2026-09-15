
from langgraph.graph import StateGraph, START, END

from state import NewsState
from nodes import (
    collect,
    normalize_and_dedupe,
    prefilter,
    rank,
    fetch_content,
    summarize,
    validate,
    compose,
    publish,
)


def build_graph():
    builder = StateGraph(NewsState)

    # 노드 등록
    builder.add_node("collect", collect)
    builder.add_node("normalize", normalize_and_dedupe)
    builder.add_node("prefilter", prefilter)
    builder.add_node("rank", rank)
    builder.add_node("fetch_content", fetch_content)
    builder.add_node("summarize", summarize)
    builder.add_node("validate", validate)
    builder.add_node("compose", compose)
    builder.add_node("publish", publish)

    # 실행 순서
    builder.add_edge(START, "collect")
    builder.add_edge("collect", "normalize")
    builder.add_edge("normalize", "prefilter")
    builder.add_edge("prefilter", "rank")
    builder.add_edge("rank", "fetch_content")
    builder.add_edge("fetch_content", "summarize")
    builder.add_edge("summarize", "validate")
    builder.add_edge("validate", "compose")
    builder.add_edge("compose", "publish")
    builder.add_edge("publish", END)

    return builder.compile()


graph = build_graph()
