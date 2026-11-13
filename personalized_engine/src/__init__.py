"""个性化试卷与资料引擎（第一版，规则引擎）。

Personalized exam and materials engine (first version, rule engine).
"""

from dataclasses import dataclass, field
from typing import Optional

__version__ = "0.2.0"

# 选科组合 → 科目列表。若学生记录已提供 subjects 字段，则以该字段为准。
# Subject combination → subject list. If a student record provides `subjects`, that field wins.
TRACK_SUBJECTS = {
    "物化生": ["物理", "化学", "生物"],
    "史地生": ["历史", "地理", "生物"],
    "物化地": ["物理", "化学", "地理"],
    "史地政": ["历史", "地理", "政治"],
    "物生地": ["物理", "生物", "地理"],
    "史政生": ["历史", "政治", "生物"],
}

# 学生表允许保留的学习字段（其余隐私列一律丢弃）。
# Learning fields allowed in the student table (all other private columns are dropped).
ALLOWED_STUDENT_FIELDS = (
    "student_id",
    "grade",
    "class_name",
    "subject_track",
    "subjects",
)


# ---- 数据结构 / Data structures ----

@dataclass
class Student:
    """学生（仅学习字段）。 / A student (learning fields only)."""

    student_id: str
    grade: str
    class_name: str
    subject_track: str
    subjects: list[str] = field(default_factory=list)


@dataclass
class Exam:
    """一次考试。 / One exam."""

    exam_id: str
    subject: str
    exam_date: str
    full_score: float
    exam_name: str = ""


@dataclass
class Answer:
    """一道题的作答记录。 / One per-question answer record."""

    exam_id: str
    student_id: str
    question_id: str
    knowledge_points: list[str] = field(default_factory=list)
    is_correct: bool = False
    score: float = 0.0
    full_score: float = 0.0
    error_type: str = ""
    subject: str = ""


@dataclass
class ScoreRecord:
    """某生某次考试的总分。 / A student's total score for one exam."""

    exam_id: str
    student_id: str
    subject: str
    score: float
    full_score: float
    exam_date: str = ""


@dataclass
class Question:
    """题库或试卷中的一道题。 / One question from the bank or an exam paper."""

    question_id: str
    subject: str
    knowledge_points: list[str] = field(default_factory=list)
    difficulty: str = "中等"
    stem: str = ""
    exam_id: str = ""
    explanation: str = ""


@dataclass
class KnowledgeMastery:
    """某生某知识点的掌握度与薄弱分。 / A student's mastery and weak score for one knowledge point."""

    student_id: str
    subject: str
    knowledge_point: str
    mastery_score: float
    recent_trend: str
    frequency: int
    weak_score: float = 0.0
    recommend_priority: str = "中"


@dataclass
class StudentProfile:
    """学情画像。 / Learning profile."""

    student: Student
    exam_count: int = 0
    subject_scores: dict = field(default_factory=dict)
    average_scores: dict = field(default_factory=dict)
    wrong_answers: list = field(default_factory=list)
    recent_exam_ids: list = field(default_factory=list)


@dataclass
class PracticeItem:
    """材料中的一道练习题。 / One practice item in the material pack."""

    question_id: str
    subject: str
    knowledge_points: list[str]
    difficulty: str
    stem: str
    source: str  # 原错题 / 同知识点新题 / 分层练习 (original wrong question / new question on the same point / tiered practice)
    origin_exam_id: str = ""
    explanation: str = ""


@dataclass
class MaterialSection:
    """按知识点分层的一节资料。 / One tiered material section for a knowledge point."""

    knowledge_point: str
    subject: str
    layer: str  # 基础 / 中等 / 拓展 (basic / intermediate / advanced)
    mastery_score: float
    tips: str
    items: list = field(default_factory=list)


@dataclass
class StudentMaterial:
    """一名学生的完整个性化材料。 / A student's complete personalized material pack."""

    student: Student
    summary: str
    weak_points: list = field(default_factory=list)
    review_items: list = field(default_factory=list)
    layered_sections: list = field(default_factory=list)
    question_count: int = 0
    estimated_pages: float = 0.0
    # 英文版概要，仅用于双语显示，不参与页数估算。
    # English summary, for bilingual display only; not counted in page estimates.
    summary_en: str = ""
