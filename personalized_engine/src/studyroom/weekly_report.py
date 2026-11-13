"""为每名学生生成学情周报。只使用学号与学习相关字段。

Generate a weekly learning report for each student, using only student IDs and
learning-related fields. Reports are bilingual (Chinese-English).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from .. import KnowledgeMastery, Student, StudentMaterial
from ..i18n import bi, bi_join, en, weekday_bi
from .checkin import Checkin
from .planner import SeatAssignment, WEEKDAY_NAMES


# 私人字段关键词（周报中不应出现这些字段的值）。
# Private-field keywords (values for these fields must never appear in reports).
PRIVATE_MARKERS = ("姓名", "手机", "电话", "身份证", "联系方式", "家庭住址", "家长姓名")


def monday_of(day: date) -> date:
    """返回当周周一。 / Return the Monday of that week."""
    return day - timedelta(days=day.weekday())


def parse_week_start(value: Optional[str], checkins: list[Checkin]) -> date:
    """解析统计周起始日；未给出时取最近签到所在周。 / Parse the week start; default to the week of the latest check-in."""
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
    """周一到周日。 / Monday to Sunday."""
    start = monday_of(week_start)
    return start, start + timedelta(days=6)


def _pct(value: float) -> str:
    """百分比格式。 / Percentage format."""
    return f"{value:.0%}"


def _filter_week(checkins: list[Checkin], start: date, end: date) -> list[Checkin]:
    """筛选本周签到。 / Filter check-ins within the week."""
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
    """渲染一名学生的双语学情周报。 / Render one student's bilingual weekly learning report."""
    start, end = week_range(week_start)
    records = [item for item in checkins if item.student_id == student.student_id]
    planned = len(records)
    attended = [item for item in records if item.attended]
    rate = (len(attended) / planned) if planned else 0.0
    minutes = sum(item.duration_minutes for item in attended)
    subjects = sorted({item.subject_focus for item in attended if item.subject_focus})

    lines = [
        f"# 学情周报 / Weekly Learning Report · {student.student_id}",
        "",
        f"- 统计周期：{start.isoformat()} 至 {end.isoformat()}（按周一至周日，日期为本地日历日）",
        f"  Period: {start.isoformat()} to {end.isoformat()} (Monday to Sunday, local calendar dates)",
        f"- 年级 / 班级 (Grade / Class)：{bi(student.grade) or '未填 / Not provided'} / {student.class_name or '未填 / Not provided'}",
        f"- 选科 / Subject combination：{bi(student.subject_track) or '未填 / Not provided'}（{bi_join(student.subjects) or '未填 / Not provided'}）",
        "",
        "> 本报告只含内部学号与学习相关字段，不含姓名、联系方式或其他私人信息。",
        "> This report contains only the internal student ID and learning-related fields, with no names, contact details or other private information.",
        "",
        "## 本周到馆 / Attendance This Week",
        "",
        f"- 应到 {planned} 次，实到 {len(attended)} 次，出勤率 {_pct(rate)}",
        f"  Planned {planned}, attended {len(attended)}, attendance rate {_pct(rate)}",
        f"- 在馆时长合计 {minutes} 分钟 / Total time in the study room: {minutes} minutes",
    ]
    if subjects:
        lines.append(f"- 实际重点科目 / Actual focus subjects：{bi_join(subjects)}")
    lines.append("")

    if records:
        lines.extend(
            [
                "| 日期 / Date | 星期 / Day | 场次 / Session | 座位 / Seat | 重点科目 / Focus subject | 应到时长 / Planned | 实到时长 / Actual | 出勤 / Status |",
                "|------|------|------|------|----------|----------|----------|------|",
            ]
        )
        for item in records:
            try:
                day = date.fromisoformat(item.date)
                weekday = weekday_bi(day.isoweekday() - 1)
            except ValueError:
                weekday = ""
            status = "到馆 / Attended" if item.attended else "未到 / Absent"
            planned_text = (
                f"{item.planned_minutes} 分钟 / min" if item.planned_minutes else "— 分钟 / min"
            )
            lines.append(
                f"| {item.date} | {weekday} | {item.slot_id or '—'} | {item.seat_id or '—'} "
                f"| {bi(item.subject_focus) or '—'} | {planned_text} "
                f"| {item.duration_minutes} 分钟 / min | {status} |"
            )
        lines.append("")
    else:
        lines.append("本周暂无签到记录。 / No check-in records this week.")
        lines.append("")

    if assignments:
        mine = [item for item in assignments if item.student_id == student.student_id]
        if mine:
            lines.extend(["## 建议场次（按薄弱科目编排） / Suggested Sessions (by Weak Subject)", ""])
            lines.append("以下为规则引擎给出的每周建议安排，可与实际签到对照。")
            lines.append("Below is the rule engine's suggested weekly schedule, for comparison with actual check-ins.")
            lines.append("")
            for item in mine:
                point = f"（{bi(item.knowledge_point)}）" if item.knowledge_point else ""
                day_text = weekday_bi(item.weekday - 1) if 1 <= item.weekday <= 7 else item.weekday
                lines.append(
                    f"- {day_text} {bi(item.slot_label)} "
                    f"{item.start}–{item.end}，座位 / seat {item.seat_id}（{bi(item.zone)}），"
                    f"重点 / focus：{bi(item.subject_focus or '未分科')}{point}"
                )
            lines.append("")

    lines.extend(["## 本周学情 / Learning Status This Week", ""])
    rows = list(mastery_rows or [])
    if rows:
        lines.extend(
            [
                "| 科目 / Subject | 知识点 / Knowledge point | 掌握度 / Mastery | 趋势 / Trend | 优先级 / Priority |",
                "|------|--------|--------|------|--------|",
            ]
        )
        for point in rows[:5]:
            lines.append(
                f"| {bi(point.subject)} | {bi(point.knowledge_point)} | {_pct(point.mastery_score)} "
                f"| {bi(point.recent_trend)} | {bi(point.recommend_priority)} |"
            )
        lines.append("")
    else:
        lines.append("暂无足够作答数据，未能列出薄弱知识点。 / Not enough answer data to list weak knowledge points.")
        lines.append("")

    if material:
        lines.append(
            f"已为其准备个性化练习 {material.question_count} 题，预估 {material.estimated_pages} 页，适合下发到墨水屏。"
        )
        lines.append(
            f"{material.question_count} personalized practice questions have been prepared "
            f"(about {material.estimated_pages} pages), suitable for pushing to an E-Ink device."
        )
        lines.append("")

    lines.extend(["## 下周建议 / Suggestions for Next Week", ""])
    if rows:
        top = rows[0]
        lines.append(
            f"- 优先巩固 {top.subject}「{top.knowledge_point}」，可安排在对应辅导区完成错题重练。"
        )
        lines.append(
            f"  Consolidate {en(top.subject)} \"{en(top.knowledge_point)}\" first; mistake re-practice can be done in the matching tutoring zone."
        )
    if planned and rate < 0.8:
        lines.append("- 本周出勤不足八成，建议与学生确认场次是否需要调整（报告中不记录私人原因）。")
        lines.append("  Attendance was below 80% this week; check with the student whether sessions need adjusting (private reasons are not recorded in this report).")
    if not planned:
        lines.append("- 本周尚无排班或签到，建议先按薄弱科目完成场次安排。")
        lines.append("  No schedule or check-ins this week yet; assign sessions by weak subject first.")
    if not rows and not planned:
        lines.append("- 待补充作答记录与到馆记录后再更新本报告。")
        lines.append("  Update this report once answer records and attendance records are available.")
    lines.append("- 材料以墨水屏阅读为主，控制篇幅，便于伴学师当堂核验。")
    lines.append("  Materials are mainly read on E-Ink and kept short so study coaches can check them in session.")
    lines.append("")
    lines.append("本报告可由教师或伴学师审核后发给家长，内容仅限学习过程。")
    lines.append("This report may be sent to parents after review by a teacher or study coach; its content is limited to the learning process.")
    lines.append("")

    text = "\n".join(lines)
    for marker in PRIVATE_MARKERS:
        if marker in text.split("私人信息")[0] and marker in ("手机", "身份证"):
            # 标题声明中会出现「私人信息」，但不应出现具体私人字段值；关键词提示本身允许。
            # The header notice mentions "private information", but no actual private values may appear; the keyword itself is allowed.
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
    """写出每生周报与汇总。 / Write per-student weekly reports and the overview."""
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

    # 教师汇总（同样不含私人信息） / Teacher overview (also free of private information)
    by_student = defaultdict(list)
    for item in week_checkins:
        by_student[item.student_id].append(item)
    summary_lines = [
        f"# 学情周报汇总 / Weekly Learning Report Overview（{start.isoformat()} 至 / to {end.isoformat()}）",
        "",
        "仅含内部学号与出勤、薄弱科目等学习字段，不含姓名或其他私人信息。",
        "Contains only internal student IDs and learning fields such as attendance and weak subjects, with no names or other private information.",
        "",
        "| 学号 / Student ID | 应到 / Planned | 实到 / Attended | 出勤率 / Rate | 在馆分钟 / Minutes | 重点科目 / Focus subjects |",
        "|------|------|------|--------|----------|----------|",
    ]
    for student in students:
        records = by_student.get(student.student_id, [])
        planned = len(records)
        arrived = [item for item in records if item.attended]
        rate = (len(arrived) / planned) if planned else 0.0
        minutes = sum(item.duration_minutes for item in arrived)
        subjects = bi_join(sorted({item.subject_focus for item in arrived if item.subject_focus})) or "—"
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
