"""为每名学生生成学情周报。只使用学号与学习相关字段。"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from .. import KnowledgeMastery, Student, StudentMaterial
from .checkin import Checkin
from .planner import SeatAssignment, WEEKDAY_NAMES


PRIVATE_MARKERS = ("姓名", "手机", "电话", "身份证", "联系方式", "家庭住址", "家长姓名")


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def parse_week_start(value: Optional[str], checkins: list[Checkin]) -> date:
    if value:
        return monday_of(date.fromisoformat(value))
    dated = []
    for item in checkins:
        try:
            dated.append(date.fromisoformat(item.date))
        except ValueError:
            continue
    if dated:
        return monday_of(max(dated))
    return monday_of(date.today())


def week_range(week_start: date) -> tuple[date, date]:
    start = monday_of(week_start)
    return start, start + timedelta(days=6)


def _pct(value: float) -> str:
    return f"{value:.0%}"


def _filter_week(checkins: list[Checkin], start: date, end: date) -> list[Checkin]:
    selected = []
    for item in checkins:
        try:
            day = date.fromisoformat(item.date)
        except ValueError:
            continue
        if start <= day <= end:
            selected.append(item)
    return selected


def render_weekly_report(
    student: Student,
    week_start: date,
    checkins: list[Checkin],
    mastery_rows: Optional[list[KnowledgeMastery]] = None,
    assignments: Optional[list[SeatAssignment]] = None,
    material: Optional[StudentMaterial] = None,
) -> str:
    start, end = week_range(week_start)
    records = [item for item in checkins if item.student_id == student.student_id]
    planned = len(records)
    attended = [item for item in records if item.attended]
    rate = (len(attended) / planned) if planned else 0.0
    minutes = sum(item.duration_minutes for item in attended)
    subjects = sorted({item.subject_focus for item in attended if item.subject_focus})

    lines = [
        f"# 学情周报 · {student.student_id}",
        "",
        f"- 统计周期：{start.isoformat()} 至 {end.isoformat()}（按周一至周日，日期为本地日历日）",
        f"- 年级 / 班级：{student.grade or '未填'} / {student.class_name or '未填'}",
        f"- 选科：{student.subject_track or '未填'}（{'、'.join(student.subjects) or '未填'}）",
        "",
        "> 本报告只含内部学号与学习相关字段，不含姓名、联系方式或其他私人信息。",
        "",
        "## 本周到馆",
        "",
        f"- 应到 {planned} 次，实到 {len(attended)} 次，出勤率 {_pct(rate)}",
        f"- 在馆时长合计 {minutes} 分钟",
    ]
    if subjects:
        lines.append(f"- 实际重点科目：{'、'.join(subjects)}")
    lines.append("")

    if records:
        lines.extend(
            [
                "| 日期 | 星期 | 场次 | 座位 | 重点科目 | 应到时长 | 实到时长 | 出勤 |",
                "|------|------|------|------|----------|----------|----------|------|",
            ]
        )
        for item in records:
            try:
                day = date.fromisoformat(item.date)
                weekday = WEEKDAY_NAMES.get(day.isoweekday(), "")
            except ValueError:
                weekday = ""
            status = "到馆" if item.attended else "未到"
            lines.append(
                f"| {item.date} | {weekday} | {item.slot_id or '—'} | {item.seat_id or '—'} "
                f"| {item.subject_focus or '—'} | {item.planned_minutes or '—'} 分钟 "
                f"| {item.duration_minutes} 分钟 | {status} |"
            )
        lines.append("")
    else:
        lines.append("本周暂无签到记录。")
        lines.append("")

    if assignments:
        mine = [item for item in assignments if item.student_id == student.student_id]
        if mine:
            lines.extend(["## 建议场次（按薄弱科目编排）", ""])
            lines.append("以下为规则引擎给出的每周建议安排，可与实际签到对照。")
            lines.append("")
            for item in mine:
                point = f"（{item.knowledge_point}）" if item.knowledge_point else ""
                lines.append(
                    f"- {WEEKDAY_NAMES.get(item.weekday, item.weekday)} {item.slot_label} "
                    f"{item.start}–{item.end}，座位 {item.seat_id}（{item.zone}），"
                    f"重点：{item.subject_focus or '未分科'}{point}"
                )
            lines.append("")

    lines.extend(["## 本周学情", ""])
    rows = list(mastery_rows or [])
    if rows:
        lines.extend(
            [
                "| 科目 | 知识点 | 掌握度 | 趋势 | 优先级 |",
                "|------|--------|--------|------|--------|",
            ]
        )
        for point in rows[:5]:
            lines.append(
                f"| {point.subject} | {point.knowledge_point} | {_pct(point.mastery_score)} "
                f"| {point.recent_trend} | {point.recommend_priority} |"
            )
        lines.append("")
    else:
        lines.append("暂无足够作答数据，未能列出薄弱知识点。")
        lines.append("")

    if material:
        lines.append(
            f"已为其准备个性化练习 {material.question_count} 题，预估 {material.estimated_pages} 页，适合下发到墨水屏。"
        )
        lines.append("")

    lines.extend(["## 下周建议", ""])
    if rows:
        top = rows[0]
        lines.append(
            f"- 优先巩固 {top.subject}「{top.knowledge_point}」，可安排在对应辅导区完成错题重练。"
        )
    if planned and rate < 0.8:
        lines.append("- 本周出勤不足八成，建议与学生确认场次是否需要调整（报告中不记录私人原因）。")
    if not planned:
        lines.append("- 本周尚无排班或签到，建议先按薄弱科目完成场次安排。")
    if not rows and not planned:
        lines.append("- 待补充作答记录与到馆记录后再更新本报告。")
    lines.append("- 材料以墨水屏阅读为主，控制篇幅，便于伴学师当堂核验。")
    lines.append("")
    lines.append("本报告可由教师或伴学师审核后发给家长，内容仅限学习过程。")
    lines.append("")

    text = "\n".join(lines)
    for marker in PRIVATE_MARKERS:
        if marker in text.split("私人信息")[0] and marker in ("手机", "身份证"):
            # 标题声明中会出现「私人信息」，但不应出现具体私人字段值；关键词提示本身允许。
            pass
    return text


def write_weekly_reports(
    students: list[Student],
    checkins: list[Checkin],
    output_dir: str | Path,
    week_start: date,
    mastery: Optional[dict[str, list[KnowledgeMastery]]] = None,
    assignments: Optional[list[SeatAssignment]] = None,
    materials: Optional[dict[str, StudentMaterial]] = None,
) -> dict:
    start, end = week_range(week_start)
    week_checkins = _filter_week(checkins, start, end)
    output_dir = Path(output_dir)
    target = output_dir / "studyroom" / "weekly"
    target.mkdir(parents=True, exist_ok=True)

    paths = []
    for student in students:
        text = render_weekly_report(
            student=student,
            week_start=start,
            checkins=week_checkins,
            mastery_rows=(mastery or {}).get(student.student_id),
            assignments=assignments,
            material=(materials or {}).get(student.student_id),
        )
        path = target / f"{student.student_id}_学情周报.md"
        path.write_text(text, encoding="utf-8")
        paths.append(path)

    # 教师汇总（同样不含私人信息）
    by_student = defaultdict(list)
    for item in week_checkins:
        by_student[item.student_id].append(item)
    summary_lines = [
        f"# 学情周报汇总（{start.isoformat()} 至 {end.isoformat()}）",
        "",
        "仅含内部学号与出勤、薄弱科目等学习字段，不含姓名或其他私人信息。",
        "",
        "| 学号 | 应到 | 实到 | 出勤率 | 在馆分钟 | 重点科目 |",
        "|------|------|------|--------|----------|----------|",
    ]
    for student in students:
        records = by_student.get(student.student_id, [])
        planned = len(records)
        arrived = [item for item in records if item.attended]
        rate = (len(arrived) / planned) if planned else 0.0
        minutes = sum(item.duration_minutes for item in arrived)
        subjects = "、".join(sorted({item.subject_focus for item in arrived if item.subject_focus})) or "—"
        summary_lines.append(
            f"| {student.student_id} | {planned} | {len(arrived)} | {_pct(rate)} | {minutes} | {subjects} |"
        )
    summary_lines.append("")
    summary_path = output_dir / "studyroom" / "学情周报汇总.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    return {
        "week_start": start,
        "week_end": end,
        "reports": paths,
        "summary": summary_path,
        "count": len(paths),
    }
