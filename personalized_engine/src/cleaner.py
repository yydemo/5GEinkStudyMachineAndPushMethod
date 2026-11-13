"""清洗与标准化：空白、选科、难度、对错标记，并补全关联字段。

Cleaning and normalization: whitespace, subject combinations, difficulty and
right/wrong markers, plus filling in related fields.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from . import TRACK_SUBJECTS, Answer, Exam, Question, ScoreRecord, Student
from .data_loader import parse_bool, split_list


# 难度别名 → 标准难度（基础 / 中等 / 拓展）。
# Difficulty aliases → standard difficulty (basic / intermediate / advanced).
DIFFICULTY_MAP = {
    "基础": "基础",
    "简单": "基础",
    "容易": "基础",
    "初级": "基础",
    "中等": "中等",
    "中级": "中等",
    "一般": "中等",
    "综合": "中等",
    "拓展": "拓展",
    "提高": "拓展",
    "困难": "拓展",
    "难题": "拓展",
    "高级": "拓展",
    "拔高": "拓展",
}


def normalize_difficulty(value: str, default: str = "中等") -> str:
    """把难度别名归一。 / Normalize a difficulty alias."""
    text = (value or "").strip()
    return DIFFICULTY_MAP.get(text, default if not text else text)


def subjects_from_track(track: str) -> list[str]:
    """按选科组合推断科目列表。 / Infer the subject list from a subject combination."""
    return list(TRACK_SUBJECTS.get((track or "").strip(), []))


def clean_students(students: list[Student]) -> list[Student]:
    """去重、去空白，并补全科目。 / Deduplicate, strip whitespace and fill in subjects."""
    cleaned: list[Student] = []
    seen: set[str] = set()
    for student in students:
        student_id = (student.student_id or "").strip()
        if not student_id or student_id in seen:
            continue
        seen.add(student_id)
        subjects = [s.strip() for s in student.subjects if s and str(s).strip()]
        track = (student.subject_track or "").strip()
        if not subjects:
            subjects = subjects_from_track(track)
        cleaned.append(
            Student(
                student_id=student_id,
                grade=(student.grade or "").strip(),
                class_name=(student.class_name or "").strip(),
                subject_track=track,
                subjects=subjects,
            )
        )
    return cleaned


def clean_exams(exams: list[Exam]) -> list[Exam]:
    """去重并按日期排序。 / Deduplicate and sort by date."""
    cleaned: list[Exam] = []
    seen: set[str] = set()
    for exam in exams:
        exam_id = (exam.exam_id or "").strip()
        if not exam_id or exam_id in seen:
            continue
        seen.add(exam_id)
        cleaned.append(
            Exam(
                exam_id=exam_id,
                subject=(exam.subject or "").strip(),
                exam_date=(exam.exam_date or "").strip(),
                full_score=float(exam.full_score or 0),
                exam_name=(exam.exam_name or "").strip(),
            )
        )
    cleaned.sort(key=lambda item: (item.exam_date, item.exam_id))
    return cleaned


def clean_scores(
    scores: list[ScoreRecord], exams: list[Exam]
) -> list[ScoreRecord]:
    """去重成绩，并用考试表补全科目、日期、满分。 / Deduplicate scores and fill subject, date and full score from exams."""
    exam_map = {exam.exam_id: exam for exam in exams}
    cleaned: list[ScoreRecord] = []
    seen: set[tuple[str, str]] = set()
    for record in scores:
        key = (record.student_id.strip(), record.exam_id.strip())
        if not key[0] or not key[1] or key in seen:
            continue
        seen.add(key)
        exam = exam_map.get(key[1])
        subject = (record.subject or "").strip() or (exam.subject if exam else "")
        exam_date = (record.exam_date or "").strip() or (exam.exam_date if exam else "")
        full_score = record.full_score or (exam.full_score if exam else 100.0)
        cleaned.append(
            ScoreRecord(
                exam_id=key[1],
                student_id=key[0],
                subject=subject,
                score=float(record.score or 0),
                full_score=float(full_score or 0),
                exam_date=exam_date,
            )
        )
    return cleaned


def clean_answers(
    answers: list[Answer],
    exams: list[Exam],
    questions: list[Question],
) -> list[Answer]:
    """去重作答，并补全知识点、科目与对错。 / Deduplicate answers and fill knowledge points, subject and correctness."""
    exam_map = {exam.exam_id: exam for exam in exams}
    question_map = {question.question_id: question for question in questions}
    cleaned: list[Answer] = []
    seen: set[tuple[str, str, str]] = set()
    for answer in answers:
        student_id = (answer.student_id or "").strip()
        exam_id = (answer.exam_id or "").strip()
        question_id = (answer.question_id or "").strip()
        key = (student_id, exam_id, question_id)
        if not student_id or not exam_id or not question_id or key in seen:
            continue
        seen.add(key)
        question = question_map.get(question_id)
        exam = exam_map.get(exam_id)
        kps = [kp.strip() for kp in (answer.knowledge_points or []) if kp and str(kp).strip()]
        if not kps and question:
            kps = list(question.knowledge_points)
        subject = (answer.subject or "").strip()
        if not subject and exam:
            subject = exam.subject
        if not subject and question:
            subject = question.subject
        is_correct = parse_bool(answer.is_correct)
        # 若未标对错，则按得分占比判断 / If correctness is not marked, judge by score ratio
        full_score = float(answer.full_score or (question and 0) or 0)
        score = float(answer.score or 0)
        if answer.full_score in (None, "", 0) and not full_score:
            full_score = 0.0
        if not is_correct and score and full_score and score >= full_score - 1e-9:
            is_correct = True
        cleaned.append(
            Answer(
                exam_id=exam_id,
                student_id=student_id,
                question_id=question_id,
                knowledge_points=kps,
                is_correct=is_correct,
                score=score,
                full_score=full_score,
                error_type=(answer.error_type or "").strip(),
                subject=subject,
            )
        )
    return cleaned


def clean_questions(questions: list[Question]) -> list[Question]:
    """去重题目并归一难度。 / Deduplicate questions and normalize difficulty."""
    cleaned: list[Question] = []
    seen: set[str] = set()
    for question in questions:
        question_id = (question.question_id or "").strip()
        if not question_id or question_id in seen:
            continue
        seen.add(question_id)
        cleaned.append(
            Question(
                question_id=question_id,
                subject=(question.subject or "").strip(),
                knowledge_points=[kp.strip() for kp in question.knowledge_points if kp.strip()],
                difficulty=normalize_difficulty(question.difficulty),
                stem=(question.stem or "").strip(),
                exam_id=(question.exam_id or "").strip(),
                explanation=(question.explanation or "").strip(),
            )
        )
    return cleaned


def derive_scores_from_answers(
    answers: list[Answer], exams: list[Exam]
) -> list[ScoreRecord]:
    """若未提供成绩表，按答题得分汇总。 / If no score table is given, aggregate from answer scores."""
    exam_map = {exam.exam_id: exam for exam in exams}
    buckets: dict[tuple[str, str], list[Answer]] = defaultdict(list)
    for answer in answers:
        buckets[(answer.student_id, answer.exam_id)].append(answer)
    records: list[ScoreRecord] = []
    for (student_id, exam_id), items in buckets.items():
        exam = exam_map.get(exam_id)
        subject = (exam.subject if exam else "") or next((a.subject for a in items if a.subject), "")
        score = sum(a.score for a in items)
        full_score = (exam.full_score if exam and exam.full_score else sum(a.full_score for a in items))
        records.append(
            ScoreRecord(
                exam_id=exam_id,
                student_id=student_id,
                subject=subject,
                score=score,
                full_score=full_score or 0,
                exam_date=exam.exam_date if exam else "",
            )
        )
    return records


def derive_exams_from_records(
    answers: list[Answer], scores: list[ScoreRecord]
) -> list[Exam]:
    """若未提供考试目录，从答题/成绩中推断。 / If no exam list is given, infer it from answers/scores."""
    found: dict[str, Exam] = {}
    for score in scores:
        if score.exam_id not in found:
            found[score.exam_id] = Exam(
                exam_id=score.exam_id,
                subject=score.subject,
                exam_date=score.exam_date,
                full_score=score.full_score or 100.0,
                exam_name=score.exam_id,
            )
    for answer in answers:
        exam = found.get(answer.exam_id)
        if exam is None:
            found[answer.exam_id] = Exam(
                exam_id=answer.exam_id,
                subject=answer.subject,
                exam_date="",
                full_score=0,
                exam_name=answer.exam_id,
            )
        elif not exam.subject and answer.subject:
            exam.subject = answer.subject
    return clean_exams(list(found.values()))


def clean_dataset(raw: dict, config: Optional[dict] = None) -> dict:
    """清洗全部表，并只保留学生表中存在的学号。 / Clean all tables and keep only student IDs present in the student table."""
    students = clean_students(raw.get("students") or [])
    exams = clean_exams(raw.get("exams") or [])
    questions = clean_questions(raw.get("questions") or [])
    answers = clean_answers(raw.get("answers") or [], exams, questions)
    scores = clean_scores(raw.get("scores") or [], exams)
    if not exams:
        exams = derive_exams_from_records(answers, scores)
        answers = clean_answers(raw.get("answers") or [], exams, questions)
        scores = clean_scores(scores, exams)
    if not scores and answers:
        scores = derive_scores_from_answers(answers, exams)
    allowed_ids = {student.student_id for student in students}
    if allowed_ids:
        answers = [a for a in answers if a.student_id in allowed_ids]
        scores = [s for s in scores if s.student_id in allowed_ids]
    return {
        "students": students,
        "exams": exams,
        "scores": scores,
        "answers": answers,
        "questions": questions,
    }
