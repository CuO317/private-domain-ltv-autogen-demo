from __future__ import annotations

import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts"
TRACE_PATH = ARTIFACTS / "workflow_trace.json"
LOG_PATH = ARTIFACTS / "terminal_run_log.txt"


@dataclass
class UserEvent:
    user_id: str
    event_type: str
    segment_hint: str
    days_since_last_purchase: int
    ltv: int
    points_expiring: int
    cart_value: int


@dataclass
class AgentDecision:
    agent: str
    action: str
    result: dict[str, Any]


class RunLogger:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def info(self, message: str) -> None:
        stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] {message}"
        self.lines.append(line)
        print(line)

    def save(self) -> None:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


class ProfileParserAgent:
    name = "ProfileParserAgent"

    def run(self, event: UserEvent) -> AgentDecision:
        churn_risk = min(0.95, 0.18 + event.days_since_last_purchase / 45)
        repurchase_score = min(0.98, 0.25 + event.ltv / 9000 + event.cart_value / 2000)
        segment = (
            "high_value_at_risk"
            if event.ltv >= 3000 and churn_risk > 0.55
            else "growth_potential"
            if repurchase_score > 0.65
            else event.segment_hint
        )
        return AgentDecision(
            self.name,
            "parse_profile",
            {
                "segment": segment,
                "churn_risk": round(churn_risk, 2),
                "repurchase_score": round(repurchase_score, 2),
            },
        )


class CopywriterAgent:
    name = "CopywriterAgent"

    def run(self, event: UserEvent, profile: dict[str, Any]) -> AgentDecision:
        if profile["segment"] == "high_value_at_risk":
            copy = "你常购的系列已补货，今晚为你保留专属权益，积分也可一并抵扣。"
        elif event.event_type == "browse_no_order":
            copy = "刚刚浏览的商品还在购物车，当前权益组合可在今天锁定。"
        elif event.points_expiring > 0:
            copy = f"你有 {event.points_expiring} 积分即将过期，可兑换专属复购礼。"
        else:
            copy = "为你更新了一组更适合当前需求的会员权益。"
        return AgentDecision(self.name, "generate_copy", {"message": copy, "tone": "brand-safe"})


class OfferMatcherAgent:
    name = "OfferMatcherAgent"

    def run(self, event: UserEvent, profile: dict[str, Any]) -> AgentDecision:
        if profile["churn_risk"] >= 0.65:
            offer = "15% retention coupon + 1v1 service reminder"
            timing = "within_15_minutes"
        elif event.points_expiring > 300:
            offer = "points redemption bundle + free shipping"
            timing = "same_day_evening"
        else:
            offer = "category coupon + product education content"
            timing = "next_best_hour"
        return AgentDecision(self.name, "match_offer", {"offer": offer, "timing": timing})


class PromptOptimizerAgent:
    name = "PromptOptimizerAgent"

    def run(self, conversion: bool, profile: dict[str, Any]) -> AgentDecision:
        reward = 1.0 if conversion else -0.25
        update = "increase urgency cue" if conversion else "reduce discount pressure"
        if profile["segment"] == "high_value_at_risk":
            update = "prioritize concierge tone and loyalty benefits"
        return AgentDecision(
            self.name,
            "optimize_prompt_policy",
            {"reward": reward, "policy_update": update},
        )


class OrchestratorAgent:
    name = "OrchestratorAgent"

    def __init__(self, logger: RunLogger) -> None:
        self.logger = logger
        self.profile_agent = ProfileParserAgent()
        self.copy_agent = CopywriterAgent()
        self.offer_agent = OfferMatcherAgent()
        self.optimizer_agent = PromptOptimizerAgent()

    def handle(self, event: UserEvent) -> dict[str, Any]:
        self.logger.info(f"{self.name} received event={event.event_type} user={event.user_id}")

        profile = self.profile_agent.run(event)
        self.logger.info(f"{profile.agent} -> {profile.result}")

        copy = self.copy_agent.run(event, profile.result)
        self.logger.info(f"{copy.agent} -> tone={copy.result['tone']} message=\"{copy.result['message']}\"")

        offer = self.offer_agent.run(event, profile.result)
        self.logger.info(f"{offer.agent} -> {offer.result}")

        conversion_probability = (
            0.16 + profile.result["repurchase_score"] * 0.45 - profile.result["churn_risk"] * 0.18
        )
        conversion = random.random() < conversion_probability
        self.logger.info(
            "LTVEngine dispatched touchpoint "
            f"strategy={offer.result['offer']} timing={offer.result['timing']} "
            f"converted={conversion}"
        )

        optimization = self.optimizer_agent.run(conversion, profile.result)
        self.logger.info(f"{optimization.agent} -> {optimization.result}")

        return {
            "event": asdict(event),
            "decisions": [
                asdict(profile),
                asdict(copy),
                asdict(offer),
                asdict(optimization),
            ],
            "conversion": conversion,
        }


def build_demo_events() -> list[UserEvent]:
    return [
        UserEvent("U10023", "browse_no_order", "beauty_member", 8, 1820, 120, 469),
        UserEvent("U10087", "points_expiring", "loyal_member", 18, 5120, 860, 0),
        UserEvent("U10156", "silent_21_days", "premium_member", 31, 7360, 240, 899),
        UserEvent("U10204", "cart_abandoned", "new_growth", 5, 620, 0, 329),
        UserEvent("U10281", "repeat_window", "mother_baby", 24, 2980, 320, 588),
    ]


def write_workflow_assets() -> None:
    docs = ROOT / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "workflow.mmd").write_text(
        """flowchart LR
    A[Realtime User Event] --> B[Orchestrator Agent]
    B --> C[ProfileParser Agent]
    B --> D[Copywriter Agent]
    B --> E[OfferMatcher Agent]
    C --> F[LTV Decision Engine]
    D --> F
    E --> F
    F --> G[Touchpoint Dispatch]
    G --> H[User Feedback]
    H --> I[PromptOptimizer Agent]
    I --> B
""",
        encoding="utf-8",
    )
    (docs / "agent_workflow.svg").write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="620" viewBox="0 0 1180 620">
  <rect width="1180" height="620" fill="#f7f8fb"/>
  <text x="46" y="58" font-family="Segoe UI, Arial" font-size="28" font-weight="700" fill="#172033">AutoGen-style Multi-Agent LTV Workflow</text>
  <text x="46" y="90" font-family="Segoe UI, Arial" font-size="15" fill="#5a6475">Simulation artifact: insight -> touchpoint -> conversion -> review</text>
  <g font-family="Segoe UI, Arial" font-size="15" fill="#172033">
    <rect x="48" y="145" width="190" height="84" rx="8" fill="#ffffff" stroke="#c9d1df"/>
    <text x="78" y="178" font-weight="700">Realtime Event</text>
    <text x="78" y="204" fill="#5a6475">browse, points, churn</text>
    <rect x="306" y="128" width="214" height="118" rx="8" fill="#e9f2ff" stroke="#7aa7e8"/>
    <text x="344" y="172" font-weight="700">Orchestrator Agent</text>
    <text x="338" y="199" fill="#35557d">global routing / policy</text>
    <rect x="594" y="104" width="220" height="72" rx="8" fill="#ffffff" stroke="#c9d1df"/>
    <text x="630" y="148" font-weight="700">ProfileParser Agent</text>
    <rect x="594" y="212" width="220" height="72" rx="8" fill="#ffffff" stroke="#c9d1df"/>
    <text x="640" y="256" font-weight="700">Copywriter Agent</text>
    <rect x="594" y="320" width="220" height="72" rx="8" fill="#ffffff" stroke="#c9d1df"/>
    <text x="628" y="364" font-weight="700">OfferMatcher Agent</text>
    <rect x="884" y="202" width="210" height="112" rx="8" fill="#eef8f0" stroke="#8ac69a"/>
    <text x="936" y="246" font-weight="700">LTV Engine</text>
    <text x="918" y="273" fill="#466b4d">risk + repurchase score</text>
    <rect x="884" y="390" width="210" height="86" rx="8" fill="#fff7e8" stroke="#e6b45e"/>
    <text x="915" y="426" font-weight="700">PromptOptimizer</text>
    <text x="924" y="452" fill="#806029">feedback reward loop</text>
  </g>
  <g stroke="#637083" stroke-width="2" fill="none" marker-end="url(#arrow)">
    <path d="M238 187 L306 187"/>
    <path d="M520 176 C560 138 560 140 594 140"/>
    <path d="M520 198 C560 236 560 248 594 248"/>
    <path d="M520 218 C560 326 560 356 594 356"/>
    <path d="M814 140 C852 160 860 204 884 234"/>
    <path d="M814 248 L884 258"/>
    <path d="M814 356 C850 338 862 300 884 278"/>
    <path d="M989 314 L989 390"/>
    <path d="M884 434 C760 526 388 526 413 246"/>
  </g>
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#637083"/>
    </marker>
  </defs>
</svg>
""",
        encoding="utf-8",
    )


def main() -> None:
    random.seed(42)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    write_workflow_assets()

    logger = RunLogger()
    orchestrator = OrchestratorAgent(logger)
    logger.info("Booting AutoGen-style private-domain LTV engine demo")
    logger.info("Loaded agents: Orchestrator, ProfileParser, Copywriter, OfferMatcher, PromptOptimizer")

    traces = []
    conversions = 0
    for event in build_demo_events():
        trace = orchestrator.handle(event)
        traces.append(trace)
        conversions += int(trace["conversion"])

    summary = {
        "processed_users": len(traces),
        "simulated_touchpoints": len(traces),
        "simulated_conversions": conversions,
        "estimated_manual_cost_reduction": "80% demo assumption",
        "estimated_high_value_repurchase_lift": "25% demo assumption",
    }
    logger.info(f"Review summary -> {summary}")
    logger.info(f"Workflow trace saved to {TRACE_PATH}")
    logger.info(f"Terminal log saved to {LOG_PATH}")

    TRACE_PATH.write_text(json.dumps({"summary": summary, "traces": traces}, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.save()


if __name__ == "__main__":
    main()

