"""AI 自习室模块：财务测算、排座、签到与学情周报。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from src.cli import main as cli_main
from src.main import load_config, run_pipeline
from src.studyroom.checkin import load_checkins
from src.studyroom.finance import calculate_scenario, load_scenarios, render_finance_report
from src.studyroom.planner import plan_sessions, primary_weakness
from src.studyroom.weekly_report import parse_week_start, render_weekly_report, write_weekly_reports
from src.analyzer import analyze_knowledge_mastery
from src.cleaner import clean_dataset
from src.data_loader import load_dataset
from src.profiler import build_student_profiles

ENGINE_ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ENGINE_ROOT / "data" / "sample"
CONFIG = ENGINE_ROOT / "config.yaml"


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG)


@pytest.fixture(scope="module")
def cleaned(config):
    return clean_dataset(load_dataset(SAMPLE, config), config)


@pytest.fixture(scope="module")
def mastery(cleaned, config):
    profiles = build_student_profiles(
        cleaned["students"],
        cleaned["scores"],
        answers=cleaned["answers"],
        exams=cleaned["exams"],
    )
    return analyze_knowledge_mastery(
        profiles,
        answers=cleaned["answers"],
        exams=cleaned["exams"],
        config=config,
    )


def test_finance_formula_with_known_inputs():
    result = calculate_scenario(
        {
            "seats": 50,
            "utilization": 0.70,
            "monthly_fee": 1800,
            "renewal_rate": 0.80,
            "rent": 12000,
            "labor": 22000,
            "equipment_amortization": 3500,
            "startup_cost": 250000,
        },
        key="neutral",
    )
    assert result.monthly_cost == 37500
    assert result.revenue_by_utilization == 63000
    assert result.revenue_steady == 50400
    assert result.profit_by_utilization == 25500
    assert result.profit_steady == 12900
    assert result.payback_months_by_utilization == 9.8
    assert result.payback_months_steady == 19.4
    assert result.annual_profit_steady == 12900 * 12
    assert result.label == "中性"


def test_finance_unprofitable_has_no_payback():
    result = calculate_scenario(
        {
            "seats": 10,
            "utilization": 0.2,
            "monthly_fee": 1000,
            "renewal_rate": 0.5,
            "rent": 20000,
            "labor": 20000,
            "equipment_amortization": 5000,
            "startup_cost": 100000,
        },
        key="conservative",
    )
    assert result.profit_steady < 0
    assert result.payback_months_steady is None
    text = render_finance_report([result])
    assert "按当前假设无法回本" in text
    assert "假设参数" in text


def test_finance_rejects_invalid_rates():
    base = {
        "seats": 10,
        "utilization": 0.5,
        "monthly_fee": 1000,
        "renewal_rate": 0.8,
        "rent": 1,
        "labor": 1,
        "equipment_amortization": 1,
        "startup_cost": 1,
    }
    with pytest.raises(ValueError, match="利用率"):
        calculate_scenario({**base, "utilization": 1.2})
    with pytest.raises(ValueError, match="续费率"):
        calculate_scenario({**base, "renewal_rate": -0.1})
    with pytest.raises(ValueError, match="缺少参数"):
        calculate_scenario({"seats": 1})


def test_default_scenarios_ordering_and_spread(config):
    results = load_scenarios(config)
    labels = [item.label for item in results]
    assert labels == ["保守", "中性", "乐观"]
    by_label = {item.label: item for item in results}
    assert by_label["保守"].profit_steady < by_label["中性"].profit_steady
    assert by_label["中性"].profit_steady < by_label["乐观"].profit_steady
    assert by_label["保守"].profit_steady < 0
    assert by_label["保守"].payback_months_steady is None
    assert by_label["中性"].payback_months_steady == 19.4
    assert by_label["乐观"].payback_months_steady == 2.4


def test_sample_checkins_are_synthetic_and_complete():
    readme = (SAMPLE / "README.md").read_text(encoding="utf-8")
    assert "示例数据" in readme or "SYNTHETIC" in readme
    assert (SAMPLE / "checkins.csv").exists()
    records = load_checkins(SAMPLE)
    assert len(records) == 32
    ids = {item.student_id for item in records}
    assert ids == {f"S00{i}" for i in range(1, 9)}
    # 同一场次座位不冲突
    seats = [(item.date, item.slot_id, item.seat_id) for item in records]
    assert len(seats) == len(set(seats))
    absences = [item for item in records if not item.attended]
    assert len(absences) == 3
    assert all(item.duration_minutes == 0 for item in absences)
    week_start = parse_week_start(None, records)
    assert week_start == date(2026, 11, 2)


def test_planner_assigns_unique_seats_and_groups_by_weak_subject(cleaned, mastery, config):
    assignments = plan_sessions(cleaned["students"], mastery, config)
    sessions_per_week = config["studyroom"]["sessions_per_week"]
    assert len(assignments) == 8 * sessions_per_week
    keys = [(item.weekday, item.slot_id, item.seat_id) for item in assignments]
    assert len(keys) == len(set(keys))
    per_student = {}
    for item in assignments:
        per_student.setdefault(item.student_id, []).append(item)
    assert all(len(items) == sessions_per_week for items in per_student.values())

    science = {"物理", "化学", "生物"}
    arts = {"历史", "地理", "政治"}
    for item in assignments:
        if item.subject_focus in science:
            assert item.zone == "理科辅导区"
            assert item.seat_id.startswith("R")
        elif item.subject_focus in arts:
            assert item.zone == "文科辅导区"
            assert item.seat_id.startswith("W")

    s003_subject, s003_point = primary_weakness(
        next(s for s in cleaned["students"] if s.student_id == "S003"),
        mastery["S003"],
    )
    assert s003_point == "动能定理"
    assert s003_subject == "物理"
    assert all(
        item.subject_focus == "物理" and item.knowledge_point == "动能定理"
        for item in per_student["S003"]
    )


def test_weekly_report_has_attendance_and_no_private_fields(cleaned, mastery, config):
    checkins = load_checkins(SAMPLE)
    student = next(s for s in cleaned["students"] if s.student_id == "S001")
    assignments = plan_sessions(cleaned["students"], mastery, config)
    text = render_weekly_report(
        student=student,
        week_start=date(2026, 11, 2),
        checkins=checkins,
        mastery_rows=mastery["S001"],
        assignments=assignments,
    )
    assert "S001" in text
    assert "学情周报" in text
    assert "应到 4 次" in text
    assert "实到 3 次" in text
    assert "未到" in text
    assert "2026-11-02" in text
    assert "私人信息" in text
    for forbidden in ("不应出现", "138", "身份证", "手机号", "家长电话"):
        assert forbidden not in text


def test_write_weekly_reports_and_finance_via_cli(tmp_path, cleaned, config):
    output = tmp_path / "output"
    checkins = load_checkins(SAMPLE)
    assignments = plan_sessions(cleaned["students"], None, config)
    result = write_weekly_reports(
        students=cleaned["students"],
        checkins=checkins,
        output_dir=output,
        week_start=date(2026, 11, 2),
        assignments=assignments,
    )
    assert result["count"] == 8
    assert result["summary"].exists()
    summary = result["summary"].read_text(encoding="utf-8")
    assert "S006" in summary
    assert "学情周报汇总" in summary
    for i in range(1, 9):
        path = output / "studyroom" / "weekly" / f"S00{i}_学情周报.md"
        assert path.exists(), path

    code = cli_main(
        [
            "all",
            "--data",
            str(SAMPLE),
            "--out",
            str(output / "all"),
            "--config",
            str(CONFIG),
            "--week-start",
            "2026-11-04",
        ]
    )
    assert code == 0
    root = output / "all"
    assert (root / "教师审核摘要.md").exists()
    assert (root / "students" / "S001.md").exists()
    finance = (root / "studyroom" / "单店测算.md").read_text(encoding="utf-8")
    assert "保守" in finance and "中性" in finance and "乐观" in finance
    assert "19,008 元" in finance or "19008" in finance
    assert (root / "studyroom" / "座位与场次安排.md").exists()
    assert (root / "studyroom" / "weekly" / "S001_学情周报.md").exists()
    # week-start 2026-11-04 应归一到周一 2026-11-02
    report = (root / "studyroom" / "weekly" / "S001_学情周报.md").read_text(encoding="utf-8")
    assert "2026-11-02 至 2026-11-08" in report


def test_existing_generate_entry_still_works(tmp_path):
    output = tmp_path / "legacy"
    result = run_pipeline(SAMPLE, output, CONFIG)
    assert result["count"] == 8
