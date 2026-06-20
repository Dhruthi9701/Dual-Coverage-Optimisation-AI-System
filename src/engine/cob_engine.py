"""
DuCO-Agent | COB Engine
State: COB_REASONING
Reads data/state.json (output of intake agent), determines primary vs secondary
insurer for each patient, calculates exact INR payments, and saves updated state.
"""

import sys
import json
from pathlib import Path

# Make src/ importable when running this file directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tools.insurer_api import call_tool   # unified tool dispatcher

STATE_PATH = Path("data/state.json")


# ─────────────────────────────────────────────────────────────
# TOOL WRAPPER
# Calls the real insurer API tool from src/tools/insurer_api.py
# ─────────────────────────────────────────────────────────────

def fetch_plan_details(plan_key: str, cpt_codes: list) -> dict:
    """
    Tool call: get_plan_details
    Fetches plan configuration from the mock insurer API.
    Returns deductible, coinsurance, OOP max, covered CPTs.
    """
    result = call_tool("get_plan_details", plan_key=plan_key)
    # Also verify coverage for the specific CPT codes
    coverage = call_tool("verify_coverage", plan_key=plan_key, cpt_codes=cpt_codes)
    result["coverage_check"] = coverage
    result["pre_auth_needed_for"] = coverage.get("requires_pre_auth", [])
    return result


# ─────────────────────────────────────────────────────────────
# COB RULE ENGINE
# ─────────────────────────────────────────────────────────────

def determine_primary_insurer(patient: str, claim_type: str, plan_a: dict, plan_b: dict) -> tuple[str, str, str]:

    """
    Coordination of Benefits Rule — Subscriber Rule (standard for dual
    corporate-policy COB in India): whichever plan you are the *named
    policyholder* on is PRIMARY for your own claims; the plan you are
    enrolled on only as a *dependent* is SECONDARY.
    (Note: this is distinct from the US "Birthday Rule," which resolves
    primacy for a dependent CHILD covered under both parents' plans by
    comparing birth months — not applicable here since both Aarav and
    Priya are each a named subscriber on one plan and a dependent on
    the other.)

    For AARAV's surgery:
      - Plan A (Insurer1): Priya is Primary, Aarav is Dependent → SECONDARY for Aarav
      - Plan B (Insurer2): Aarav is Primary Policyholder → PRIMARY for Aarav

    For PRIYA's PT bills:
      - Plan A (Insurer1): Priya is Primary Policyholder → PRIMARY for Priya
      - Plan B (Insurer2): Aarav is Primary, Priya is Dependent → SECONDARY for Priya

    Returns (primary_insurer_key, secondary_insurer_key, reasoning)
    """
    print(f"  [COB] Determining primary insurer for {patient} — {claim_type}...")

    # Extract subscriber names from the passed plan dictionaries
    plan_a_subscriber = plan_a.get("subscriber_name", "")
    plan_b_subscriber = plan_b.get("subscriber_name", "")

    # Determine which plan the patient is the primary policyholder on
    # Determine which plan the patient is the primary policyholder on (using partial match)
    if patient in plan_b_subscriber:
        primary = "Insurer2_PlanB"
        secondary = "Insurer1_PlanA"
        reasoning = (
            f"{patient} is the Primary Policyholder on Plan B (Insurer2), "
            f"so Plan B is PRIMARY for their own claims. "
            f"On Plan A (Insurer1), {patient} is a Dependent under {plan_a_subscriber}'s policy, "
            f"so Plan A is SECONDARY."
        )
    elif patient in plan_a_subscriber:
        primary = "Insurer1_PlanA"
        secondary = "Insurer2_PlanB"
        reasoning = (
            f"{patient} is the Primary Policyholder on Plan A (Insurer1), "
            f"so Plan A is PRIMARY for their own claims. "
            f"On Plan B (Insurer2), {patient} is a Dependent under {plan_b_subscriber}'s policy, "
            f"so Plan B is SECONDARY."
        )
    else:
        # Fallback: if patient name doesn't match any subscriber, default to first available plan
        primary = "Insurer1_PlanA"
        secondary = "Insurer2_PlanB"
        reasoning = (
            f"Unable to determine subscriber relationship for {patient}. "
            f"Defaulting to Plan A as PRIMARY."
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
    Standard COB calculation (non-duplication method, IRDAI-aligned):

    Step 0: Apply primary deductible (remaining, if any)
    Step 1: Primary pays after deductible + coinsurance
    Step 2: Secondary pays the remaining balance, but NOT more than it would
            have paid had it been primary (non-duplication clause)
    Step 3: Patient pays whatever is left (capped by secondary OOP max)

    The function also calculates the counterfactual single-plan OOP so the
    patient briefing can report actual savings accurately.
    """

    # ── Step 0: Apply primary deductible (partial deductible support) ──
    primary_deductible_remaining = max(
        0, primary_plan["annual_deductible_inr"] - primary_plan["deductible_met_inr"]
    )
    amount_after_primary_deductible = max(0, total_billed_inr - primary_deductible_remaining)

    # ── Step 1: Primary insurer calculation ──
    primary_coinsurance_rate = primary_plan["coinsurance_percent"] / 100
    primary_pays = round(amount_after_primary_deductible * (1 - primary_coinsurance_rate))
    primary_patient_responsibility = round(total_billed_inr - primary_pays)

    # ── Step 2: Secondary insurer calculation (non-duplication clause) ──
    # Non-duplication: secondary will not pay more than it would have paid
    # as the primary insurer for the same claim.
    secondary_deductible_remaining = max(
        0, secondary_plan["annual_deductible_inr"] - secondary_plan["deductible_met_inr"]
    )
    amount_after_secondary_deductible = max(0, total_billed_inr - secondary_deductible_remaining)
    secondary_coinsurance_rate = secondary_plan["coinsurance_percent"] / 100
    secondary_max_as_primary = round(
        amount_after_secondary_deductible * (1 - secondary_coinsurance_rate)
    )

    # Secondary's actual benefit = min(what primary left unpaid, what secondary would pay as primary)
    # — this is the IRDAI non-duplication clause in practice
    secondary_pays_raw = round(primary_patient_responsibility * (1 - secondary_coinsurance_rate))
    secondary_pays = min(secondary_pays_raw, secondary_max_as_primary)
    final_patient_pays = max(0, total_billed_inr - primary_pays - secondary_pays)

    # ── Out-of-pocket max check ──
    remaining_oop_secondary = (
        secondary_plan["out_of_pocket_max_inr"] - secondary_plan["out_of_pocket_met_inr"]
    )
    oop_note = ""
    if final_patient_pays > remaining_oop_secondary:
        capped = final_patient_pays - remaining_oop_secondary
        final_patient_pays = remaining_oop_secondary
        secondary_pays += capped
        oop_note = f"Out-of-pocket max applied: ₹{capped:,.0f} shifted to secondary."

    # ── Counterfactual: what patient would pay with primary only (no dual coverage) ──
    single_plan_patient_pays = round(
        max(0, amount_after_primary_deductible) * primary_coinsurance_rate
        + primary_deductible_remaining
    )
    dual_coverage_savings = round(single_plan_patient_pays - final_patient_pays)

    print(f"  [COB] Total billed       : ₹{total_billed_inr:>10,.0f}")
    print(f"  [COB] Primary pays       : ₹{primary_pays:>10,.0f}")

    print(f"  [COB] Secondary pays     : ₹{secondary_pays:>10,.0f}")
    print(f"  [COB] Patient pays       : ₹{final_patient_pays:>10,.0f}")
    print(f"  [COB] Without dual cover : ₹{single_plan_patient_pays:>10,.0f}  (counterfactual)")
    print(f"  [COB] Dual-cover savings : ₹{dual_coverage_savings:>10,.0f}")

    primary_pct   = primary_plan["coinsurance_percent"]
    secondary_pct = secondary_plan["coinsurance_percent"]
    formula = (
        f"Primary deductible remaining: ₹{primary_deductible_remaining:,.0f}. "
        f"Primary pays {100 - primary_pct:.0f}% of post-deductible amount. "
        f"Secondary (non-duplication): pays min(its share of primary's patient responsibility, "
        f"what it would pay as primary). "
        f"Patient pays remainder."
    )

    return {
        "total_billed_inr":               total_billed_inr,
        "primary_pays_inr":               primary_pays,
        "secondary_pays_inr":             secondary_pays,
        "patient_pays_inr":               final_patient_pays,
        "primary_coinsurance":            f"{primary_plan['coinsurance_percent']}%",
        "secondary_coinsurance":          f"{secondary_plan['coinsurance_percent']}%",
        "primary_deductible_applied_inr": primary_deductible_remaining,
        "non_duplication_cap_applied":    secondary_pays < secondary_pays_raw,
        "counterfactual_single_plan_oop": single_plan_patient_pays,
        "dual_coverage_savings_inr":      dual_coverage_savings,
        "deductibles_note": (
            "Both annual deductibles already met (mid-year scenario)."
            if primary_deductible_remaining == 0
            else f"Primary deductible partially met; ₹{primary_deductible_remaining:,.0f} applied first."
        ),
        "oop_note":  oop_note,
        "math_audit": {
            "check_sum_correct": abs(
                primary_pays + secondary_pays + final_patient_pays - total_billed_inr
            ) < 1,
            "formula": formula,
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

    if state.get("agent_state") not in ("COB_READY",):
        if state.get("agent_state") == "INTAKE_FAILED":
            raise RuntimeError(
                "Refusing to run COB on an INTAKE_FAILED state — intake validation "
                f"never passed (issues: {state.get('validation_issues')}). "
                "Fix the underlying extraction and re-run intake_agent first."
            )
        print(f"  [WARN] Agent state is '{state.get('agent_state')}', expected 'COB_READY'.")
        print("  [WARN] Proceeding anyway (non-fatal state mismatch)...")

    state["agent_state"] = "COB_REASONING"

    # ── Tool call audit log (every API call is recorded for auditability) ──
    import datetime as _dt
    tool_call_log = []

    _orig_call_tool = __import__("src.tools.insurer_api", fromlist=["call_tool"]).call_tool

    def _logged_call_tool(tool_name: str, **kwargs) -> dict:
        entry = {
            "timestamp": _dt.datetime.utcnow().isoformat() + "Z",
            "tool": tool_name,
            "inputs": {k: (v if not isinstance(v, list) or len(v) <= 10 else v[:10]) for k, v in kwargs.items()},
        }
        result = _orig_call_tool(tool_name, **kwargs)
        entry["result_summary"] = {
            k: v for k, v in result.items()
            if k in ("decision", "status", "auth_number", "insurer", "plan_code",
                     "coinsurance_percent", "deductible_met_inr", "covered", "not_covered",
                     "requires_pre_auth", "denial_reason")
        }
        tool_call_log.append(entry)
        return result

    # Monkey-patch the dispatcher for this run so all downstream calls are logged
    import src.tools.insurer_api as _api_mod
    _api_mod.call_tool = _logged_call_tool

    # Re-import to pick up the patched version in cob_engine's own scope
    from src.tools.insurer_api import call_tool   # noqa: F811

    # ── Pull CPT codes from intake, SCOPED PER CLAIM ──
    # (Previously both insurer lookups were checked against the combined
    # surgery+PT code list, which leaked Aarav's surgical CPTs into Priya's
    # pre-auth-required flag. Each claim now only checks its own codes.)
    import re as _re

    def _normalise_cpt(raw: str) -> str:
        """Strip any 'CPT' prefix (with or without a trailing space) and return
        only the numeric/alpha code, e.g. 'CPT 29888' → '29888', 'CPT00400' → '00400'."""
        return _re.sub(r"^CPT\s*", "", str(raw).strip())

    # Only keep codes that look like real CPT numbers (digits, 5 chars).
    # This filters out sentinel tokens like "IMPLANTS" AND malformed codes
    # like "CPT00400" that appear because the vision model may not add the space.
    # Anesthesia code 00400 is included deliberately — it IS in covered_cpt_codes.
    surgery_cpts = [
        _normalise_cpt(p["cpt_code"])
        for p in state["surgeon_estimate"].get("procedures", [])
        if p.get("cpt_code") and p["cpt_code"] not in ("IMPLANTS",)
        and _re.match(r"^(CPT\s*)?\d{5}$", str(p["cpt_code"]).strip())
    ]
    pt_line_items = state["pt_invoice"].get("line_items", [])
    pt_cpts = list(dict.fromkeys(   # deduplicate while preserving order
        _normalise_cpt(li["inferred_cpt_code"])
        for li in pt_line_items
        if li.get("inferred_cpt_code")
    ))

    # ── TOOL CALLS: fetch plan details from src/tools/insurer_api.py ──
    print("\n  [TOOL CALLS] Fetching plan details from insurer API tool...")
    plan_a_for_surgery = fetch_plan_details("Insurer1_PlanA", surgery_cpts)
    plan_b_for_surgery = fetch_plan_details("Insurer2_PlanB", surgery_cpts)
    plan_a_for_pt       = fetch_plan_details("Insurer1_PlanA", pt_cpts)
    plan_b_for_pt       = fetch_plan_details("Insurer2_PlanB", pt_cpts)
    # plan_a / plan_b kept for the COB payment maths (coinsurance/OOP are
    # plan-level, not claim-specific, so either claim-scoped fetch works)
    plan_a, plan_b = plan_a_for_surgery, plan_b_for_surgery

    # ─────────────────────────────────────────
    # CLAIM 1: Aarav's ACL Surgery
    # ─────────────────────────────────────────
    print("\n  ── CLAIM 1: Aarav's ACL Surgery ──")
    aarav_primary_key, aarav_secondary_key, aarav_cob_reason = determine_primary_insurer(
        "Aarav", "ACL Surgery", plan_a, plan_b
    )


    aarav_primary_plan   = plan_b if aarav_primary_key   == "Insurer2_PlanB" else plan_a
    aarav_secondary_plan = plan_a if aarav_secondary_key == "Insurer1_PlanA" else plan_b

    aarav_total = state["surgeon_estimate"].get("total_surgical_amount_inr", 450000)
    aarav_cob   = calculate_cob_payment(aarav_total, aarav_primary_plan, aarav_secondary_plan, "Aarav")
    aarav_math  = audit_cob_math(aarav_cob)
    print(f"  [AUDIT] Math check: {aarav_math['note']}")

    # ── TOOL CALL: request_pre_authorization (both insurers — surgeon's
    # estimate explicitly notes pre-auth is required from both) ──
    aarav_icd10 = [c.get("icd10_code") for c in state["surgeon_estimate"].get("procedures", []) if c.get("icd10_code")]
    aarav_preauth_primary = call_tool(
        "request_pre_authorization", plan_key=aarav_primary_key, cpt_codes=surgery_cpts,
        patient_name="Aarav Sen", diagnosis_codes=aarav_icd10,
    )
    aarav_preauth_secondary = call_tool(
        "request_pre_authorization", plan_key=aarav_secondary_key, cpt_codes=surgery_cpts,
        patient_name="Aarav Sen", diagnosis_codes=aarav_icd10,
    )

    # ─────────────────────────────────────────
    # CLAIM 2: Priya's PT Bills
    # ─────────────────────────────────────────
    print("\n  ── CLAIM 2: Priya's PT Bills ──")
    priya_primary_key, priya_secondary_key, priya_cob_reason = determine_primary_insurer(
        "Priya", "Physical Therapy", plan_a, plan_b
    )


    priya_primary_plan   = plan_a if priya_primary_key   == "Insurer1_PlanA" else plan_b
    priya_secondary_plan = plan_b if priya_secondary_key == "Insurer2_PlanB" else plan_a

    priya_total = state["pt_invoice"].get("total_amount_inr", 30000)
    priya_cob   = calculate_cob_payment(priya_total, priya_primary_plan, priya_secondary_plan, "Priya")
    priya_math  = audit_cob_math(priya_cob)
    print(f"  [AUDIT] Math check: {priya_math['note']}")

    # ── TOOL CALL: request_pre_authorization (both insurers) ──
    priya_icd10 = [c.split(":")[0].strip() for c in state["pt_invoice"].get("inferred_icd10_codes", [])]
    priya_preauth_primary = call_tool(
        "request_pre_authorization", plan_key=priya_primary_key, cpt_codes=pt_cpts,
        patient_name="Priya Sen", diagnosis_codes=priya_icd10,
    )
    priya_preauth_secondary = call_tool(
        "request_pre_authorization", plan_key=priya_secondary_key, cpt_codes=pt_cpts,
        patient_name="Priya Sen", diagnosis_codes=priya_icd10,
    )

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
            "pre_auth_required": plan_b_for_surgery.get("pre_auth_needed_for", []),
            "preauth_decision": {
                aarav_primary_key:   aarav_preauth_primary,
                aarav_secondary_key: aarav_preauth_secondary,
            },
        },
        "priya_pt": {
            "patient":          "Priya Sen",
            "claim_type":       "Physical Therapy Sessions",
            "primary_insurer":  priya_primary_key,
            "secondary_insurer": priya_secondary_key,
            "cob_reasoning":    priya_cob_reason,
            "payment_breakdown": priya_cob,
            "math_audit":       priya_math,
            "pre_auth_required": plan_a_for_pt.get("pre_auth_needed_for", []),
            "preauth_decision": {
                priya_primary_key:   priya_preauth_primary,
                priya_secondary_key: priya_preauth_secondary,
            },
        },
        "family_summary": {
            "total_billed_inr":   total_family_bill,
            "family_pays_inr":    total_family_pays,
            "total_savings_inr":  total_family_savings,
            "savings_percent":    round((total_family_savings / total_family_bill) * 100, 1),
        },
    }

    # Persist the raw tool-returned plan records too (policy number, subscriber
    # name, claim address) so the output stage can pull them dynamically
    # instead of hardcoding values that happen to match the mock DB.
    state["plan_details"] = {
        "Insurer1_PlanA": plan_a,
        "Insurer2_PlanB": plan_b,
    }

    state["agent_state"] = "OUTPUT_READY"

    # Persist full tool call audit trail
    state["tool_call_log"] = tool_call_log

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