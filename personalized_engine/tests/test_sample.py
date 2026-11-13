"""针对示例数据与核心规则的测试。 / Tests for the sample data and core rules."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.analyzer import analyze_knowledge_mastery
from src.cleaner import clean_dataset, subjects_from_track
from src.data_loader import (
    drop_private_student_fields,
    load_dataset,
    load_students,
    parse_bool,
)
from src.exporter import export_to_markdown
from src.generator import (
    LLMGenerator,
    MaterialGenerator,
    RuleBasedGenerator,
    get_generator,
    layer_for,
)
from src.main import load_config, run_pipeline
from src.profiler import build_student_profiles

ENGINE_ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ENGINE_ROOT / "data" / "sample"
CONFIG = ENGINE_ROOT / "config.yaml"


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG)


@pytest.fixture(scope="module")
def cleaned(config):
    raw = load_dataset(SAMPLE, config)
    return clean_dataset(raw, config)


def test_sample_files_exist_and_labeled_synthetic():
    readme = (SAMPLE / "README.md").read_text(encoding="utf-8")
    assert "示例数据" in readme or "SYNTHETIC" in readme
    for name in ("students.csv", "scores.csv", "answers.csv", "question_bank.csv", "exams.csv"):
        assert (SAMPLE / name).exists(), name


def test_sample_has_eight_students_and_two_tracks(cleaned):
    students = cleaned["students"]
    assert len(students) == 8
    tracks = {s.subject_track for s in students}
    assert "物化生" in tracks
    assert "史地生" in tracks
    ids = {s.student_id for s in students}
    assert ids == {f"S00{i}" for i in range(1, 9)}


def test_loader_drops_private_columns(tmp_path, config):
    path = tmp_path / "students.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "student_id",
                "name",
                "phone",
                "id_card",
                "grade",
                "class_name",
                "subject_track",
                "subjects",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "student_id": "S999",
                "name": "不应出现",
                "phone": "00000000000",
                "id_card": "000000",
                "grade": "高二",
                "class_name": "1班",
                "subject_track": "物化生",
                "subjects": "物理,化学,生物",
            }
        )
    dropped = drop_private_student_fields(
        {
            "student_id": "S999",
            "name": "不应出现",
            "phone": "00000000000",
            "grade": "高二",
            "class_name": "1班",
            "subject_track": "物化生",
            "subjects": "物理,化学,生物",
        },
        config,
    )
    assert "name" not in dropped
    assert "phone" not in dropped
    assert "id_card" not in dropped
    assert set(dropped) <= {
        "student_id",
        "grade",
        "class_name",
        "subject_track",
        "subjects",
    }
    students = load_students(tmp_path, config)
    assert len(students) == 1
    assert students[0].student_id == "S999"
    assert not hasattr(students[0], "name") or not getattr(students[0], "name", None)


def test_parse_bool_variants():
    assert parse_bool("是") is True
    assert parse_bool("错") is False
    assert parse_bool("1") is True
    assert parse_bool("0") is False
    assert parse_bool(True) is True


def test_track_mapping():
    assert subjects_from_track("物化生") == ["物理", "化学", "生物"]
    assert subjects_from_track("史地生") == ["历史", "地理", "生物"]


def test_cleaner_fills_subjects_from_track():
    from src import Student

    cleaned = clean_dataset(
        {"students": [Student("S100", "高二", "1班", "物化地", [])], "answers": []}
    )
    assert cleaned["students"][0].subjects == ["物理", "化学", "地理"]


def test_mastery_filters_by_subject_track(cleaned, config):
    profiles = build_student_profiles(
        cleaned["students"],
        cleaned["scores"],
        answers=cleaned["answers"],
        exams=cleaned["exams"],
    )
    mastery = analyze_knowledge_mastery(
        profiles,
        answers=cleaned["answers"],
        exams=cleaned["exams"],
        config=config,
    )
    s001 = mastery["S001"]
    s005 = mastery["S005"]
    assert all(row.subject in {"物理", "化学", "生物"} for row in s001)
    assert all(row.subject in {"历史", "地理", "生物"} for row in s005)
    assert not any(row.subject == "历史" for row in s001)
    assert not any(row.subject == "物理" for row in s005)


def test_wrong_answers_pull_mastery_down(cleaned, config):
    profiles = build_student_profiles(
        cleaned["students"],
        cleaned["scores"],
        answers=cleaned["answers"],
        exams=cleaned["exams"],
    )
    mastery = analyze_knowledge_mastery(
        profiles, answers=cleaned["answers"], exams=cleaned["exams"], config=config
    )
    s001_n2 = next(r for r in mastery["S001"] if r.knowledge_point == "牛顿第二定律")
    s002_n2 = next(r for r in mastery["S002"] if r.knowledge_point == "牛顿第二定律")
    assert s001_n2.mastery_score < s002_n2.mastery_score
    assert s001_n2.recent_trend == "下降"
    assert s001_n2.recommend_priority in {"高", "中"}


def test_weak_points_rank_low_mastery_first(cleaned, config):
    profiles = build_student_profiles(
        cleaned["students"],
        cleaned["scores"],
        answers=cleaned["answers"],
        exams=cleaned["exams"],
    )
    mastery = analyze_knowledge_mastery(
        profiles, answers=cleaned["answers"], exams=cleaned["exams"], config=config
    )
    s003 = mastery["S003"]
    assert s003[0].knowledge_point == "动能定理"
    assert s003[0].weak_score >= s003[-1].weak_score


def test_layers_thresholds(config):
    assert layer_for(0.2, config) == "基础"
    assert layer_for(0.6, config) == "中等"
    assert layer_for(0.9, config) == "拓展"


def test_generator_includes_wrong_question_review_and_respects_cap(cleaned, config):
    profiles = build_student_profiles(
        cleaned["students"],
        cleaned["scores"],
        answers=cleaned["answers"],
        exams=cleaned["exams"],
    )
    mastery = analyze_knowledge_mastery(
        profiles, answers=cleaned["answers"], exams=cleaned["exams"], config=config
    )
    profile = next(p for p in profiles if p.student.student_id == "S001")
    material = RuleBasedGenerator().generate(
        profile, mastery["S001"], cleaned["questions"], config
    )
    assert any(item.source == "原错题" for item in material.review_items)
    assert any(item.source == "同知识点新题" for item in material.review_items)
    max_q = config["output"]["max_questions"]
    assert material.question_count <= max_q
    assert material.estimated_pages <= config["output"]["max_pages"] + 1e-6


def test_llm_hook_exists_but_is_not_used_by_default(config):
    assert issubclass(LLMGenerator, MaterialGenerator)
    assert isinstance(get_generator(config), RuleBasedGenerator)
    with pytest.raises(NotImplementedError):
        LLMGenerator().generate(None, [], [], config)  # type: ignore[arg-type]


def test_end_to_end_pipeline(tmp_path, config):
    output = tmp_path / "output"
    result = run_pipeline(SAMPLE, output, CONFIG)
    assert result["count"] == 8
    summary = output / "教师审核摘要.md"
    assert summary.exists()
    text = summary.read_text(encoding="utf-8")
    assert "教师审核摘要" in text
    assert "S001" in text
    assert "私人信息" in text
    for i in range(1, 9):
        path = output / "students" / f"S00{i}.md"
        assert path.exists(), path
        body = path.read_text(encoding="utf-8")
        assert f"S00{i}" in body
        assert "错题重练" in body
        assert "分层资料" in body
