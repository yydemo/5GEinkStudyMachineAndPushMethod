"""导出每生一份 Markdown 材料，以及一份教师审核摘要。

Export one Markdown material pack per student, plus one teacher review summary.
生成的内容为中英双语。 / Generated content is bilingual (Chinese-English).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from . import StudentMaterial
from .generator import tip_for_en
from .i18n import bi, bi_join, en


def _now_text() -> str:
    """当前北京时间文字。 / Current Asia/Shanghai time as text."""
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M") + "（Asia/Shanghai）"


def _pct(value: float) -> str:
    """百分比格式。 / Percentage format."""
    return f"{value:.0%}"


def _or_missing(value: str) -> str:
    """空值显示为「未填 / Not provided」。 / Show empty values as "未填 / Not provided"."""
    return value or "未填 / Not provided"


def render_student_markdown(material: StudentMaterial) -> str:
    """渲染一名学生的双语学习材料。 / Render one student's bilingual learning material."""
    student = material.student
    subjects = bi_join(student.subjects) or "未填 / Not provided"
    lines = [
        f"# 个性化学习材料 / Personalized Learning Materials — {student.student_id}",
        "",
        f"- 年级 / Grade：{_or_missing(bi(student.grade))}",
        f"- 班级 / Class：{_or_missing(bi(student.class_name))}",
        f"- 选科 / Subject combination：{_or_missing(bi(student.subject_track))}（{subjects}）",
        f"- 练习题量 / Practice questions：{material.question_count} 题 / questions",
        f"- 预估页数 / Estimated pages：{material.estimated_pages} 页 / pages（适配墨水屏 / sized for E-Ink）",
        "",
        "## 学情摘要 / Learning Summary",
        "",
        material.summary,
        "",
    ]
    if material.summary_en:
        lines.extend([material.summary_en, ""])
    lines.extend(["## 薄弱知识点（优先） / Weak Knowledge Points (Priority)", ""])
    if not material.weak_points:
        lines.append("暂无足够作答数据，未能诊断薄弱点。 / Not enough answer data to diagnose weak points.")
        lines.append("")
    else:
        lines.extend(
            [
                "| 科目 / Subject | 知识点 / Knowledge point | 掌握度 / Mastery | 趋势 / Trend | 出现次数 / Occurrences | 优先级 / Priority |",
                "|------|--------|--------|------|----------|--------|",
            ]
        )
        for point in material.weak_points:
            lines.append(
                f"| {bi(point.subject)} | {bi(point.knowledge_point)} | {_pct(point.mastery_score)} "
                f"| {bi(point.recent_trend)} | {point.frequency} | {bi(point.recommend_priority)} |"
            )
        lines.append("")

    lines.extend(["## 错题重练 / Mistake Re-practice", ""])
    if not material.review_items:
        lines.append(
            "本次未编排错题重练（可能没有错题或已达容量上限）。"
            " / No mistake re-practice this time (no wrong answers, or the capacity limit was reached)."
        )
        lines.append("")
    else:
        for index, item in enumerate(material.review_items, start=1):
            kps = bi_join(item.knowledge_points) or "未标注 / Not tagged"
            origin = (
                f"，来源考试 / Source exam `{item.origin_exam_id}`" if item.origin_exam_id else ""
            )
            lines.append(f"### {index}. [{bi(item.source)}] {item.question_id}")
            lines.append("")
            lines.append(
                f"- 科目 / Subject：{bi(item.subject or '未分科')}　难度 / Difficulty：{bi(item.difficulty)}"
                f"　知识点 / Knowledge points：{kps}{origin}"
            )
            lines.append("")
            lines.append(item.stem or "（题干待补） / (Stem to be added)")
            lines.append("")
            if item.explanation:
                lines.append(f"> 提示 / Hint：{item.explanation}")
                lines.append("")

    lines.extend(["## 分层资料 / Tiered Materials", ""])
    if not material.layered_sections:
        lines.append("本次未生成分层资料。 / No tiered materials were generated this time.")
        lines.append("")
    else:
        for section in material.layered_sections:
            lines.append(
                f"### {bi(section.subject)} · {bi(section.knowledge_point)}"
                f"（{bi(section.layer)}，掌握度 / mastery {_pct(section.mastery_score)}）"
            )
            lines.append("")
            lines.append(section.tips)
            lines.append("")
            lines.append(tip_for_en(section.knowledge_point))
            lines.append("")
            if not section.items:
                lines.append(
                    "（本题点以概念巩固为主，未再附加新题，以避免超出墨水屏容量。）"
                    " / (This point focuses on consolidating concepts; no extra question was added, to stay within E-Ink capacity.)"
                )
                lines.append("")
            else:
                for index, item in enumerate(section.items, start=1):
                    lines.append(
                        f"**练习 / Practice {index}**（{item.question_id}，{bi(item.difficulty)}）"
                    )
                    lines.append("")
                    lines.append(item.stem or "（题干待补） / (Stem to be added)")
                    lines.append("")
                    if item.explanation:
                        lines.append(f"> 提示 / Hint：{item.explanation}")
                        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "本材料由规则引擎自动生成，须经任课教师审核后再发放。请勿写入或传播学生真实姓名、联系方式等私人信息。",
            "",
            "This material was generated automatically by the rule engine and must be reviewed by the subject teacher "
            "before distribution. Never add or share students' real names, contact details or other private information.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_teacher_summary(materials: list[StudentMaterial]) -> str:
    """渲染双语教师审核摘要。 / Render the bilingual teacher review summary."""
    lines = [
        "# 教师审核摘要 / Teacher Review Summary",
        "",
        f"- 生成时间 / Generated at：{_now_text()}",
        f"- 学生人数 / Students：{len(materials)}",
        "- 使用说明：请按班级快速浏览薄弱点与题量，确认或删改后再下发到墨水屏 / 打印。",
        "  How to use: skim weak points and question counts by class, confirm or edit, then push to E-Ink devices or print.",
        "",
        "## 班级概览 / Class Overview",
        "",
    ]

    by_class: dict[str, list[StudentMaterial]] = {}
    for material in materials:
        key = f"{material.student.grade}{material.student.class_name}" or "未分班"
        by_class.setdefault(key, []).append(material)

    lines.extend(
        [
            "| 班级 / Class | 人数 / Students | 高优先级薄弱点出现较多的知识点 / Most frequent high-priority weak points |",
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
            f"{name}（{count}人 / students）"
            for name, count in sorted(kp_count.items(), key=lambda x: -x[1])[:4]
        ) or "暂无 / None"
        class_label = "未分班 / No class" if class_name == "未分班" else class_name
        lines.append(f"| {class_label} | {len(group)} | {top} |")
    lines.append("")

    lines.extend(["## 逐生摘要 / Per-Student Summary", ""])
    for material in materials:
        student = material.student
        weak = "、".join(
            f"{p.subject}-{p.knowledge_point}（{_pct(p.mastery_score)}，{p.recent_trend}，优先级{p.recommend_priority}）"
            for p in material.weak_points[:5]
        ) or "暂无"
        weak_en = "; ".join(
            f"{en(p.subject)} - {en(p.knowledge_point)} ({_pct(p.mastery_score)}, {en(p.recent_trend)}, "
            f"priority {en(p.recommend_priority)})"
            for p in material.weak_points[:5]
        ) or "none"
        focus_points = [p.knowledge_point for p in material.weak_points if p.recommend_priority == "高"]
        focus = "、".join(focus_points) or "按中等优先级知识点巩固即可"
        focus_en = ", ".join(en(p) for p in focus_points) or "consolidating medium-priority points is enough"
        review_n = len(material.review_items)
        layer_n = sum(len(s.items) for s in material.layered_sections)
        layer_desc = "、".join(
            f"{s.knowledge_point}-{s.layer}" for s in material.layered_sections
        ) or "无"
        layer_desc_en = ", ".join(
            f"{en(s.knowledge_point)} - {en(s.layer)}" for s in material.layered_sections
        ) or "none"
        lines.extend(
            [
                f"### {student.student_id}（{bi(student.grade)} {bi(student.class_name)} · {bi(student.subject_track)}）",
                "",
                f"- 主要薄弱点：{weak}",
                f"  Main weak points: {weak_en}",
                f"- 建议重点：{focus}",
                f"  Suggested focus: {focus_en}",
                f"- 本次推送：错题重练 {review_n} 题，分层练习 {layer_n} 题；分层安排：{layer_desc}",
                f"  This push: {review_n} mistake re-practice questions, {layer_n} tiered practice questions; tiers: {layer_desc_en}",
                f"- 预估页数 / Estimated pages：{material.estimated_pages} 页 / pages",
                "- 请审核：题量是否合适、原错题是否需要替换或删除、讲解是否需要补充。",
                "  Please review: whether the question count is right, whether original wrong questions should be replaced or removed, and whether explanations need more detail.",
                "",
            ]
        )
    lines.extend(
        [
            "---",
            "",
            "摘要只使用内部学号与学习字段，不含学生真实姓名或其他私人信息。",
            "",
            "This summary uses only internal student IDs and learning fields; it contains no real student names or other private information.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def export_to_markdown(
    materials: list[StudentMaterial],
    output_dir: str | Path,
    config: Optional[dict] = None,
) -> dict:
    """写出每生材料与教师审核摘要。 / Write per-student materials and the teacher review summary."""
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
