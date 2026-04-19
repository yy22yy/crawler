from __future__ import annotations

"""LangGraph-style task3 workflow demo.

This file shows how the task3 plan-and-execute workflow maps to LangGraph.
If LangGraph is not installed, the file will still remain readable and the
fallback message explains what to install.
"""

from typing import Any, Dict, TypedDict


class CrawlState(TypedDict, total=False):
    city: str
    page_html: str
    screenshot_path: str
    strategy: str
    result: Dict[str, Any]
    validated: bool
    attempt: int
    error: str


REQUIRED_FIELDS = ["竞得人", "成交总价", "成交时间", "宗地编号", "宗地位置", "土地用途", "用地面积"]


def load_city_profile(city: str) -> Dict[str, Any]:
    profiles = {
        "中山市": {"preferred_strategy": "normal_dom"},
        "江门市": {"preferred_strategy": "ocr"},
        "佛山市": {"preferred_strategy": "llm"},
    }
    return profiles.get(city, {"preferred_strategy": "normal_dom"})


def plan_node(state: CrawlState) -> CrawlState:
    profile = load_city_profile(state["city"])
    state["strategy"] = profile["preferred_strategy"]
    return state


def dom_node(state: CrawlState) -> CrawlState:
    state["attempt"] = 1
    # Demo: return empty result to force fallback.
    state["result"] = {}
    return state


def ocr_node(state: CrawlState) -> CrawlState:
    state["attempt"] = 2
    state["result"] = {
        "竞得人": "",
        "成交总价": "1000万元",
        "成交时间": "2026-04-19 10:00:00",
        "宗地编号": "",
        "宗地位置": "广东省示例地块",
        "土地用途": "住宅用地",
        "用地面积": "10000平方米",
    }
    return state


def llm_node(state: CrawlState) -> CrawlState:
    state["attempt"] = 3
    state["result"] = {
        "竞得人": "示例竞得人有限公司",
        "成交总价": "1000万元",
        "成交时间": "2026-04-19 10:00:00",
        "宗地编号": "GZ-2026-001",
        "宗地位置": "广东省示例地块",
        "土地用途": "住宅用地",
        "用地面积": "10000平方米",
    }
    return state


def validate_node(state: CrawlState) -> CrawlState:
    result = state.get("result", {})
    valid = True
    for field_name in REQUIRED_FIELDS:
        value = result.get(field_name)
        if value is None or str(value).strip() == "":
            valid = False
            break
    state["validated"] = valid
    return state


def route_after_validate(state: CrawlState) -> str:
    if state.get("validated"):
        return "end"
    if state.get("attempt") == 1:
        return "ocr"
    if state.get("attempt") == 2:
        return "llm"
    return "end"


def build_graph():
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        raise SystemExit(
            "LangGraph is not installed. Install it with: pip install langgraph"
        )

    graph = StateGraph(CrawlState)
    graph.add_node("plan", plan_node)
    graph.add_node("dom", dom_node)
    graph.add_node("ocr", ocr_node)
    graph.add_node("llm", llm_node)
    graph.add_node("validate", validate_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "dom")
    graph.add_edge("dom", "validate")
    graph.add_edge("ocr", "validate")
    graph.add_edge("llm", "validate")

    graph.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "ocr": "ocr",
            "llm": "llm",
            "end": END,
        },
    )

    return graph.compile()


def run_demo() -> None:
    app = build_graph()
    for city in ["中山市", "江门市", "佛山市"]:
        final_state = app.invoke({"city": city, "page_html": "<html></html>"})
        print("=" * 80)
        print(f"city: {city}")
        print(f"validated: {final_state.get('validated')}")
        print(f"strategy: {final_state.get('strategy')}")
        print(f"attempt: {final_state.get('attempt')}")
        print(f"result: {final_state.get('result')}")


if __name__ == "__main__":
    run_demo()
