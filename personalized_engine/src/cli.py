"""AI 自习室与个性化引擎的命令行入口。

安装后可使用::

    eink-studyroom generate
    eink-studyroom report
    eink-studyroom finance
    eink-studyroom all

也可在未安装时执行 ``python -m src.cli``。原有 ``python -m src.main`` 仍然只跑个性化材料生成。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .analyzer import analyze_knowledge_mastery
from .cleaner import clean_dataset
from .data_loader import load_dataset
from .generator import generate_personalized_materials
from .main import DEFAULT_CONFIG, ENGINE_ROOT, load_config, run_pipeline
from .profiler import build_student_profiles
from .studyroom.checkin import load_checkins
from .studyroom.finance import run_finance
from .studyroom.planner import plan_sessions, write_plan
from .studyroom.weekly_report import parse_week_start, write_weekly_reports


def resolve_existing(path_value: str | Path, kind: str) -> Path:
    path = Path(path_value)
    if path.exists():
        return path
    fallback = ENGINE_ROOT / path_value
    if fallback.exists():
        return fallback
    raise SystemExit(f"未找到{kind}：{path_value}")


def resolve_config(path_value: Optional[str | Path]) -> Path:
    if path_value:
        path = Path(path_value)
        if path.exists():
            return path
        fallback = ENGINE_ROOT / path_value
        if fallback.exists():
            return fallback
        raise SystemExit(f"未找到配置文件：{path_value}")
    if DEFAULT_CONFIG.exists():
        return DEFAULT_CONFIG
    raise SystemExit(f"未找到默认配置文件：{DEFAULT_CONFIG}")


def resolve_output(path_value: str | Path) -> Path:
    return Path(path_value)


def _learning_context(data_dir: Path, config: dict) -> dict:
    raw = load_dataset(data_dir, config)
    cleaned = clean_dataset(raw, config)
    if not cleaned["students"]:
        raise SystemExit(f"未读取到学生数据，请检查目录：{data_dir}")
    profiles = build_student_profiles(
        cleaned["students"],
        cleaned["scores"],
        answers=cleaned["answers"],
        exams=cleaned["exams"],
    )
    mastery = {}
    if cleaned["answers"]:
        mastery = analyze_knowledge_mastery(
            profiles,
            answers=cleaned["answers"],
            exams=cleaned["exams"],
            config=config,
        )
    materials = []
    if cleaned["answers"] and cleaned["questions"]:
        materials = generate_personalized_materials(
            profiles,
            mastery,
            cleaned["questions"],
            config,
        )
    material_map = {item.student.student_id: item for item in materials}
    return {
        "cleaned": cleaned,
        "profiles": profiles,
        "mastery": mastery,
        "materials": material_map,
    }


def cmd_generate(args: argparse.Namespace) -> int:
    data_dir = resolve_existing(args.data, "数据目录")
    config_path = resolve_config(args.config)
    result = run_pipeline(
        data_dir=data_dir,
        output_dir=resolve_output(args.out),
        config_path=config_path,
        save_processed=getattr(args, "save_processed", False),
    )
    return 0 if result else 0


def cmd_report(args: argparse.Namespace) -> int:
    data_dir = resolve_existing(args.data, "数据目录")
    config_path = resolve_config(args.config)
    config = load_config(config_path)
    output_dir = resolve_output(args.out)

    context = _learning_context(data_dir, config)
    students = context["cleaned"]["students"]
    assignments = plan_sessions(students, context["mastery"], config)
    plan_result = write_plan(assignments, output_dir)

    try:
        checkins = load_checkins(data_dir)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    default_week = (config.get("studyroom") or {}).get("week_start")
    week_start = parse_week_start(args.week_start or default_week, checkins)
    report_result = write_weekly_reports(
        students=students,
        checkins=checkins,
        output_dir=output_dir,
        week_start=week_start,
        mastery=context["mastery"],
        assignments=assignments,
        materials=context["materials"],
    )
    print(f"已生成座位与场次安排：{plan_result['markdown'].resolve()}（共 {plan_result['count']} 条）")
    print(
        f"已为 {report_result['count']} 名学生生成学情周报"
        f"（{report_result['week_start'].isoformat()} 至 {report_result['week_end'].isoformat()}）："
        f"{Path(report_result['summary']).resolve()}"
    )
    return 0


def cmd_finance(args: argparse.Namespace) -> int:
    config_path = resolve_config(args.config)
    config = load_config(config_path)
    result = run_finance(config, resolve_output(args.out))
    print(f"已生成单店测算：{result['path'].resolve()}")
    for item in result["results"]:
        payback = (
            f"{item.payback_months_steady:.1f} 个月"
            if item.payback_months_steady is not None
            else "按当前假设无法回本"
        )
        print(
            f"  {item.label}：稳态月营收 {item.revenue_steady} 元，"
            f"稳态月利润 {item.profit_steady} 元，回本 {payback}"
        )
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    cmd_generate(args)
    cmd_report(args)
    cmd_finance(args)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eink-studyroom",
        description="墨水屏个性化学习材料引擎与 AI 自习室运营工具",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_io(target: argparse.ArgumentParser, include_data: bool = True) -> None:
        if include_data:
            target.add_argument(
                "--data",
                default="data/sample",
                help="输入数据目录（默认 data/sample，若不存在则回退到引擎自带示例目录）",
            )
        target.add_argument("--out", default="output", help="输出目录（默认 output）")
        target.add_argument(
            "--config",
            default=str(DEFAULT_CONFIG),
            help="YAML 配置文件路径",
        )

    p_gen = sub.add_parser("generate", help="生成每生个性化材料与教师审核摘要")
    add_io(p_gen)
    p_gen.add_argument(
        "--save-processed",
        action="store_true",
        help="将清洗后的数据快照写入输出目录的 _processed/",
    )
    p_gen.set_defaults(func=cmd_generate)

    p_report = sub.add_parser("report", help="生成座位场次安排与学情周报")
    add_io(p_report)
    p_report.add_argument(
        "--week-start",
        default=None,
        help="周报统计起始日（YYYY-MM-DD，将归一到当周周一；默认取配置或签到记录所在周）",
    )
    p_report.set_defaults(func=cmd_report)

    p_finance = sub.add_parser("finance", help="按配置测算单店财务模型")
    add_io(p_finance, include_data=False)
    p_finance.set_defaults(func=cmd_finance)

    p_all = sub.add_parser("all", help="依次执行 generate、report、finance")
    add_io(p_all)
    p_all.add_argument(
        "--save-processed",
        action="store_true",
        help="将清洗后的数据快照写入输出目录的 _processed/",
    )
    p_all.add_argument(
        "--week-start",
        default=None,
        help="周报统计起始日（YYYY-MM-DD，将归一到当周周一）",
    )
    p_all.set_defaults(func=cmd_all)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
