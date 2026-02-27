import json
from pathlib import Path
import math


def load_profile(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def score_liquidity(months_runway: float) -> float:
    # Smooth curve: very high risk when runway is near 0, decays as runway increases
    m = max(0.0, float(months_runway))
    score = 10 + 90 * math.exp(-m / 1.5)
    return clamp(score, 10, 95)


def score_debt(dti: float, apr: float) -> float:
    # dti here = total debt / annual income (rough)
    if dti < 0.10:
        base = 15
    elif dti < 0.30:
        base = 35
    elif dti < 0.60:
        base = 65
    else:
        base = 85

    penalty = 0
    if apr >= 30:
        penalty = 15
    elif apr >= 20:
        penalty = 10

    return clamp(base + penalty, 0, 100)


def score_cashflow(surplus: float, income: float) -> float:
    # surplus ratio = surplus / income
    if income <= 0:
        return 90
    ratio = surplus / income

    if ratio >= 0.20:
        return 10
    if ratio >= 0.10:
        return 30
    if ratio >= 0.0:
        return 60
    return 90


def calculate_risk(profile: dict) -> dict:
    income = float(profile["monthly_income"])
    fixed = float(profile["monthly_fixed_expenses"])
    variable = float(profile["monthly_variable_expenses"])
    cash = float(profile["cash_savings"])
    debt = float(profile["debt_balance"])
    apr = float(profile["debt_apr"])

    burn = fixed + variable
    months_runway = cash / burn if burn > 0 else 12.0
    surplus = income - burn
    annual_income = income * 12.0
    dti = (debt / annual_income) if annual_income > 0 else 1.0

    liq = score_liquidity(months_runway)
    debt_score = score_debt(dti, apr)
    cashflow = score_cashflow(surplus, income)

    risk = 0.40 * liq + 0.35 * debt_score + 0.25 * cashflow
    risk = clamp(risk, 0, 100)

    return {
        "risk_score": round(risk, 1),
        "breakdown": {
            "liquidity_risk": round(liq, 1),
            "debt_risk": round(debt_score, 1),
            "cashflow_risk": round(cashflow, 1),
        },
        "metrics": {
            "months_runway": round(months_runway, 2),
            "monthly_surplus": round(surplus, 2),
            "dti": round(dti, 3),
        },
    }


if __name__ == "__main__":
    profile = load_profile("data/sample_profile.json")
    result = calculate_risk(profile)

    print("\n=== FinTwin Risk Engine (MVP) ===")
    print(f"Risk Score: {result['risk_score']} / 100\n")
    print("Metrics:")
    for k, v in result["metrics"].items():
        print(f"  - {k}: {v}")

    print("\nBreakdown:")
    for k, v in result["breakdown"].items():
        print(f"  - {k}: {v}")
    print()