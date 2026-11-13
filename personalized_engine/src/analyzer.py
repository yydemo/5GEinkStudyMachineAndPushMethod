"""知识点掌握度分析与薄弱点排序。"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from . import Answer, Exam, KnowledgeMastery, StudentProfile


def _config_section(config: Optional[dict], name: str) -> dict:
    return (config or {}).get(name) or {}


def exam_chronology(exams: list[Exam], answers: list[Answer] | None = None) -> dict[str, str]:
    dates = {exam.exam_id: exam.exam_date for exam in exams if exam.exam_date}
    return dates


def _correctness(answer: Answer) -> float:
    if answer.full_score and answer.full_score > 0:
        ratio = answer.score / answer.full_score
        return max(0.0, min(1.0, ratio))
    return 1.0 if answer.is_correct else 0.0


def _trend(series: list[float], gap: float = 0.08) -> str:
    if len(series) < 2:
        return "数据不足"
    mid = max(1, len(series) // 2)
    earlier = sum(series[:mid]) / mid
    later = sum(series[mid:]) / (len(series) - mid)
    if later < earlier - gap:
        return "下降"
    if later > earlier + gap:
        return "上升"
    return "平稳"


def _priority(weak_score: float) -> str:
    if weak_score >= 0.6:
        return "高"
    if weak_score >= 0.35:
        return "中"
    return "低"


def analyze_knowledge_mastery(
    profiles: list[StudentProfile],
    answers: list[Answer] | None = None,
    exams: list[Exam] | None = None,
    config: Optional[dict] = None,
    dataset: Optional[dict] = None,
) -> dict[str, list[KnowledgeMastery]]:
    """计算每名学生各知识点掌握度，并给出薄弱点排序。

    规则：
    - 只分析选科组合内的科目；
    - 取该知识点最近 3 次相关考试，按配置加权；
    - 错题在分母中权重更高，从而更明显拉低掌握度；
    - 薄弱分 = 低掌握度 + 高出现频次 + 下降趋势。
    """
    if dataset:
        answers = answers if answers is not None else dataset.get("answers")
        exams = exams if exams is not None else dataset.get("exams")
    answers = answers or []
    exams = exams or []

    mastery_cfg = _config_section(config, "mastery")
    weak_cfg = _config_section(config, "weak_points")
    recent_n = int(mastery_cfg.get("recent_exam_count") or 3)
    weights = list(mastery_cfg.get("exam_weights") or [0.5, 0.3, 0.2])
    wrong_weight = float(mastery_cfg.get("wrong_answer_weight") or 1.8)
    w_mastery = float(weak_cfg.get("mastery_weight") or 0.5)
    w_freq = float(weak_cfg.get("frequency_weight") or 0.3)
    w_decline = float(weak_cfg.get("decline_weight") or 0.2)
    max_weak = int(weak_cfg.get("max_weak_points") or 5)

    exam_dates = exam_chronology(exams)

    answers_by_student: dict[str, list[Answer]] = defaultdict(list)
    for answer in answers:
        answers_by_student[answer.student_id].append(answer)

    results: dict[str, list[KnowledgeMastery]] = {}
    for profile in profiles:
        student = profile.student
        allowed = set(student.subjects)
        items = [
            a
            for a in answers_by_student.get(student.student_id, [])
            if (not allowed) or (not a.subject) or (a.subject in allowed)
        ]

        # (subject, kp) -> exam_id -> [answers]
        grouped: dict[tuple[str, str], dict[str, list[Answer]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for answer in items:
            subject = answer.subject or "未分科"
            for kp in answer.knowledge_points:
                grouped[(subject, kp)][answer.exam_id].append(answer)

        rows: list[KnowledgeMastery] = []
        frequencies: list[int] = []
        pending = []
        for (subject, kp), by_exam in grouped.items():
            exam_ids = sorted(
                by_exam.keys(),
                key=lambda eid: (exam_dates.get(eid, ""), eid),
            )
            recent_ids = exam_ids[-recent_n:]
            # 用于趋势的按时间正序正确率
            per_exam_correctness = []
            numerator = 0.0
            denominator = 0.0
            # 最近一次对应 weights[0]
            for offset, exam_id in enumerate(reversed(recent_ids)):
                weight = weights[offset] if offset < len(weights) else weights[-1]
                exam_values = []
                for answer in by_exam[exam_id]:
                    correctness = _correctness(answer)
                    exam_values.append(correctness)
                    sample_w = weight * (wrong_weight if not answer.is_correct else 1.0)
                    numerator += correctness * weight
                    denominator += sample_w
                if exam_values:
                    per_exam_correctness.append(
                        sum(exam_values) / len(exam_values)
                    )
            mastery = (numerator / denominator) if denominator else 0.0
            mastery = max(0.0, min(1.0, mastery))
            # per_exam_correctness 目前是从新到旧，趋势需要从旧到新
            trend = _trend(list(reversed(per_exam_correctness)))
            frequency = sum(len(v) for v in by_exam.values())
            frequencies.append(frequency)
            pending.append((subject, kp, mastery, trend, frequency, exam_ids))

        max_freq = max(frequencies) if frequencies else 1
        for subject, kp, mastery, trend, frequency, _exam_ids in pending:
            freq_norm = frequency / max_freq if max_freq else 0.0
            decline_flag = 1.0 if trend == "下降" else 0.0
            weak_score = (
                (1.0 - mastery) * w_mastery
                + freq_norm * w_freq
                + decline_flag * w_decline
            )
            rows.append(
                KnowledgeMastery(
                    student_id=student.student_id,
                    subject=subject,
                    knowledge_point=kp,
                    mastery_score=round(mastery, 4),
                    recent_trend=trend,
                    frequency=frequency,
                    weak_score=round(weak_score, 4),
                    recommend_priority=_priority(weak_score),
                )
            )
        rows.sort(key=lambda row: (-row.weak_score, row.mastery_score, -row.frequency))
        # 截断仅用于“优先薄弱点”展示，完整列表仍返回，调用方可自行切片
        results[student.student_id] = rows
        profile_max = max_weak  # stored for generator via config; keep full list
        _ = profile_max
    return results


def top_weak_points(
    rows: list[KnowledgeMastery], limit: int = 5
) -> list[KnowledgeMastery]:
    return list(rows)[:limit]
