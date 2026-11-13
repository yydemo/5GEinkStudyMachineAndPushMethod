"""按假设参数测算单店月营收、月利润与回本月数。

本模块只做参数化计算，不把任何数字当作已核实的经营事实。
测算口径在 `calculate_scenario` 中写明，并会写入输出文档。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

SCENARIO_LABELS = {
    "conservative": "保守",
    "neutral": "中性",
    "optimistic": "乐观",
    "保守": "保守",
    "中性": "中性",
    "乐观": "乐观",
}

SCENARIO_ORDER = ("conservative", "neutral", "optimistic")

PARAM_KEYS = (
    "seats",
    "utilization",
    "monthly_fee",
    "renewal_rate",
    "rent",
    "labor",
    "equipment_amortization",
    "startup_cost",
)


def _as_float(value: Any, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"财务参数 {name} 必须是数字，实际为：{value!r}") from exc


def _yuan(value: float) -> int:
    """金额四舍五入到元。"""
    return int(round(value))


@dataclass(frozen=True)
class ScenarioResult:
    key: str
    label: str
    seats: int
    utilization: float
    monthly_fee: int
    renewal_rate: float
    rent: int
    labor: int
    equipment_amortization: int
    startup_cost: int
    monthly_cost: int
    revenue_by_utilization: int
    revenue_steady: int
    profit_by_utilization: int
    profit_steady: int
    payback_months_by_utilization: Optional[float]
    payback_months_steady: Optional[float]
    annual_revenue_steady: int
    annual_profit_steady: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def calculate_scenario(params: dict, key: str = "custom") -> ScenarioResult:
    """按一组假设参数计算单店情景。

    采用的公式（写入报告，便于复核）：

    - 按利用率月营收 = 座位数 × 利用率 × 月费
    - 稳态月营收（测算主口径）= 座位数 × 利用率 × 续费率 × 月费
    - 月固定成本 = 房租 + 人力 + 设备摊销
    - 月利润 = 对应口径月营收 − 月固定成本
    - 回本月数 = 启动成本 / 月利润（月利润 ≤ 0 时为无法回本）

    「稳态」把续费率视为对在席学生持续付费的折减，是偏保守的近似，
    不是会计上的确认收入方式。同时给出「按利用率、不折减续费」的对照口径，
    以便对照常见宣传中只强调上座率的算法。
    """
    missing = [name for name in PARAM_KEYS if name not in params]
    if missing:
        raise ValueError(f"财务情景缺少参数：{', '.join(missing)}")

    seats = int(round(_as_float(params["seats"], "seats")))
    utilization = _as_float(params["utilization"], "utilization")
    monthly_fee = _as_float(params["monthly_fee"], "monthly_fee")
    renewal_rate = _as_float(params["renewal_rate"], "renewal_rate")
    rent = _as_float(params["rent"], "rent")
    labor = _as_float(params["labor"], "labor")
    equipment_amortization = _as_float(params["equipment_amortization"], "equipment_amortization")
    startup_cost = _as_float(params["startup_cost"], "startup_cost")

    if seats <= 0:
        raise ValueError("座位数必须为正整数")
    if not 0 <= utilization <= 1:
        raise ValueError("利用率必须在 0 到 1 之间")
    if not 0 <= renewal_rate <= 1:
        raise ValueError("续费率必须在 0 到 1 之间")
    if monthly_fee < 0 or rent < 0 or labor < 0 or equipment_amortization < 0 or startup_cost < 0:
        raise ValueError("月费、房租、人力、设备摊销和启动成本不能为负数")

    monthly_cost = _yuan(rent + labor + equipment_amortization)
    revenue_by_utilization = _yuan(seats * utilization * monthly_fee)
    revenue_steady = _yuan(seats * utilization * renewal_rate * monthly_fee)
    profit_by_utilization = revenue_by_utilization - monthly_cost
    profit_steady = revenue_steady - monthly_cost

    def payback(profit: int) -> Optional[float]:
        if profit <= 0:
            return None
        return round(startup_cost / profit, 1)

    return ScenarioResult(
        key=key,
        label=SCENARIO_LABELS.get(key, key),
        seats=seats,
        utilization=utilization,
        monthly_fee=_yuan(monthly_fee),
        renewal_rate=renewal_rate,
        rent=_yuan(rent),
        labor=_yuan(labor),
        equipment_amortization=_yuan(equipment_amortization),
        startup_cost=_yuan(startup_cost),
        monthly_cost=monthly_cost,
        revenue_by_utilization=revenue_by_utilization,
        revenue_steady=revenue_steady,
        profit_by_utilization=profit_by_utilization,
        profit_steady=profit_steady,
        payback_months_by_utilization=payback(profit_by_utilization),
        payback_months_steady=payback(profit_steady),
        annual_revenue_steady=_yuan(revenue_steady * 12),
        annual_profit_steady=_yuan(profit_steady * 12),
    )


def load_scenarios(config: dict) -> list[ScenarioResult]:
    finance_cfg = (config or {}).get("studyroom", {}).get("finance", {})
    raw = finance_cfg.get("scenarios")
    if not raw or not isinstance(raw, dict):
        raise ValueError("config.yaml 中缺少 studyroom.finance.scenarios，无法测算")

    results: list[ScenarioResult] = []
    keys = [k for k in SCENARIO_ORDER if k in raw] + [k for k in raw if k not in SCENARIO_ORDER]
    for key in keys:
        params = raw[key]
        if not isinstance(params, dict):
            raise ValueError(f"情景 {key} 应为参数映射")
        results.append(calculate_scenario(params, key=key))
    return results


def _fmt_money(value: int) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}{abs(value):,} 元"


def _fmt_pct(value: float) -> str:
    return f"{value:.0%}"


def _fmt_payback(value: Optional[float]) -> str:
    if value is None:
        return "按当前假设无法回本"
    return f"{value:.1f} 个月"


def render_finance_report(results: list[ScenarioResult]) -> str:
    lines = [
        "# 单店测算",
        "",
        "> 本文件由程序根据 `config.yaml` 中的**假设参数**自动计算，",
        "> 不是已核实的经营事实，也不是对收益的承诺。",
        "> 行业宣传中的「百平百万」「数月回本」等口径未经独立核实，投资前请自行调整参数并复核。",
        "",
        "## 测算口径",
        "",
        "- 按利用率月营收 = 座位数 × 利用率 × 月费",
        "- **稳态月营收（主口径）** = 座位数 × 利用率 × 续费率 × 月费",
        "- 月固定成本 = 房租 + 人力 + 设备摊销",
        "- 月利润 = 对应口径月营收 − 月固定成本",
        "- 回本月数 = 启动成本 ÷ 月利润（月利润 ≤ 0 则标注无法回本）",
        "",
        "稳态口径把续费率视为对在席学生持续付费的折减，偏保守；",
        "「按利用率」口径不折减续费，更接近只强调上座率的宣传算法。两列对照列出。",
        "",
        "## 假设参数",
        "",
        "| 情景 | 座位数 | 利用率 | 月费 | 续费率 | 房租 | 人力 | 设备摊销 | 启动成本 |",
        "|------|--------|--------|------|--------|------|------|----------|----------|",
    ]
    for item in results:
        lines.append(
            f"| {item.label} | {item.seats} | {_fmt_pct(item.utilization)} "
            f"| {_fmt_money(item.monthly_fee)} | {_fmt_pct(item.renewal_rate)} "
            f"| {_fmt_money(item.rent)} | {_fmt_money(item.labor)} "
            f"| {_fmt_money(item.equipment_amortization)} | {_fmt_money(item.startup_cost)} |"
        )

    lines.extend(
        [
            "",
            "## 测算结果",
            "",
            "| 情景 | 月成本 | 按利用率月营收 | 按利用率月利润 | 按利用率回本 | 稳态月营收 | 稳态月利润 | 稳态回本 | 稳态年利润 |",
            "|------|--------|----------------|----------------|--------------|------------|------------|----------|------------|",
        ]
    )
    for item in results:
        lines.append(
            f"| {item.label} | {_fmt_money(item.monthly_cost)} "
            f"| {_fmt_money(item.revenue_by_utilization)} "
            f"| {_fmt_money(item.profit_by_utilization)} "
            f"| {_fmt_payback(item.payback_months_by_utilization)} "
            f"| {_fmt_money(item.revenue_steady)} "
            f"| {_fmt_money(item.profit_steady)} "
            f"| {_fmt_payback(item.payback_months_steady)} "
            f"| {_fmt_money(item.annual_profit_steady)} |"
        )

    lines.extend(
        [
            "",
            "## 阅读说明",
            "",
            "- 保守情景用于观察利用率不足、续费偏低、成本偏高时是否还能覆盖固定开支。",
            "- 中性情景用于观察较常见的假设组合下，两种口径的回本周期会相差多少。",
            "- 乐观情景用于对照品牌宣传中较常见的高利用率、高客单假设；即使测算出短期回本，也不应直接当作可实现目标。",
            "- 未计入税费、获客费用、退费、空置装修期和设备二次投入。实际经营还需自行补全。",
            "",
        ]
    )
    return "\n".join(lines)


def run_finance(config: dict, output_dir: str | Path) -> dict:
    results = load_scenarios(config)
    output_dir = Path(output_dir)
    target_dir = output_dir / "studyroom"
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "单店测算.md"
    path.write_text(render_finance_report(results), encoding="utf-8")
    return {"path": path, "results": results}
