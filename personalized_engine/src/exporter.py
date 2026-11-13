"""导出每生一份 Markdown 材料，以及一份教师审核摘要。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from . import StudentMaterial


def _now_text() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M") + "（Asia/Shanghai）"


def _pct(value: float) -> str:
    return f"{value:.0%}"


def render_student_markdown(material: StudentMaterial) -> str:
    student = material.student
    lines = [
        f"# 个性化学习材料 — {student.student_id}",
        "",
        f"- 年级：{student.grade or '未填'}",
        f"- 班级：{student.class_name or '未填'}",
        f"- 选科：{student.subject_track or '未填'}（{'、'.join(student.subjects) or '未填'}）",
        f"- 练习题量：{material.question_count} 题",
        f"- 预估页数：{material.estimated_pages} 页（适配墨水屏）",
        "",
        "## 学情摘要",
        "",
        material.summary,
        "",
        "## 薄弱知识点（优先）",
        "",
    ]
    if not material.weak_points:
        lines.append("暂无足够作答数据，未能诊断薄弱点。")
        lines.append("")
    else:
        lines.extend(
            [
                "| 科目 | 知识点 | 掌握度 | 趋势 | 出现次数 | 优先级 |",
                "|------|--------|--------|------|----------|--------|",
            ]
        )
        for point in material.weak_points:
            lines.append(
                f"| {point.subject} | {point.knowledge_point} | {_pct(point.mastery_score)} "
                f"| {point.recent_trend} | {point.frequency} | {point.recommend_priority} |"
            )
        lines.append("")

    lines.extend(["## 错题重练", ""])
    if not material.review_items:
        lines.append("本次未编排错题重练（可能没有错题或已达容量上限）。")
        lines.append("")
    else:
        for index, item in enumerate(material.review_items, start=1):
            kps = "、".join(item.knowledge_points) or "未标注"
            origin = f"，来源考试 `{item.origin_exam_id}`" if item.origin_exam_id else ""
            lines.append(f"### {index}. [{item.source}] {item.question_id}")
            lines.append("")
            lines.append(f"- 科目：{item.subject or '未分科'}　难度：{item.difficulty}　知识点：{kps}{origin}")
            lines.append("")
            lines.append(item.stem or "（题干待补）")
            lines.append("")
            if item.explanation:
                lines.append(f"> 提示：{item.explanation}")
                lines.append("")

    lines.extend(["## 分层资料", ""])
    if not material.layered_sections:
        lines.append("本次未生成分层资料。")
        lines.append("")
    else:
        for section in material.layered_sections:
            lines.append(
                f"### {section.subject} · {section.knowledge_point}（{section.layer}，掌握度 {_pct(section.mastery_score)}）"
            )
            lines.append("")
            lines.append(section.tips)
            lines.append("")
            if not section.items:
                lines.append("（本题点以概念巩固为主，未再附加新题，以避免超出墨水屏容量。）")
                lines.append("")
            else:
                for index, item in enumerate(section.items, start=1):
                    lines.append(f"**练习 {index}**（{item.question_id}，{item.difficulty}）")
                    lines.append("")
                    lines.append(item.stem or "（题干待补）")
                    lines.append("")
                    if item.explanation:
                        lines.append(f"> 提示：{item.explanation}")
                        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "本材料由规则引擎自动生成，须经任课教师审核后再发放。请勿写入或传播学生真实姓名、联系方式等私人信息。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_teacher_summary(materials: list[StudentMaterial]) -> str:
    lines = [
        "# 教师审核摘要",
        "",
        f"- 生成时间：{_now_text()}",
        f"- 学生人数：{len(materials)}",
        f"- 使用说明：请按班级快速浏览薄弱点与题量，确认或删改后再下发到墨水屏 / 打印。",
        "",
        "## 班级概览",
        "",
    ]

    by_class: dict[str, list[StudentMaterial]] = {}
    for material in materials:
        key = f"{material.student.grade}{material.student.class_name}" or "未分班"
        by_class.setdefault(key, []).append(material)

    lines.extend(
        [
            "| 班级 | 人数 | 高优先级薄弱点出现较多的知识点 |",
            "|------|------|--------------------------------|",
        ]
    )
    for class_name, group in sorted(by_class.items()):
        kp_count: dict[str, int] = {}
        for material in group:
            for point in material.weak_points:
                if point.recommend_priority == "高":
                    name = f"{point.subject}-{point.knowledge_point}"
                    kp_count[name] = kp_count.get(name, 0) + 1
        top = "、".join(
            f"{name}（{count}人）"
            for name, count in sorted(kp_count.items(), key=lambda x: -x[1])[:4]
        ) or "暂无"
        lines.append(f"| {class_name} | {len(group)} | {top} |")
    lines.append("")

    lines.extend(["## 逐生摘要", ""])
    for material in materials:
        student = material.student
        weak = "、".join(
            f"{p.subject}-{p.knowledge_point}（{_pct(p.mastery_score)}，{p.recent_trend}，优先级{p.recommend_priority}）"
            for p in material.weak_points[:5]
        ) or "暂无"
        focus = "、".join(
            f"{p.knowledge_point}"
            for p in material.weak_points
            if p.recommend_priority == "高"
        ) or "按中等优先级知识点巩固即可"
        review_n = len(material.review_items)
        layer_n = sum(len(s.items) for s in material.layered_sections)
        layer_desc = "、".join(
            f"{s.knowledge_point}-{s.layer}" for s in material.layered_sections
        ) or "无"
        lines.extend(
            [
                f"### {student.student_id}（{student.grade}{student.class_name} · {student.subject_track}）",
                "",
                f"- 主要薄弱点：{weak}",
                f"- 建议重点：{focus}",
                f"- 本次推送：错题重练 {review_n} 题，分层练习 {layer_n} 题；分层安排：{layer_desc}",
                f"- 预估页数：{material.estimated_pages} 页",
                f"- 请审核：题量是否合适、原错题是否需要替换或删除、讲解是否需要补充。",
                "",
            ]
        )
    lines.extend(
        [
            "---",
            "",
            "摘要只使用内部学号与学习字段，不含学生真实姓名或其他私人信息。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def export_to_markdown(
    materials: list[StudentMaterial],
    output_dir: str | Path,
    config: Optional[dict] = None,
) -> dict:
    output = Path(output_dir)
    students_dir = output / "students"
    students_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for material in materials:
        path = students_dir / f"{material.student.student_id}.md"
        path.write_text(render_student_markdown(material), encoding="utf-8")
        written.append(path)

    summary_name = ((config or {}).get("output") or {}).get(
        "teacher_summary_filename", "教师审核摘要.md"
    )
    summary_path = output / summary_name
    summary_path.write_text(render_teacher_summary(materials), encoding="utf-8")
    return {
        "student_files": written,
        "teacher_summary": summary_path,
        "count": len(materials),
    }
