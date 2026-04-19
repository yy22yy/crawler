from __future__ import annotations

"""Task3 plan-and-execute workflow orchestrator demo.

This is a small, self-contained demo that shows the architecture discussed:
Plan -> DOM -> Validate -> OCR -> Validate -> LLM -> Validate.

It does not depend on LangGraph at runtime. The logic is intentionally written
as a clean state-machine / orchestrator skeleton so it can be swapped into a
real LangGraph StateGraph later with minimal changes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class PageStrategy(str, Enum):
    NORMAL_DOM = "normal_dom"
    OCR = "ocr"
    LLM = "llm"


@dataclass
class CrawlState:
    city: str
    page_html: str = ""
    screenshot_path: str = ""
    strategy: Optional[PageStrategy] = None
    result: Dict[str, Any] = field(default_factory=dict)
    validated: bool = False
    attempt: int = 0
    history: List[str] = field(default_factory=list)
    error: Optional[str] = None


REQUIRED_FIELDS = ["竞得人", "成交总价", "成交时间", "宗地编号", "宗地位置", "土地用途", "用地面积"]


class WorkflowOrchestrator:
    def __init__(self, city_profile_loader: Callable[[str], Dict[str, Any]]):
        self.city_profile_loader = city_profile_loader

    def run(self, state: CrawlState) -> CrawlState:
        state.history.append(f"start:{state.city}")

        state = self.plan_node(state)
        state = self.dom_node(state)
        state = self.validate_node(state)

        if state.validated:
            state.history.append("finish:dom")
            return state

        if state.attempt == 1:
            state = self.ocr_node(state)
            state = self.validate_node(state)
            if state.validated:
                state.history.append("finish:ocr")
                return state

        if state.attempt <= 2:
            state = self.llm_node(state)
            state = self.validate_node(state)
            if state.validated:
                state.history.append("finish:llm")
                return state

        state.history.append("finish:failed")
        return state

    def plan_node(self, state: CrawlState) -> CrawlState:
        profile = self.city_profile_loader(state.city)
        state.strategy = PageStrategy(profile.get("preferred_strategy", PageStrategy.NORMAL_DOM.value))
        state.history.append(f"plan:{state.strategy}")
        return state

    def dom_node(self, state: CrawlState) -> CrawlState:
        state.attempt = 1
        state.history.append("dom:try")
        state.result = self.try_dom_extract(state)
        return state

    def ocr_node(self, state: CrawlState) -> CrawlState:
        state.attempt = 2
        state.history.append("ocr:try")
        state.result = self.try_ocr_extract(state)
        return state

    def llm_node(self, state: CrawlState) -> CrawlState:
        state.attempt = 3
        state.history.append("llm:try")
        state.result = self.try_llm_extract(state)
        return state

    def validate_node(self, state: CrawlState) -> CrawlState:
        state.validated = self.check_fields(state.result)
        state.history.append(f"validate:{state.validated}")
        return state

    @staticmethod
    def check_fields(result: Dict[str, Any]) -> bool:
        if not result:
            return False
        for field_name in REQUIRED_FIELDS:
            value = result.get(field_name)
            if value is None or str(value).strip() == "":
                return False
        return True

    @staticmethod
    def try_dom_extract(state: CrawlState) -> Dict[str, Any]:
        # Demo only: return empty result when current city/page does not support DOM.
        # In real task3 this can call a normal Selenium DOM extractor.
        return {}

    @staticmethod
    def try_ocr_extract(state: CrawlState) -> Dict[str, Any]:
        # Demo only: pretend OCR extracted partial fields.
        # In real task3 this can call task3_tesseract.py logic.
        return {
            "竞得人": "",
            "成交总价": "1000万元",
            "成交时间": "2026-04-19 10:00:00",
            "宗地编号": "",
            "宗地位置": "广东省示例地块",
            "土地用途": "住宅用地",
            "用地面积": "10000平方米",
        }

    @staticmethod
    def try_llm_extract(state: CrawlState) -> Dict[str, Any]:
        # Demo only: pretend LLM repaired the missing fields.
        # In real task3 this can call task3_model.py logic.
        return {
            "竞得人": "示例竞得人有限公司",
            "成交总价": "1000万元",
            "成交时间": "2026-04-19 10:00:00",
            "宗地编号": "GZ-2026-001",
            "宗地位置": "广东省示例地块",
            "土地用途": "住宅用地",
            "用地面积": "10000平方米",
        }


def load_city_profile(city: str) -> Dict[str, Any]:
    # Demo config loader. Real version can read city_config.json.
    profiles = {
        "中山市": {"preferred_strategy": "normal_dom"},
        "江门市": {"preferred_strategy": "ocr"},
        "佛山市": {"preferred_strategy": "llm"},
    }
    return profiles.get(city, {"preferred_strategy": "normal_dom"})


def run_demo() -> None:
    orchestrator = WorkflowOrchestrator(load_city_profile)

    demo_cases = [
        CrawlState(city="中山市", page_html="<html>normal dom available</html>"),
        CrawlState(city="江门市", page_html="<html>shadow dom page</html>"),
        CrawlState(city="佛山市", page_html="<html>dom failed, llm fallback</html>"),
    ]

    for case in demo_cases:
        final_state = orchestrator.run(case)
        print("=" * 80)
        print(f"city: {final_state.city}")
        print(f"strategy: {final_state.strategy}")
        print(f"validated: {final_state.validated}")
        print(f"result: {final_state.result}")
        print(f"history: {' -> '.join(final_state.history)}")


if __name__ == "__main__":
    run_demo()
