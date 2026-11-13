"""个性化引擎主流程入口。

Main pipeline entry point for the personalized engine.

示例 / Example:

    python -m src.main --data data/sample --out output
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from .analyzer import analyze_knowledge_mastery
from .cleaner import clean_dataset
from .data_loader import load_dataset
from .exporter import export_to_markdown
from .generator import generate_personalized_materials
from .profiler import build_student_profiles

ENGINE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ENGINE_ROOT / "config.yaml"


def load_config(path: Optional[str | Path] = None) -> dict:
    """读取 YAML 配置；文件不存在时返回空字典。 / Load the YAML config; return {} if the file is missing."""
    config_path = Path(path) if path else DEFAULT_CONFIG
    if not config_path.exists():
        return {}
    with config_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"配置文件应为 YAML 映射 / Config file must be a YAML mapping: {config_path}")
    return data


def _to_plain(value: Any) -> Any:
    """把 dataclass 递归转为普通字典/列表，便于写 JSON。 / Recursively convert dataclasses to plain dicts/lists for JSON."""
    if is_dataclass(value):
        return {k: _to_plain(v) for k, v in asdict(value).items()}
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    return value


def run_pipeline(
    data_dir: str | Path,
    output_dir: str | Path,
    config_path: Optional[str | Path] = None,
    save_processed: bool = False,
) -> dict:
    """读取 → 清洗 → 画像 → 掌握度 → 生成 → 导出。 / Load → clean → profile → mastery → generate → export."""
    config = load_config(config_path)
    raw = load_dataset(data_dir, config)
    cleaned = clean_dataset(raw, config)
    if not cleaned["students"]:
        raise SystemExit(f"未读取到学生数据，请检查目录 / No student data found, check the directory: {data_dir}")
    if not cleaned["answers"]:
        raise SystemExit(f"未读取到答题记录，请检查目录 / No answer records found, check the directory: {data_dir}")

    profiles = build_student_profiles(
        cleaned["students"],
        cleaned["scores"],
        answers=cleaned["answers"],
        exams=cleaned["exams"],
    )
    mastery = analyze_knowledge_mastery(
        profiles,
        answers=cleaned["answers"],
        exams=cleaned["exams"],
        config=config,
    )
    materials = generate_personalized_materials(
        profiles,
        mastery,
        cleaned["questions"],
        config,
    )
    output_dir = Path(output_dir)
    result = export_to_markdown(materials, output_dir, config)

    if save_processed:
        processed_dir = output_dir / "_processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "students": _to_plain(cleaned["students"]),
            "exams": _to_plain(cleaned["exams"]),
            "scores": _to_plain(cleaned["scores"]),
            "answers": _to_plain(cleaned["answers"]),
        }
        (processed_dir / "cleaned.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(
        f"已为 {result['count']} 名学生生成个性化材料，输出目录：{output_dir.resolve()}\n"
        f"Generated personalized materials for {result['count']} students. Output directory: {output_dir.resolve()}"
    )
    print(f"教师审核摘要 / Teacher review summary: {result['teacher_summary']}")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="个性化试卷与资料引擎 / Personalized exam and materials engine")
    parser.add_argument(
        "--data",
        default="data/sample",
        help="输入数据目录（含 students/scores/answers/question_bank 等，默认 data/sample） / Input data directory (students/scores/answers/question_bank etc., default data/sample)",
    )
    parser.add_argument("--out", default="output", help="输出目录（默认 output） / Output directory (default output)")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="YAML 配置文件路径 / Path to the YAML config file",
    )
    parser.add_argument(
        "--save-processed",
        action="store_true",
        help="将清洗后的数据快照写入输出目录的 _processed/ / Write a snapshot of cleaned data to _processed/ in the output directory",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    run_pipeline(
        data_dir=args.data,
        output_dir=args.out,
        config_path=args.config,
        save_processed=args.save_processed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
