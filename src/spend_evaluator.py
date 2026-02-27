from copy import deepcopy
from typing import Dict, Any

from src.risk_engine import calculate_risk

def evaluate_spend(profile: Dict[str, Any], amount: float) -> Dict[str, Any]:
    """
    Returns risk impact of a one-time discretionary spend.
    For MVP: spending reduces cash_savings only.
    """
    if amount < 0:
        raise ValueError("amount must be non-negative")

    before = calculate_risk(profile)

    updated = deepcopy(profile)
    updated["cash_savings"] = max(0.0, float(updated["cash_savings"]) - float(amount))

    after = calculate_risk(updated)

    before_score = float(before["risk_score"])
    after_score = float(after["risk_score"])

    delta_points = round(after_score - before_score, 1)
    delta_percent = round((delta_points / before_score * 100.0), 1) if before_score > 0 else None
    
    decision = classify_spend(before, after, delta_points)

    return {
        "amount": round(float(amount), 2),
        "risk_before": before,
        "risk_after": after,
        "delta_points": delta_points,
        "delta_percent": delta_percent,
        "cash_before": float(profile["cash_savings"]),
        "cash_after": float(updated["cash_savings"]),
        "decision": decision,
    }

def classify_spend(risk_before: dict, risk_after: dict, delta_points: float) -> dict:
    runway_after = float(risk_after["metrics"]["months_runway"])

    # Hard stop cases
    if delta_points >= 3.0 or runway_after < 0.25:
        return {
            "label": "NOT RECOMMENDED",
            "badge": "❌",
            "reason": "This spend meaningfully increases your risk or leaves you with an extremely low cash buffer."
        }

    # Warning cases
    if delta_points >= 1.0 or runway_after < 1.0:
        return {
            "label": "CAUTION",
            "badge": "⚠️",
            "reason": "This increases your financial risk or keeps your cash buffer under 1 month."
        }

    return {
        "label": "SAFE",
        "badge": "✅",
        "reason": "This has minimal impact on your short-term financial resilience."
    }

if __name__ == "__main__":
    # quick local test
    sample_profile = {
        "monthly_income": 4200,
        "monthly_fixed_expenses": 2200,
        "monthly_variable_expenses": 900,
        "cash_savings": 1800,
        "debt_balance": 12000,
        "debt_apr": 24.99,
    }

    for amt in [50, 120, 300, 800]:
        out = evaluate_spend(sample_profile, amt)
        print("\n=== Spend Test ===")
        print(f"Spend: ${out['amount']}")
        print(f"Cash: ${out['cash_before']:.2f} -> ${out['cash_after']:.2f}")
        print(f"Risk: {out['risk_before']['risk_score']} -> {out['risk_after']['risk_score']}")
        print(f"Delta: {out['delta_points']} points ({out['delta_percent']}%)")
        print(
            f"Runway: {out['risk_before']['metrics']['months_runway']} -> {out['risk_after']['metrics']['months_runway']}"
        )
        print(f"Decision: {out['decision']['badge']} {out['decision']['label']}")
        print(f"Why: {out['decision']['reason']}")