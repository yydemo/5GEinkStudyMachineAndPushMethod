"""读取自习室签到记录。仅使用学号与学习相关字段。"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from ..data_loader import parse_bool
from ..main import ENGINE_ROOT


@dataclass
class Checkin:
    checkin_id: str
    student_id: str
    date: str
    slot_id: str
    seat_id: str
    subject_focus: str = ""
    planned_minutes: int = 0
    attended: bool = False
    duration_minutes: int = 0


ALLOWED_FIELDS = (
    "checkin_id",
    "student_id",
    "date",
    "slot_id",
    "seat_id",
    "subject_focus",
    "planned_minutes",
    "attended",
    "duration_minutes",
)


def _read_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"签到 JSON 应为对象数组：{path}")
        return data
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _to_int(value: object, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return default


def load_checkins(data_dir: str | Path) -> list[Checkin]:
    data_dir = Path(data_dir)
    candidates = [data_dir / "checkins.csv", data_dir / "checkins.json"]
    path = next((item for item in candidates if item.exists()), None)
    if path is None:
        raise FileNotFoundError(f"未找到签到文件 checkins.csv 或 checkins.json：{data_dir}")

    records: list[Checkin] = []
    for index, row in enumerate(_read_rows(path), start=1):
        cleaned = {key: (row.get(key) or "") for key in ALLOWED_FIELDS if key in row}
        student_id = str(cleaned.get("student_id", "")).strip()
        date = str(cleaned.get("date", "")).strip()
        if not student_id or not date:
            continue
        checkin_id = str(cleaned.get("checkin_id", "")).strip() or f"C{index:03d}"
        attended = parse_bool(cleaned.get("attended", False))
        duration = _to_int(cleaned.get("duration_minutes"), 0)
        if not attended:
            duration = 0
        records.append(
            Checkin(
                checkin_id=checkin_id,
                student_id=student_id,
                date=date,
                slot_id=str(cleaned.get("slot_id", "")).strip(),
                seat_id=str(cleaned.get("seat_id", "")).strip(),
                subject_focus=str(cleaned.get("subject_focus", "")).strip(),
                planned_minutes=_to_int(cleaned.get("planned_minutes"), 0),
                attended=attended,
                duration_minutes=duration,
            )
        )
    records.sort(key=lambda item: (item.date, item.slot_id, item.student_id))
    return records


def default_sample_dir() -> Path:
    return ENGINE_ROOT / "data" / "sample"
