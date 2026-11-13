"""按薄弱科目为学生安排自习场次与座位。

Assign study sessions and seats to students by their weak subject.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .. import KnowledgeMastery, Student
from ..i18n import bi, weekday_bi

# 星期名称（CSV 中保持中文取值）。 / Weekday names (kept as Chinese values in the CSV).
WEEKDAY_NAMES = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}

# 未配置时使用的默认场次。 / Default sessions used when none are configured.
DEFAULT_SLOTS = [
    {"id": "WD_PM", "label": "工作日傍晚", "weekdays": [1, 2, 3, 4, 5], "start": "16:30", "end": "18:30", "priority": 2},
    {"id": "WD_EV", "label": "工作日晚间", "weekdays": [1, 2, 3, 4, 5], "start": "19:00", "end": "21:00", "priority": 1},
    {"id": "WE_AM", "label": "周末上午", "weekdays": [6, 7], "start": "09:00", "end": "11:30", "priority": 4},
    {"id": "WE_PM", "label": "周末下午", "weekdays": [6, 7], "start": "14:00", "end": "16:30", "priority": 3},
    {"id": "WE_EV", "label": "周末晚间", "weekdays": [6, 7], "start": "19:00", "end": "21:00", "priority": 5},
]

# 未配置时使用的默认辅导分区。 / Default tutoring zones used when none are configured.
DEFAULT_ZONES = [
    {"name": "理科辅导区", "subjects": ["物理", "化学", "生物"], "seat_ids": [f"R{i:02d}" for i in range(1, 9)]},
    {"name": "文科辅导区", "subjects": ["历史", "地理", "政治"], "seat_ids": [f"W{i:02d}" for i in range(1, 9)]},
]


@dataclass
class SeatAssignment:
    """一条座位与场次安排。 / One seat-and-session assignment."""

    student_id: str
    weekday: int
    slot_id: str
    slot_label: str
    start: str
    end: str
    seat_id: str
    zone: str
    subject_focus: str
    knowledge_point: str = ""


def primary_weakness(
    student: Student, mastery_rows: Optional[list[KnowledgeMastery]]
) -> tuple[str, str]:
    """取最薄弱的（科目, 知识点）。 / Return the weakest (subject, knowledge point)."""
    rows = list(mastery_rows or [])
    if rows:
        top = rows[0]
        return top.subject, top.knowledge_point
    if student.subjects:
        return student.subjects[0], ""
    return "", ""


def _slots_from_config(config: dict) -> list[dict]:
    """读取并规范场次配置。 / Read and normalize session config."""
    slots = (config or {}).get("studyroom", {}).get("slots") or DEFAULT_SLOTS
    normalized = []
    for item in slots:
        normalized.append(
            {
                "id": item["id"],
                "label": item.get("label") or item.get("name") or item["id"],
                "weekdays": list(item.get("weekdays") or []),
                "start": item.get("start", ""),
                "end": item.get("end", ""),
                "priority": int(item.get("priority") or 99),
            }
        )
    return normalized


def _zones_from_config(config: dict) -> list[dict]:
    """读取分区配置。 / Read zone config."""
    zones = (config or {}).get("studyroom", {}).get("zones") or DEFAULT_ZONES
    result = []
    for zone in zones:
        result.append(
            {
                "name": zone["name"],
                "subjects": list(zone.get("subjects") or []),
                "seat_ids": list(zone.get("seat_ids") or []),
            }
        )
    return result


def _zone_for_subject(subject: str, zones: list[dict]) -> dict:
    """按科目找辅导区。 / Find the tutoring zone for a subject."""
    for zone in zones:
        if subject and subject in zone["subjects"]:
            return zone
    if zones:
        return zones[0]
    return {"name": "未分区", "subjects": [], "seat_ids": [f"S{i:02d}" for i in range(1, 17)]}


def _occurrences(slots: list[dict]) -> list[tuple[int, dict]]:
    """展开为（星期, 场次）并按优先级排序。 / Expand into (weekday, slot) pairs sorted by priority."""
    items: list[tuple[int, dict]] = []
    for slot in slots:
        for weekday in slot["weekdays"]:
            items.append((int(weekday), slot))
    items.sort(key=lambda pair: (pair[1]["priority"], pair[0], pair[1]["id"]))
    return items


def plan_sessions(
    students: Iterable[Student],
    mastery: Optional[dict[str, list[KnowledgeMastery]]] = None,
    config: Optional[dict] = None,
) -> list[SeatAssignment]:
    """按薄弱科目把学生安排到场次和座位，同一场次座位不冲突。

    Assign students to sessions and seats by weak subject, with no seat conflicts within a session.
    """
    config = config or {}
    mastery = mastery or {}
    slots = _slots_from_config(config)
    zones = _zones_from_config(config)
    sessions_per_week = int((config.get("studyroom") or {}).get("sessions_per_week") or 4)
    if sessions_per_week <= 0:
        raise ValueError("sessions_per_week 必须为正整数 / sessions_per_week must be a positive integer")

    occurrences = _occurrences(slots)
    if not occurrences:
        raise ValueError("未配置可用场次 / No available sessions configured")

    # 按薄弱科目聚集，便于同一场次由一位伴学师盯同一科目。
    # Group by weak subject so one study coach can cover the same subject in a session.
    prepared: list[tuple[Student, str, str]] = []
    for student in students:
        subject, point = primary_weakness(student, mastery.get(student.student_id))
        prepared.append((student, subject, point))
    prepared.sort(key=lambda item: (item[1] or "未分科", item[0].student_id))

    occupied: dict[tuple[int, str], set[str]] = {}
    assignments: list[SeatAssignment] = []

    for student, subject, point in prepared:
        zone = _zone_for_subject(subject, zones)
        assigned = 0
        for weekday, slot in occurrences:
            if assigned >= sessions_per_week:
                break
            key = (weekday, slot["id"])
            taken = occupied.setdefault(key, set())
            seat = next((seat_id for seat_id in zone["seat_ids"] if seat_id not in taken), None)
            if seat is None:
                continue
            taken.add(seat)
            assignments.append(
                SeatAssignment(
                    student_id=student.student_id,
                    weekday=weekday,
                    slot_id=slot["id"],
                    slot_label=slot["label"],
                    start=slot["start"],
                    end=slot["end"],
                    seat_id=seat,
                    zone=zone["name"],
                    subject_focus=subject,
                    knowledge_point=point,
                )
            )
            assigned += 1
        if assigned < sessions_per_week:
            raise ValueError(
                f"无法为 {student.student_id} 排满 {sessions_per_week} 场："
                "座位或场次不足，请增加座位数或减少每人场次"
                f" / Cannot schedule {sessions_per_week} sessions for {student.student_id}: "
                "not enough seats or sessions; add seats or reduce sessions per student"
            )

    assignments.sort(key=lambda item: (item.weekday, item.start, item.slot_id, item.seat_id))
    return assignments


def render_plan_markdown(assignments: list[SeatAssignment]) -> str:
    """渲染双语座位与场次表。 / Render the bilingual seat and session table."""
    lines = [
        "# 座位与场次安排 / Seat and Session Plan",
        "",
        "按学生薄弱科目优先安排到对应辅导区，同一场次内座位不重复。",
        "Students are placed in the tutoring zone matching their weak subject first; no seat is reused within a session.",
        "",
        "本表只使用内部学号与学习字段，不含姓名等私人信息。",
        "This table uses only internal student IDs and learning fields, with no names or other private information.",
        "",
        "| 星期 / Day | 场次 / Session | 时间 / Time | 学号 / Student ID | 座位 / Seat | 分区 / Zone | 重点科目 / Focus subject | 薄弱知识点 / Weak point |",
        "|------|------|------|------|------|------|----------|------------|",
    ]
    for item in assignments:
        point = item.knowledge_point or "—"
        subject = item.subject_focus or "—"
        time_range = f"{item.start}–{item.end}" if item.start or item.end else "—"
        lines.append(
            f"| {weekday_bi(item.weekday - 1) if 1 <= item.weekday <= 7 else item.weekday} | {bi(item.slot_label)} "
            f"| {time_range} | {item.student_id} | {item.seat_id} | {bi(item.zone)} "
            f"| {bi(subject)} | {bi(point)} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_plan(
    assignments: list[SeatAssignment],
    output_dir: str | Path,
) -> dict:
    """写出 Markdown 与 CSV（CSV 列名和取值保持不变）。 / Write Markdown and CSV (CSV columns and values unchanged)."""
    output_dir = Path(output_dir)
    target = output_dir / "studyroom"
    target.mkdir(parents=True, exist_ok=True)
    md_path = target / "座位与场次安排.md"
    csv_path = target / "座位与场次安排.csv"
    md_path.write_text(render_plan_markdown(assignments), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "weekday",
                "weekday_name",
                "slot_id",
                "slot_label",
                "start",
                "end",
                "student_id",
                "seat_id",
                "zone",
                "subject_focus",
                "knowledge_point",
            ],
        )
        writer.writeheader()
        for item in assignments:
            writer.writerow(
                {
                    "weekday": item.weekday,
                    "weekday_name": WEEKDAY_NAMES.get(item.weekday, ""),
                    "slot_id": item.slot_id,
                    "slot_label": item.slot_label,
                    "start": item.start,
                    "end": item.end,
                    "student_id": item.student_id,
                    "seat_id": item.seat_id,
                    "zone": item.zone,
                    "subject_focus": item.subject_focus,
                    "knowledge_point": item.knowledge_point,
                }
            )
    return {"markdown": md_path, "csv": csv_path, "count": len(assignments)}
