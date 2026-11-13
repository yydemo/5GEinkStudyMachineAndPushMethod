"""按学生构建学情画像：成绩轨迹、错题列表、近期考试。"""

from __future__ import annotations

from collections import defaultdict

from . import Answer, Exam, ScoreRecord, Student, StudentProfile


def _exam_date(exam_id: str, exams: dict[str, Exam], scores: list[ScoreRecord]) -> str:
    exam = exams.get(exam_id)
    if exam and exam.exam_date:
        return exam.exam_date
    for score in scores:
        if score.exam_id == exam_id and score.exam_date:
            return score.exam_date
    return ""


def build_student_profiles(
    students: list[Student],
    exam_records: list[ScoreRecord] | None = None,
    answers: list[Answer] | None = None,
    exams: list[Exam] | None = None,
) -> list[StudentProfile]:
    """构建每名学生的学情画像。

    可通过位置参数 `(students, exam_records)` 调用，也可传入 answers / exams。
    """
    exam_records = exam_records or []
    answers = answers or []
    exams = exams or []
    exam_map = {exam.exam_id: exam for exam in exams}

    scores_by_student: dict[str, list[ScoreRecord]] = defaultdict(list)
    for record in exam_records:
        scores_by_student[record.student_id].append(record)

    answers_by_student: dict[str, list[Answer]] = defaultdict(list)
    for answer in answers:
        answers_by_student[answer.student_id].append(answer)

    profiles: list[StudentProfile] = []
    for student in students:
        records = list(scores_by_student.get(student.student_id, []))
        allowed = set(student.subjects)

        def subject_ok(subject: str) -> bool:
            return (not allowed) or (not subject) or (subject in allowed)

        records = [r for r in records if subject_ok(r.subject)]
        student_answers = [
            a for a in answers_by_student.get(student.student_id, []) if subject_ok(a.subject)
        ]

        records.sort(
            key=lambda r: (_exam_date(r.exam_id, exam_map, records), r.exam_id)
        )
        subject_scores: dict[str, list[dict]] = defaultdict(list)
        for record in records:
            subject_scores[record.subject or "未分科"].append(
                {
                    "exam_id": record.exam_id,
                    "score": record.score,
                    "full_score": record.full_score,
                    "exam_date": record.exam_date or _exam_date(record.exam_id, exam_map, records),
                    "ratio": (record.score / record.full_score) if record.full_score else 0.0,
                }
            )

        average_scores = {}
        for subject, items in subject_scores.items():
            if not items:
                continue
            ratios = [item["ratio"] for item in items]
            average_scores[subject] = sum(ratios) / len(ratios)

        wrong = [a for a in student_answers if not a.is_correct]
        exam_ids = []
        seen = set()
        for record in reversed(records):
            if record.exam_id not in seen:
                exam_ids.append(record.exam_id)
                seen.add(record.exam_id)
        # recent first already from reversed chronological sort
        profiles.append(
            StudentProfile(
                student=student,
                exam_count=len(seen),
                subject_scores=dict(subject_scores),
                average_scores=average_scores,
                wrong_answers=wrong,
                recent_exam_ids=exam_ids,
            )
        )
    return profiles
