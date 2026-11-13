"""AI 自习室运营模块：座位场次安排、签到、学情周报与单店财务测算。

AI study-room operations: seat/session planning, check-ins, weekly learning reports
and single-store financial estimates.
"""

from .checkin import Checkin, load_checkins
from .finance import ScenarioResult, calculate_scenario, render_finance_report, run_finance
from .planner import SeatAssignment, plan_sessions, render_plan_markdown
from .weekly_report import render_weekly_report, write_weekly_reports

__all__ = [
    "Checkin",
    "load_checkins",
    "ScenarioResult",
    "calculate_scenario",
    "render_finance_report",
    "run_finance",
    "SeatAssignment",
    "plan_sessions",
    "render_plan_markdown",
    "render_weekly_report",
    "write_weekly_reports",
]
