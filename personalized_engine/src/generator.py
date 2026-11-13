"""个性化内容生成：错题重练 + 按掌握度分层资料。

默认使用规则引擎。LLMGenerator 为大模型预留接口，本版本不调用任何外部 API。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from . import (
    Answer,
    KnowledgeMastery,
    MaterialSection,
    PracticeItem,
    Question,
    StudentMaterial,
    StudentProfile,
)
from .analyzer import top_weak_points


# 示例知识点的简短讲解（规则引擎内置，后续可由大模型替换）
KNOWLEDGE_TIPS = {
    "牛顿第二定律": "先明确研究对象，画受力分析图，再按 F=ma 列方程。注意力和加速度的方向一致，合力不要漏力或重复计算。",
    "受力分析": "隔离物体，标出重力、弹力、摩擦力等，检查是否有被忽略的约束力。建议先画示意图再列平衡或运动方程。",
    "动能定理": "合外力做功等于动能变化。先确定初末状态，再计算各力做功，注意位移方向与力的夹角。",
    "圆周运动": "向心力由指向圆心的合力提供，常用 F=mv²/r 或 F=mω²r。先找圆心和半径，再分析哪个力（或分力）充当向心力。",
    "动量守恒": "系统合外力为零或可忽略时，总动量守恒。先确认系统与过程，再按矢量方向列出守恒方程。",
    "离子反应": "先写出完整的电离情况，再删去不参加反应的Spectator离子，得到净离子方程式。注意难溶、弱电解质和气体。",
    "氧化还原": "先找化合价升降，确定氧化剂与还原剂，再配平电子转移。可用化合价升降法或离子电子法。",
    "化学平衡": "平衡移动看条件改变对正逆反应速率的影响。注意浓度、压强、温度对K和转化率的不同作用。",
    "细胞分裂": "区分有丝分裂与减数分裂的时期特征：染色体、染色单体和核DNA数量变化是常见考查点。",
    "遗传定律": "先判断分离定律还是自由组合定律，再写清亲本基因型。注意配子种类和性状分离比的适用条件。",
    "洋务运动": "抓住“中体西用”的主张、军事与民用工业代表企业，以及未能使中国富强的根本原因。",
    "辛亥革命": "关注武昌起义、中华民国成立和《临时约法》，理解其在推翻帝制与未完成反帝反封建任务两方面的评价。",
    "抗日战争": "分清阶段、战场和胜利原因，注意国共合作、敌后战场与国际反法西斯同盟的作用。",
    "改革开放": "从十一届三中全会起步，抓住家庭联产承包、经济特区和社会主义市场经济体制等关键节点。",
    "气候类型": "结合纬度、海陆位置和地形判断气候，用气温曲线与降水量柱状图核对类型特征。",
    "工业区位": "从原料、能源、市场、交通、劳动力和政策分析主导区位因素，注意产业转移带来的变化。",
    "河流地貌": "区分侵蚀、搬运与堆积，上游多峡谷，中下游多冲积平原和三角洲，注意凹岸侵蚀凸岸堆积。",
}


def tip_for(knowledge_point: str) -> str:
    if knowledge_point in KNOWLEDGE_TIPS:
        return KNOWLEDGE_TIPS[knowledge_point]
    return f"围绕「{knowledge_point}」回顾核心概念与典型题型，先巩固定义与适用条件，再练习综合应用。"


def layer_for(mastery_score: float, config: Optional[dict] = None) -> str:
    layers = (config or {}).get("layers") or {}
    basic_max = float(layers.get("basic_max") if layers.get("basic_max") is not None else 0.5)
    advanced_min = float(layers.get("advanced_min") if layers.get("advanced_min") is not None else 0.75)
    if mastery_score < basic_max:
        return "基础"
    if mastery_score >= advanced_min:
        return "拓展"
    return "中等"


def _question_map(questions: Iterable[Question]) -> dict[str, Question]:
    return {q.question_id: q for q in questions}


def _matches_kp(question: Question, knowledge_point: str, subject: str) -> bool:
    if subject and question.subject and question.subject != subject:
        return False
    return knowledge_point in question.knowledge_points


def _estimate_chars(material: StudentMaterial) -> int:
    total = len(material.summary or "") + 400
    for item in material.review_items:
        total += len(item.stem) + len(item.explanation) + 80
    for section in material.layered_sections:
        total += len(section.tips) + 60
        for item in section.items:
            total += len(item.stem) + len(item.explanation) + 80
    return total


def _estimate_pages(material: StudentMaterial, chars_per_page: int) -> float:
    chars_per_page = chars_per_page or 800
    return round(_estimate_chars(material) / chars_per_page, 2)


class MaterialGenerator(ABC):
    """内容生成器接口。规则引擎与后续大模型实现都应遵循此接口。"""

    @abstractmethod
    def generate(
        self,
        profile: StudentProfile,
        mastery: list[KnowledgeMastery],
        questions: list[Question],
        config: Optional[dict] = None,
    ) -> StudentMaterial:
        raise NotImplementedError


class LLMGenerator(MaterialGenerator):
    """大模型生成器预留接口。

    后续可在本类中接入校内部署或本地大模型，用于改写题干、生成解析与分层讲解。
    当前版本禁止调用任何外部 API，也不会在默认流程中实例化并执行本类。
    """

    def generate(
        self,
        profile: StudentProfile,
        mastery: list[KnowledgeMastery],
        questions: list[Question],
        config: Optional[dict] = None,
    ) -> StudentMaterial:
        raise NotImplementedError(
            "LLMGenerator 为预留接口，本版本未实现，也未调用任何模型 API。"
            "请在 config.yaml 中保持 generator.backend: rule。"
        )


class RuleBasedGenerator(MaterialGenerator):
    """基于掌握度与题库的规则生成器。"""

    def generate(
        self,
        profile: StudentProfile,
        mastery: list[KnowledgeMastery],
        questions: list[Question],
        config: Optional[dict] = None,
    ) -> StudentMaterial:
        config = config or {}
        output_cfg = config.get("output") or {}
        weak_cfg = config.get("weak_points") or {}
        max_questions = int(output_cfg.get("max_questions") or 12)
        max_pages = float(output_cfg.get("max_pages") or 6)
        chars_per_page = int(output_cfg.get("chars_per_page") or 800)
        review_ratio = float(output_cfg.get("review_slot_ratio") or 0.5)
        max_weak = int(weak_cfg.get("max_weak_points") or 5)

        student = profile.student
        weak = top_weak_points(mastery, max_weak)
        qmap = _question_map(questions)
        used_ids: set[str] = set()

        review_budget = max(1, int(round(max_questions * review_ratio))) if max_questions else 0
        review_items: list[PracticeItem] = []
        # 为「同知识点新题」预留名额，避免原错题占满错题重练栏
        reserve_new = min(len(weak), max(1, review_budget // 3)) if review_budget > 1 and weak else 0
        original_budget = max(0, review_budget - reserve_new)

        # 1) 原错题重练：按薄弱知识点优先级，最近错题优先
        wrong_sorted = sorted(
            profile.wrong_answers,
            key=lambda a: (
                min(
                    (
                        next(
                            (i for i, w in enumerate(weak) if w.knowledge_point in a.knowledge_points and (not a.subject or a.subject == w.subject)),
                            max_weak,
                        ),
                    ),
                    default=max_weak,
                ),
                -(1 if any(a.exam_id == eid for eid in profile.recent_exam_ids[:3]) else 0),
                a.exam_id,
            ),
        )
        for answer in wrong_sorted:
            if len(review_items) >= original_budget or len(review_items) >= max_questions:
                break
            if answer.question_id in used_ids:
                continue
            question = qmap.get(answer.question_id)
            stem = question.stem if question else f"（原题 {answer.question_id}，题干预留，待补全试卷文本）"
            explanation = (question.explanation if question else "") or (
                f"本题考查 { '、'.join(answer.knowledge_points) or '相关知识点' }。"
                + (f"错误类型：{answer.error_type}。" if answer.error_type else "建议对照错因重做。")
            )
            review_items.append(
                PracticeItem(
                    question_id=answer.question_id,
                    subject=answer.subject or (question.subject if question else ""),
                    knowledge_points=list(answer.knowledge_points),
                    difficulty=question.difficulty if question else "中等",
                    stem=stem,
                    source="原错题",
                    origin_exam_id=answer.exam_id,
                    explanation=explanation,
                )
            )
            used_ids.add(answer.question_id)

        # 2) 同知识点新题（来自题库，排除已考原题）
        for point in weak:
            if len(review_items) >= review_budget or len(review_items) >= max_questions:
                break
            target_layer = layer_for(point.mastery_score, config)
            candidates = [
                q
                for q in questions
                if q.question_id not in used_ids
                and not q.exam_id  # 题库新题，非试卷原题
                and _matches_kp(q, point.knowledge_point, point.subject)
            ]
            candidates.sort(
                key=lambda q: (0 if q.difficulty == target_layer else 1, q.question_id)
            )
            if not candidates:
                continue
            question = candidates[0]
            review_items.append(
                PracticeItem(
                    question_id=question.question_id,
                    subject=question.subject,
                    knowledge_points=list(question.knowledge_points),
                    difficulty=question.difficulty,
                    stem=question.stem,
                    source="同知识点新题",
                    origin_exam_id="",
                    explanation=question.explanation or tip_for(point.knowledge_point),
                )
            )
            used_ids.add(question.question_id)

        # 3) 分层资料：每个优先知识点一节，并配不超过剩余名额的练习
        layered_sections: list[MaterialSection] = []
        remaining = max(0, max_questions - len(review_items))
        for point in weak:
            layer = layer_for(point.mastery_score, config)
            section_items: list[PracticeItem] = []
            if remaining > 0:
                candidates = [
                    q
                    for q in questions
                    if q.question_id not in used_ids
                    and not q.exam_id
                    and _matches_kp(q, point.knowledge_point, point.subject)
                    and q.difficulty == layer
                ]
                if not candidates:
                    candidates = [
                        q
                        for q in questions
                        if q.question_id not in used_ids
                        and not q.exam_id
                        and _matches_kp(q, point.knowledge_point, point.subject)
                    ]
                if candidates:
                    question = candidates[0]
                    section_items.append(
                        PracticeItem(
                            question_id=question.question_id,
                            subject=question.subject,
                            knowledge_points=list(question.knowledge_points),
                            difficulty=question.difficulty,
                            stem=question.stem,
                            source="分层练习",
                            explanation=question.explanation or tip_for(point.knowledge_point),
                        )
                    )
                    used_ids.add(question.question_id)
                    remaining -= 1
            layered_sections.append(
                MaterialSection(
                    knowledge_point=point.knowledge_point,
                    subject=point.subject,
                    layer=layer,
                    mastery_score=point.mastery_score,
                    tips=tip_for(point.knowledge_point),
                    items=section_items,
                )
            )

        avg_text = "、".join(
            f"{sub} {ratio:.0%}" for sub, ratio in (profile.average_scores or {}).items()
        ) or "暂无成绩"
        weak_text = "、".join(
            f"{w.subject}-{w.knowledge_point}（掌握度 {w.mastery_score:.0%}，{w.recent_trend}）"
            for w in weak
        ) or "暂无足够作答数据"
        summary = (
            f"{student.grade}{student.class_name}、选科{student.subject_track or '未填写'}。"
            f"已纳入 {profile.exam_count} 次考试，科目均分（得分率）：{avg_text}。"
            f"优先关注：{weak_text}。"
        )

        material = StudentMaterial(
            student=student,
            summary=summary,
            weak_points=weak,
            review_items=review_items,
            layered_sections=layered_sections,
            question_count=len(review_items) + sum(len(s.items) for s in layered_sections),
            estimated_pages=0.0,
        )
        material.estimated_pages = _estimate_pages(material, chars_per_page)

        # 若超出页数上限，从分层练习末尾开始裁剪
        while (
            material.estimated_pages > max_pages
            and (material.layered_sections or material.review_items)
        ):
            trimmed = False
            for section in reversed(material.layered_sections):
                if section.items:
                    section.items.pop()
                    trimmed = True
                    break
            if not trimmed and material.review_items:
                material.review_items.pop()
                trimmed = True
            if not trimmed:
                break
            material.question_count = len(material.review_items) + sum(
                len(s.items) for s in material.layered_sections
            )
            material.estimated_pages = _estimate_pages(material, chars_per_page)

        return material


def get_generator(config: Optional[dict] = None) -> MaterialGenerator:
    backend = ((config or {}).get("generator") or {}).get("backend", "rule")
    if str(backend).lower() in {"llm", "large_model", "gpt"}:
        return LLMGenerator()
    return RuleBasedGenerator()


def generate_personalized_materials(
    profiles: list[StudentProfile],
    mastery_by_student: dict[str, list[KnowledgeMastery]],
    questions: list[Question],
    config: Optional[dict] = None,
) -> list[StudentMaterial]:
    generator = get_generator(config)
    materials = []
    for profile in profiles:
        mastery = mastery_by_student.get(profile.student.student_id, [])
        materials.append(generator.generate(profile, mastery, questions, config))
    return materials
