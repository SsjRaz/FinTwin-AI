import json
from pathlib import Path

import streamlit as st

from src.spend_evaluator import evaluate_spend


def load_profiles() -> list[dict]:
    path = Path("data/sample_profiles.json")
    return json.loads(path.read_text(encoding="utf-8"))


st.set_page_config(page_title="FinTwin AI", layout="wide")

st.title("FinTwin AI — Spend Decision MVP")
st.caption("Checks how a purchase changes your short-term financial safety buffer (MVP).")

profiles = load_profiles()
profile_names = [p["name"] for p in profiles]

col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.subheader("Profile")
    choice = st.selectbox("Choose a sample profile", profile_names, index=0)
    base_profile = next(p for p in profiles if p["name"] == choice).copy()

    st.divider()
    st.subheader("Inputs")

    # Let user tweak inputs (optional but great for demo)
    base_profile["monthly_income"] = st.number_input(
        "Monthly income ($)",
        min_value=0.0,
        value=float(base_profile["monthly_income"]),
        step=100.0,
    )
    base_profile["monthly_fixed_expenses"] = st.number_input(
        "Fixed expenses ($)",
        min_value=0.0,
        value=float(base_profile["monthly_fixed_expenses"]),
        step=50.0,
    )
    base_profile["monthly_variable_expenses"] = st.number_input(
        "Variable expenses ($)",
        min_value=0.0,
        value=float(base_profile["monthly_variable_expenses"]),
        step=50.0,
    )
    base_profile["cash_savings"] = st.number_input(
        "Cash savings ($)",
        min_value=0.0,
        value=float(base_profile["cash_savings"]),
        step=100.0,
    )
    base_profile["debt_balance"] = st.number_input(
        "Total debt balance ($)",
        min_value=0.0,
        value=float(base_profile["debt_balance"]),
        step=100.0,
    )
    base_profile["debt_apr"] = st.number_input(
        "Debt APR (%)",
        min_value=0.0,
        max_value=60.0,
        value=float(base_profile["debt_apr"]),
        step=0.5,
    )

    st.divider()
    st.subheader("Spend Check")
    spend_amount = st.slider(
        "How much do you want to spend? ($)",
        min_value=0,
        max_value=2000,
        value=120,
        step=10,
    )

    run = st.button("Evaluate Spend", type="primary")

with col_right:
    st.subheader("Result")

    if run:
        out = evaluate_spend(base_profile, float(spend_amount))

        decision = out["decision"]
        before = out["risk_before"]
        after = out["risk_after"]

        # Top summary
        st.markdown(f"## {decision['badge']} {decision['label']}")
        st.write(decision["reason"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Financial Risk Score (Before)", before["risk_score"])
        c2.metric("Financial Risk Score (After)", after["risk_score"], delta=f"{out['delta_points']} pts")
        c3.metric("Cash After", f"${out['cash_after']:.0f}", delta=f"-${out['amount']:.0f}")

        st.divider()

        # Human-readable emergency coverage (days)
        before_months = float(before["metrics"]["months_runway"])
        after_months = float(after["metrics"]["months_runway"])
        before_days = round(before_months * 30)
        after_days = round(after_months * 30)

        c4, c5, c6 = st.columns(3)
        c4.metric("Emergency Coverage (Before)", f"{before_days} days")
        c5.metric("Emergency Coverage (After)", f"{after_days} days")
        c6.metric("Debt Pressure", before["metrics"]["dti"])

        st.divider()
        st.subheader("Risk Breakdown")
        b1, b2, b3 = st.columns(3)
        b1.metric("Cash Stability", before["breakdown"]["liquidity_risk"])
        b2.metric("Debt Pressure", before["breakdown"]["debt_risk"])
        b3.metric("Monthly Balance Risk", before["breakdown"]["cashflow_risk"])

        st.caption("Note: This is a simulation MVP and not financial advice.")
    else:
        st.info("Pick a profile, choose a spend amount, then click **Evaluate Spend**.")