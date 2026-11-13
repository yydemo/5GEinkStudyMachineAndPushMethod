"""个性化试卷与资料引擎（第一版，规则引擎）。"""

from dataclasses import dataclass, field
from typing import Optional

__version__ = "0.1.0"

# 选科组合 → 科目列表。若学生记录已提供 subjects 字段，则以该字段为准。
TRACK_SUBJECTS = {
    "物化生": ["物理", "化学", "生物"],
    "史地生": ["历史", "地理", "生物"],
    "物化地": ["物理", "化学", "地理"],
    "史地政": ["历史", "地理", "政治"],
    "物生地": ["物理", "生物", "地理"],
    "史政生": ["历史", "政治", "生物"],
}

ALLOWED_STUDENT_FIELDS = (
    "student_id",
    "grade",
    "class_name",
    "subject_track",
    "subjects",
)


@dataclass
class Student:
    student_id: str
    grade: str
    class_name: str
    subject_track: str
    subjects: list[str] = field(default_factory=list)


@dataclass
class Exam:
    exam_id: str
    subject: str
    exam_date: str
    full_score: float
    exam_name: str = ""


@dataclass
class Answer:
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
    exam_id: str
    student_id: str
    subject: str
    score: float
    full_score: float
    exam_date: str = ""


@dataclass
class Question:
    question_id: str
    subject: str
    knowledge_points: list[str] = field(default_factory=list)
    difficulty: str = "中等"
    stem: str = ""
    exam_id: str = ""
    explanation: str = ""


@dataclass
class KnowledgeMastery:
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
    student: Student
    exam_count: int = 0
    subject_scores: dict = field(default_factory=dict)
    average_scores: dict = field(default_factory=dict)
    wrong_answers: list = field(default_factory=list)
    recent_exam_ids: list = field(default_factory=list)


@dataclass
class PracticeItem:
    question_id: str
    subject: str
    knowledge_points: list[str]
    difficulty: str
    stem: str
    source: str  # 原错题 / 同知识点新题 / 分层练习
    origin_exam_id: str = ""
    explanation: str = ""


@dataclass
class MaterialSection:
    knowledge_point: str
    subject: str
    layer: str  # 基础 / 中等 / 拓展
    mastery_score: float
    tips: str
    items: list = field(default_factory=list)


@dataclass
class StudentMaterial:
    student: Student
    summary: str
    weak_points: list = field(default_factory=list)
    review_items: list = field(default_factory=list)
    layered_sections: list = field(default_factory=list)
    question_count: int = 0
    estimated_pages: float = 0.0
