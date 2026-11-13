"""读取学生、考试、答题与题库数据。

仅保留学习相关字段。学生表中的姓名、联系方式、身份证等额外列会被丢弃。
支持 CSV 与 JSON 两种输入（同名文件，优先 CSV）。
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Optional

from . import (
    ALLOWED_STUDENT_FIELDS,
    Answer,
    Exam,
    Question,
    ScoreRecord,
    Student,
)


def _as_path(data_dir: str | Path) -> Path:
    return Path(data_dir)


def _load_table(data_dir: Path, name: str) -> list[dict[str, Any]]:
    csv_path = data_dir / f"{name}.csv"
    json_path = data_dir / f"{name}.json"
    if csv_path.exists():
        with csv_path.open(encoding="utf-8-sig", newline="") as fh:
            return [dict(row) for row in csv.DictReader(fh)]
    if json_path.exists():
        with json_path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            data = data.get("records") or data.get(name) or data.get("data") or []
        if not isinstance(data, list):
            raise ValueError(f"{json_path} 应为对象列表")
        return [dict(item) for item in data]
    return []


def _s(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _f(value: Any, default: float = 0.0) -> float:
    text = _s(value)
    if text == "":
        return default
    try:
        return float(text)
    except ValueError:
        return default


def parse_bool(value: Any, default: bool = False) -> bool:
    """把常见对错标记转为布尔值。"""
    if isinstance(value, bool):
        return value
    text = _s(value).lower()
    if text in {"1", "true", "t", "yes", "y", "是", "对", "正确", "对的", "√"}:
        return True
    if text in {"0", "false", "f", "no", "n", "否", "错", "错误", "错的", "×", "x"}:
        return False
    return default


def split_list(value: Any) -> list[str]:
    """把逗号/顿号/分号分隔的字符串拆成列表；已是列表则原样规范化。"""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    for sep in ("，", "、", ";", "；", "|"):
        text = text.replace(sep, ",")
    return [part.strip() for part in text.split(",") if part.strip()]


def allowed_student_fields(config: Optional[dict] = None) -> tuple[str, ...]:
    if config:
        extra = (
            config.get("privacy", {}).get("allowed_student_fields")
            or config.get("allowed_student_fields")
        )
        if extra:
            return tuple(extra)
    return ALLOWED_STUDENT_FIELDS


def drop_private_student_fields(
    row: dict[str, Any], config: Optional[dict] = None
) -> dict[str, Any]:
    """只保留学习相关字段，丢弃姓名等隐私列。"""
    allowed = set(allowed_student_fields(config))
    return {key: value for key, value in row.items() if key in allowed}


def load_students(data_dir: str | Path, config: Optional[dict] = None) -> list[Student]:
    rows = _load_table(_as_path(data_dir), "students")
    students: list[Student] = []
    for row in rows:
        cleaned = drop_private_student_fields(row, config)
        student_id = _s(cleaned.get("student_id"))
        if not student_id:
            continue
        students.append(
            Student(
                student_id=student_id,
                grade=_s(cleaned.get("grade")),
                class_name=_s(cleaned.get("class_name")),
                subject_track=_s(cleaned.get("subject_track")),
                subjects=split_list(cleaned.get("subjects")),
            )
        )
    return students


def load_exams(data_dir: str | Path) -> list[Exam]:
    rows = _load_table(_as_path(data_dir), "exams")
    exams: list[Exam] = []
    for row in rows:
        exam_id = _s(row.get("exam_id"))
        if not exam_id:
            continue
        exams.append(
            Exam(
                exam_id=exam_id,
                subject=_s(row.get("subject")),
                exam_date=_s(row.get("exam_date")),
                full_score=_f(row.get("full_score"), 100.0),
                exam_name=_s(row.get("exam_name") or row.get("name")),
            )
        )
    return exams


def load_scores(data_dir: str | Path) -> list[ScoreRecord]:
    rows = _load_table(_as_path(data_dir), "scores")
    records: list[ScoreRecord] = []
    for row in rows:
        student_id = _s(row.get("student_id"))
        exam_id = _s(row.get("exam_id"))
        if not student_id or not exam_id:
            continue
        records.append(
            ScoreRecord(
                exam_id=exam_id,
                student_id=student_id,
                subject=_s(row.get("subject")),
                score=_f(row.get("score")),
                full_score=_f(row.get("full_score"), 100.0),
                exam_date=_s(row.get("exam_date")),
            )
        )
    return records


def load_answers(data_dir: str | Path) -> list[Answer]:
    rows = _load_table(_as_path(data_dir), "answers")
    records: list[Answer] = []
    for row in rows:
        student_id = _s(row.get("student_id"))
        exam_id = _s(row.get("exam_id"))
        question_id = _s(row.get("question_id"))
        if not student_id or not exam_id or not question_id:
            continue
        records.append(
            Answer(
                exam_id=exam_id,
                student_id=student_id,
                question_id=question_id,
                knowledge_points=split_list(row.get("knowledge_points")),
                is_correct=parse_bool(row.get("is_correct")),
                score=_f(row.get("score")),
                full_score=_f(row.get("full_score")),
                error_type=_s(row.get("error_type")),
                subject=_s(row.get("subject")),
            )
        )
    return records


def load_question_bank(data_dir: str | Path) -> list[Question]:
    rows = _load_table(_as_path(data_dir), "question_bank")
    questions: list[Question] = []
    for row in rows:
        question_id = _s(row.get("question_id"))
        if not question_id:
            continue
        questions.append(
            Question(
                question_id=question_id,
                subject=_s(row.get("subject")),
                knowledge_points=split_list(row.get("knowledge_points")),
                difficulty=_s(row.get("difficulty"), "中等"),
                stem=_s(row.get("stem") or row.get("content") or row.get("question")),
                exam_id=_s(row.get("exam_id")),
                explanation=_s(row.get("explanation") or row.get("tips")),
            )
        )
    return questions


def load_dataset(data_dir: str | Path, config: Optional[dict] = None) -> dict:
    """一次性读取全部输入表。缺表时返回空列表，不报错。"""
    path = _as_path(data_dir)
    if not path.exists():
        raise FileNotFoundError(f"数据目录不存在：{path}")
    return {
        "students": load_students(path, config),
        "exams": load_exams(path),
        "scores": load_scores(path),
        "answers": load_answers(path),
        "questions": load_question_bank(path),
    }
