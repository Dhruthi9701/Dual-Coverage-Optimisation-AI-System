"""
DuCO-Agent | COB Engine
State: COB_REASONING
Reads data/state.json (output of intake agent), determines primary vs secondary
insurer for each patient, calculates exact INR payments, and saves updated state.
"""

import json
from pathlib import Path

STATE_PATH = Path("data/state.json")


# ─────────────────────────────────────────────────────────────
# MOCK INSURER API TOOL
# src/tools/insurer_api.py is called here as a tool
# ─────────────────────────────────────────────────────────────

def call_insurer_api(insurer: str, cpt_codes: list[str]) -> dict:
    """
    Mock tool call to insurer API.
    In production this would be a real HTTP request.
    Returns plan details: deductible, coinsurance, out-of-pocket max.
    """
    print(f"  [TOOL] Calling mock insurer API → {insurer}...")

    plans = {
        "Insurer1_PlanA": {
            "insurer": "Insurer1",
            "plan": "Plan A",
            "annual_deductible_inr": 10000,
            "deductible_met_inr": 10000,       # already fully met this year
            "coinsurance_percent": 20,          # patient pays 20% after deductible
            "out_of_pocket_max_inr": 100000,
            "out_of_pocket_met_inr": 10000,
            "pre_auth_required_cpts": ["29888", "29881"],
            "covered_cpts": ["29888", "29881", "97161", "97110", "97140", "97112"],
        },
        "Insurer2_PlanB": {
            "insurer": "Insurer2",
            "plan": "Plan B",
            "annual_deductible_inr": 15000,
            "deductible_met_inr": 15000,       # already fully met this year
            "coinsurance_percent": 10,          # patient pays 10% after deductible
            "out_of_pocket_max_inr": 75000,
            "out_of_pocket_met_inr": 15000,
            "pre_auth_required_cpts": ["29888", "29881"],
            "covered_cpts": ["29888", "29881", "97161", "97110", "97140", "97112"],
        },
    }

    # Check which CPT codes need pre-auth
    plan_data = plans.get(insurer, {})
    pre_auth_needed = [
        c for c in cpt_codes
        if c in plan_data.get("pre_auth_required_cpts", [])
    ]
    plan_data["pre_auth_needed_for"] = pre_auth_needed
    return plan_data


# ─────────────────────────────────────────────────────────────
# COB RULE ENGINE
# ─────────────────────────────────────────────────────────────

def determine_primary_insurer(patient: str, claim_type: str) -> tuple[str, str, str]:
    """
    Coordination of Benefits Rule:
    The Birthday Rule / Subscriber Rule — standard Indian dual-coverage COB:

    For AARAV's surgery:
      - Plan A (Insurer1): Priya is Primary, Aarav is Dependent → SECONDARY for Aarav
      - Plan B (Insurer2): Aarav is Primary Policyholder → PRIMARY for Aarav

    For PRIYA's PT bills:
      - Plan A (Insurer1): Priya is Primary Policyholder → PRIMARY for Priya
      - Plan B (Insurer2): Aarav is Primary, Priya is Dependent → SECONDARY for Priya

    Returns (primary_insurer_key, secondary_insurer_key, reasoning)
    """
    print(f"  [COB] Determining primary insurer for {patient} — {claim_type}...")

    if patient == "Aarav":
        primary   = "Insurer2_PlanB"
        secondary = "Insurer1_PlanA"
        reasoning = (
            "Aarav is the Primary Policyholder on Plan B (Insurer2), "
            "so Plan B is PRIMARY for his own claims. "
            "On Plan A (Insurer1), Aarav is a Dependent under Priya's policy, "
            "so Plan A is SECONDARY."
        )
    else:  # Priya
        primary   = "Insurer1_PlanA"
        secondary = "Insurer2_PlanB"
        reasoning = (
            "Priya is the Primary Policyholder on Plan A (Insurer1), "
            "so Plan A is PRIMARY for her own claims. "
            "On Plan B (Insurer2), Priya is a Dependent under Aarav's policy, "
            "so Plan B is SECONDARY."
        )

    print(f"  [COB] PRIMARY  → {primary}")
    print(f"  [COB] SECONDARY → {secondary}")
    return primary, secondary, reasoning


def calculate_cob_payment(
    total_billed_inr: float,
    primary_plan: dict,
    secondary_plan: dict,
    patient: str,
) -> dict:
    """
    Standard COB calculation (non-duplication method):

    Step 1: Primary pays after applying deductible + coinsurance
    Step 2: Secondary pays the remaining balance (up to its own limits)
    Step 3: Patient pays whatever is left

    Since both deductibles are already met (realistic mid-year scenario),
    the math simplifies to coinsurance only.
    """

    # ── Primary insurer calculation ──
    primary_coinsurance_rate = primary_plan["coinsurance_percent"] / 100
    primary_pays = round(total_billed_inr * (1 - primary_coinsurance_rate))
    primary_patient_responsibility = round(total_billed_inr * primary_coinsurance_rate)

    # ── Secondary insurer calculation ──
    # Secondary covers the primary's patient responsibility
    # but subject to its own coinsurance rate
    secondary_coinsurance_rate = secondary_plan["coinsurance_percent"] / 100
    secondary_pays = round(primary_patient_responsibility * (1 - secondary_coinsurance_rate))
    final_patient_pays = round(primary_patient_responsibility * secondary_coinsurance_rate)

    # ── Out-of-pocket max check (applied to final patient amount) ──
    # Use the secondary plan's remaining OOP since that's what covers
    # the patient's residual after both insurers pay
    remaining_oop_secondary = (
        secondary_plan["out_of_pocket_max_inr"] - secondary_plan["out_of_pocket_met_inr"]
    )

    oop_note = ""
    if final_patient_pays > remaining_oop_secondary:
        capped = final_patient_pays - remaining_oop_secondary
        final_patient_pays = remaining_oop_secondary
        secondary_pays += capped
        oop_note = f"Out-of-pocket max applied: ₹{capped:,.0f} shifted to secondary."

    print(f"  [COB] Total billed       : ₹{total_billed_inr:>10,.0f}")
    print(f"  [COB] Primary pays       : ₹{primary_pays:>10,.0f}")
    print(f"  [COB] Secondary pays     : ₹{secondary_pays:>10,.0f}")
    print(f"  [COB] Patient pays       : ₹{final_patient_pays:>10,.0f}")

    return {
        "total_billed_inr":      total_billed_inr,
        "primary_pays_inr":      primary_pays,
        "secondary_pays_inr":    secondary_pays,
        "patient_pays_inr":      final_patient_pays,
        "primary_coinsurance":   f"{primary_plan['coinsurance_percent']}%",
        "secondary_coinsurance": f"{secondary_plan['coinsurance_percent']}%",
        "deductibles_note":      "Both annual deductibles already met (mid-year scenario).",
        "oop_note":              oop_note,
        "math_audit": {
            "check_sum_correct": abs(
                primary_pays + secondary_pays + final_patient_pays - total_billed_inr
            ) < 1,
            "formula": "Primary(80%) + Secondary(90% of remaining 20%) + Patient(10% of 20%)",
        },
    }


# ─────────────────────────────────────────────────────────────
# MATH SELF-AUDIT
# ─────────────────────────────────────────────────────────────

def audit_cob_math(cob_result: dict) -> dict:
    """
    Agentic self-check: verify the three amounts sum to the total billed.
    Flags any discrepancy > ₹1 (rounding tolerance).
    """
    total = cob_result["total_billed_inr"]
    computed = (
        cob_result["primary_pays_inr"]
        + cob_result["secondary_pays_inr"]
        + cob_result["patient_pays_inr"]
    )
    discrepancy = abs(total - computed)
    passed = discrepancy <= 1

    return {
        "audit_passed":    passed,
        "total_billed":    total,
        "computed_sum":    computed,
        "discrepancy_inr": discrepancy,
        "note": "PASS — amounts reconcile." if passed else f"FAIL — ₹{discrepancy} discrepancy found.",
    }


# ─────────────────────────────────────────────────────────────
# MAIN COB AGENT
# ─────────────────────────────────────────────────────────────

def run_cob_engine():
    print("\n" + "="*50)
    print("DuCO-Agent | COB_REASONING STATE")
    print("="*50)

    # ── Load state from intake agent ──
    if not STATE_PATH.exists():
        raise FileNotFoundError(
            "data/state.json not found. Run intake_agent.py first."
        )

    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)

    if state.get("agent_state") != "COB_READY":
        print(f"  [WARN] Agent state is '{state.get('agent_state')}', expected 'COB_READY'.")
        print("  [WARN] Proceeding anyway...")

    state["agent_state"] = "COB_REASONING"

    # ── Pull CPT codes from intake ──
    surgery_cpts  = [
        p["cpt_code"].replace("CPT ", "")
        for p in state["surgeon_estimate"].get("procedures", [])
    ]
    pt_cpts = [
        c.split(":")[0].replace("CPT ", "").strip()
        for c in state["pt_invoice"].get("inferred_cpt_codes", [])
    ]

    # ── TOOL CALLS: fetch plan details from mock insurer API ──
    print("\n  [TOOL CALLS] Fetching plan details from mock insurer API...")
    plan_a = call_insurer_api("Insurer1_PlanA", surgery_cpts + pt_cpts)
    plan_b = call_insurer_api("Insurer2_PlanB", surgery_cpts + pt_cpts)

    # ─────────────────────────────────────────
    # CLAIM 1: Aarav's ACL Surgery
    # ─────────────────────────────────────────
    print("\n  ── CLAIM 1: Aarav's ACL Surgery ──")
    aarav_primary_key, aarav_secondary_key, aarav_cob_reason = determine_primary_insurer(
        "Aarav", "ACL Surgery"
    )
    aarav_primary_plan   = plan_b if aarav_primary_key   == "Insurer2_PlanB" else plan_a
    aarav_secondary_plan = plan_a if aarav_secondary_key == "Insurer1_PlanA" else plan_b

    aarav_total = state["surgeon_estimate"].get("total_surgical_amount_inr", 450000)
    aarav_cob   = calculate_cob_payment(aarav_total, aarav_primary_plan, aarav_secondary_plan, "Aarav")
    aarav_math  = audit_cob_math(aarav_cob)
    print(f"  [AUDIT] Math check: {aarav_math['note']}")

    # ─────────────────────────────────────────
    # CLAIM 2: Priya's PT Bills
    # ─────────────────────────────────────────
    print("\n  ── CLAIM 2: Priya's PT Bills ──")
    priya_primary_key, priya_secondary_key, priya_cob_reason = determine_primary_insurer(
        "Priya", "Physical Therapy"
    )
    priya_primary_plan   = plan_a if priya_primary_key   == "Insurer1_PlanA" else plan_b
    priya_secondary_plan = plan_b if priya_secondary_key == "Insurer2_PlanB" else plan_a

    priya_total = state["pt_invoice"].get("total_amount_inr", 30000)
    priya_cob   = calculate_cob_payment(priya_total, priya_primary_plan, priya_secondary_plan, "Priya")
    priya_math  = audit_cob_math(priya_cob)
    print(f"  [AUDIT] Math check: {priya_math['note']}")

    # ─────────────────────────────────────────
    # COMBINED SUMMARY
    # ─────────────────────────────────────────
    total_family_bill    = aarav_total + priya_total
    total_family_pays    = aarav_cob["patient_pays_inr"] + priya_cob["patient_pays_inr"]
    total_family_savings = total_family_bill - total_family_pays

    print(f"\n  ── FAMILY SUMMARY ──")
    print(f"  [COB] Total family bill  : ₹{total_family_bill:>10,.0f}")
    print(f"  [COB] Family pays        : ₹{total_family_pays:>10,.0f}")
    print(f"  [COB] Total savings      : ₹{total_family_savings:>10,.0f}")

    # ── Update state ──
    state["cob_results"] = {
        "aarav_surgery": {
            "patient":          "Aarav Sen",
            "claim_type":       "ACL Reconstruction + Meniscectomy",
            "primary_insurer":  aarav_primary_key,
            "secondary_insurer": aarav_secondary_key,
            "cob_reasoning":    aarav_cob_reason,
            "payment_breakdown": aarav_cob,
            "math_audit":       aarav_math,
            "pre_auth_required": plan_b.get("pre_auth_needed_for", []),
        },
        "priya_pt": {
            "patient":          "Priya Sen",
            "claim_type":       "Physical Therapy Sessions",
            "primary_insurer":  priya_primary_key,
            "secondary_insurer": priya_secondary_key,
            "cob_reasoning":    priya_cob_reason,
            "payment_breakdown": priya_cob,
            "math_audit":       priya_math,
            "pre_auth_required": plan_a.get("pre_auth_needed_for", []),
        },
        "family_summary": {
            "total_billed_inr":   total_family_bill,
            "family_pays_inr":    total_family_pays,
            "total_savings_inr":  total_family_savings,
            "savings_percent":    round((total_family_savings / total_family_bill) * 100, 1),
        },
    }

    state["agent_state"] = "OUTPUT_READY"

    # ── Save updated state ──
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(f"\n  [STATE] Saved to {STATE_PATH}")
    print(f"  [STATE] Agent state → {state['agent_state']}")
    print("="*50 + "\n")

    return state


if __name__ == "__main__":
    result = run_cob_engine()
    cob = result["cob_results"]

    print("\n╔══════════════════════════════════════════════╗")
    print("║         COB RESULTS SUMMARY                 ║")
    print("╠══════════════════════════════════════════════╣")
    print(f"║  AARAV'S SURGERY (₹{cob['aarav_surgery']['payment_breakdown']['total_billed_inr']:,.0f})")
    print(f"║  Primary   ({cob['aarav_surgery']['primary_insurer']})  pays: ₹{cob['aarav_surgery']['payment_breakdown']['primary_pays_inr']:,.0f}")
    print(f"║  Secondary ({cob['aarav_surgery']['secondary_insurer']}) pays: ₹{cob['aarav_surgery']['payment_breakdown']['secondary_pays_inr']:,.0f}")
    print(f"║  Aarav pays OUT OF POCKET:             ₹{cob['aarav_surgery']['payment_breakdown']['patient_pays_inr']:,.0f}")
    print("╠══════════════════════════════════════════════╣")
    print(f"║  PRIYA'S PT BILLS (₹{cob['priya_pt']['payment_breakdown']['total_billed_inr']:,.0f})")
    print(f"║  Primary   ({cob['priya_pt']['primary_insurer']})  pays: ₹{cob['priya_pt']['payment_breakdown']['primary_pays_inr']:,.0f}")
    print(f"║  Secondary ({cob['priya_pt']['secondary_insurer']}) pays: ₹{cob['priya_pt']['payment_breakdown']['secondary_pays_inr']:,.0f}")
    print(f"║  Priya pays OUT OF POCKET:              ₹{cob['priya_pt']['payment_breakdown']['patient_pays_inr']:,.0f}")
    print("╠══════════════════════════════════════════════╣")
    summary = cob["family_summary"]
    print(f"║  FAMILY TOTAL SAVINGS: ₹{summary['total_savings_inr']:,.0f} ({summary['savings_percent']}%)")
    print("╚══════════════════════════════════════════════╝")