"""中英双语显示辅助。

Bilingual (Chinese-English) display helpers.

只用于生成材料、报告和命令行提示中的显示文字；数据中的中文取值（如科目、分层、
优先级、情景名称）保持不变，因此不会影响数据格式、函数行为或已有脚本。

Used only for display text in generated materials, reports and CLI messages.
Chinese data values (subjects, layers, priorities, scenario labels, etc.) stay
unchanged, so data formats, function behavior and existing scripts are unaffected.
"""

from __future__ import annotations

import re
from typing import Iterable

# 常用中文术语 → 英文。未收录的词（如具体知识点、题干）原样显示。
# Common Chinese terms → English. Terms not listed (e.g. specific knowledge
# points or question stems) are shown as-is.
TERMS: dict[str, str] = {
    # 科目 / Subjects
    "物理": "Physics",
    "化学": "Chemistry",
    "生物": "Biology",
    "历史": "History",
    "地理": "Geography",
    "政治": "Politics",
    "未分科": "Unassigned subject",
    # 选科组合 / Subject combinations
    "物化生": "Physics-Chemistry-Biology",
    "史地生": "History-Geography-Biology",
    "物化地": "Physics-Chemistry-Geography",
    "史地政": "History-Geography-Politics",
    "物生地": "Physics-Biology-Geography",
    "史政生": "History-Politics-Biology",
    # 年级 / Grades
    "高一": "Senior 1",
    "高二": "Senior 2",
    "高三": "Senior 3",
    # 分层 / Layers
    "基础": "Basic",
    "中等": "Intermediate",
    "拓展": "Advanced",
    # 优先级 / Priorities
    "高": "High",
    "中": "Medium",
    "低": "Low",
    # 趋势 / Trends
    "下降": "Declining",
    "上升": "Rising",
    "平稳": "Stable",
    "数据不足": "Insufficient data",
    # 题目来源 / Question sources
    "原错题": "Original wrong question",
    "同知识点新题": "New question, same knowledge point",
    "分层练习": "Tiered practice",
    # 财务情景 / Finance scenarios
    "保守": "Conservative",
    "中性": "Neutral",
    "乐观": "Optimistic",
    # 自习室分区 / Study-room zones
    "理科辅导区": "Science tutoring zone",
    "文科辅导区": "Humanities tutoring zone",
    # 场次 / Sessions
    "工作日傍晚": "Weekday late afternoon",
    "工作日晚间": "Weekday evening",
    "周末上午": "Weekend morning",
    "周末下午": "Weekend afternoon",
    "周末晚间": "Weekend evening",
    # 出勤 / Attendance
    "已到": "Attended",
    "未到": "Absent",
    # 示例知识点 / Sample knowledge points
    "牛顿第二定律": "Newton's second law",
    "受力分析": "Force analysis",
    "动能定理": "Work-energy theorem",
    "圆周运动": "Circular motion",
    "动量守恒": "Conservation of momentum",
    "离子反应": "Ionic reactions",
    "氧化还原": "Redox reactions",
    "化学平衡": "Chemical equilibrium",
    "细胞分裂": "Cell division",
    "遗传定律": "Laws of inheritance",
    "洋务运动": "Self-Strengthening Movement",
    "辛亥革命": "1911 Revolution",
    "抗日战争": "War of Resistance against Japan",
    "改革开放": "Reform and Opening-up",
    "气候类型": "Climate types",
    "工业区位": "Industrial location",
    "河流地貌": "Fluvial landforms",
    # 错误类型 / Error types
    "概念混淆": "Concept confusion",
    "计算错误": "Calculation error",
    "审题不清": "Misread the question",
    "知识遗漏": "Knowledge gap",
    "计算失误": "Calculation slip",
    "配平错误": "Balancing error",
    "公式记混": "Mixed up formulas",
    "受力漏力": "Missed a force",
    "漏画摩擦力": "Forgot to draw friction",
    "方向未考虑": "Direction not considered",
    "加速度方向": "Acceleration direction",
    "史实记忆不准": "Inaccurate recall of historical facts",
    "时间节点记混": "Mixed up dates",
    "因果分析不足": "Insufficient cause-and-effect analysis",
    "评价不全面": "Incomplete evaluation",
}

WEEKDAYS_ZH = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
WEEKDAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _class_en(text: str) -> str:
    """「3班」→「Class 3」；不匹配返回空串。 / "3班" → "Class 3"; empty string if no match."""
    match = re.fullmatch(r"(\d+)班", text or "")
    return f"Class {match.group(1)}" if match else ""


def en(term: str) -> str:
    """返回英文译名；未收录则原样返回。 / Return the English term, or the input if unknown."""
    text = (term or "").strip()
    return TERMS.get(text) or _class_en(text) or term


def bi(term: str, sep: str = " / ") -> str:
    """返回「中文 / English」；未收录则只返回原文。

    Return "Chinese / English"; return the original text alone if no translation is known.
    """
    text = (term or "").strip()
    english = TERMS.get(text) or _class_en(text)
    if not english or english == text:
        return term
    return f"{text}{sep}{english}"


def bi_join(terms: Iterable[str], sep_zh: str = "、", sep_en: str = ", ") -> str:
    """把一组术语拼成「中文列表 / English list」。 / Join terms as "Chinese list / English list"."""
    items = [str(item) for item in terms if str(item).strip()]
    if not items:
        return ""
    zh = sep_zh.join(items)
    english = sep_en.join(en(item) for item in items)
    return zh if english == ", ".join(items) or english == zh else f"{zh} / {english}"


def weekday_bi(index: int) -> str:
    """0=周一。返回「周一 / Mon」。 / 0 = Monday. Returns "周一 / Mon"."""
    return f"{WEEKDAYS_ZH[index % 7]} / {WEEKDAYS_EN[index % 7]}"
