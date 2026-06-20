"""
DuCO-Agent | Mock Insurer API Tool
src/tools/insurer_api.py

Simulates HTTP calls to two insurance company APIs.
In production these would be real REST endpoints.
Each call returns plan details: deductible status,
coinsurance rates, covered CPT codes, and pre-auth rules.

Tool interface follows a standard schema so the COB engine
can call either insurer with identical syntax.
"""

import json
import time
from dataclasses import dataclass, asdict
from typing import Optional


# ─────────────────────────────────────────────────────────────
# RESPONSE SCHEMA
# ─────────────────────────────────────────────────────────────

@dataclass
class PlanDetails:
    insurer:                  str
    plan_code:                str
    subscriber_name:          str
    policy_number:            str
    annual_deductible_inr:    float
    deductible_met_inr:       float
    deductible_remaining_inr: float
    coinsurance_percent:      float   # patient's share after deductible
    out_of_pocket_max_inr:    float
    out_of_pocket_met_inr:    float
    covered_cpt_codes:        list
    pre_auth_required_cpts:   list
    network_status:           str     # "in-network" | "out-of-network"
    claim_submission_address: str
    api_response_time_ms:     int
    status:                   str     # "active" | "lapsed" | "suspended"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PreAuthDecision:
    insurer:          str
    plan_code:        str
    cpt_codes:        list
    decision:         str    # "approved" | "pending" | "denied"
    auth_number:      Optional[str]
    validity_days:    int
    conditions:       list
    denial_reason:    Optional[str]
    response_time_ms: int

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────
# MOCK PLAN DATABASE
# ─────────────────────────────────────────────────────────────

_PLAN_DB = {
    "Insurer1_PlanA": {
        "insurer":                  "Insurer1",
        "plan_code":                "CORP-HEALTH-A-2024",
        "subscriber_name":          "Priya Sen",
        "policy_number":            "PLA-2024-PS-00219",
        "annual_deductible_inr":    10000.0,
        "deductible_met_inr":       10000.0,   # fully met (mid-year)
        "coinsurance_percent":      20.0,       # patient pays 20% after deductible
        "out_of_pocket_max_inr":    100000.0,
        "out_of_pocket_met_inr":    10000.0,
        "covered_cpt_codes":        [
            "29888", "29881", "00400",
            "97161", "97110", "97140", "97112", "97530",
        ],
        "pre_auth_required_cpts":   ["29888", "29881"],
        "network_status":           "in-network",
        "claim_submission_address": "Insurer1 Claims Dept, BKC, Mumbai 400051",
        "status":                   "active",
    },
    "Insurer2_PlanB": {
        "insurer":                  "Insurer2",
        "plan_code":                "CORP-HEALTH-B-2024",
        "subscriber_name":          "Aarav Sen",
        "policy_number":            "PLB-2024-AS-00441",
        "annual_deductible_inr":    15000.0,
        "deductible_met_inr":       15000.0,   # fully met (mid-year)
        "coinsurance_percent":      10.0,       # patient pays 10% after deductible
        "out_of_pocket_max_inr":    75000.0,
        "out_of_pocket_met_inr":    15000.0,
        "covered_cpt_codes":        [
            "29888", "29881", "00400",
            "97161", "97110", "97140", "97112", "97530",
        ],
        "pre_auth_required_cpts":   ["29888", "29881"],
        "network_status":           "in-network",
        "claim_submission_address": "Insurer2 Claims Dept, Nariman Point, Mumbai 400021",
        "status":                   "active",
    },
}

_PRE_AUTH_RULES = {
    "29888": {
        "decision":      "approved",
        "validity_days": 90,
        "conditions":    [
            "MRI confirmation of complete ACL tear required",
            "Surgery must be performed at empanelled hospital",
            "Post-operative physiotherapy plan must be submitted within 7 days",
        ],
    },
    "29881": {
        "decision":      "approved",
        "validity_days": 90,
        "conditions":    [
            "Must be performed concurrently with ACL reconstruction",
            "Arthroscopic approach only",
        ],
    },
}


# ─────────────────────────────────────────────────────────────
# API FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_plan_details(plan_key: str) -> PlanDetails:
    """
    Tool: fetch_plan_details
    Simulates GET /api/v1/plans/{plan_key}
    Returns full plan configuration for COB calculation.
    Raises ValueError if plan not found (simulates 404).
    """
    start = time.time()

    if plan_key not in _PLAN_DB:
        raise ValueError(
            f"[Insurer API] Plan '{plan_key}' not found. "
            f"Available: {list(_PLAN_DB.keys())}"
        )

    raw = _PLAN_DB[plan_key].copy()
    elapsed_ms = int((time.time() - start) * 1000) + 12  # simulate ~12ms network

    return PlanDetails(
        **raw,
        deductible_remaining_inr=max(
            0, raw["annual_deductible_inr"] - raw["deductible_met_inr"]
        ),
        api_response_time_ms=elapsed_ms,
    )


def request_pre_authorization(
    plan_key: str,
    cpt_codes: list[str],
    patient_name: str,
    diagnosis_codes: list[str],
) -> PreAuthDecision:
    """
    Tool: request_pre_authorization
    Simulates POST /api/v1/preauth
    Submits a pre-authorization request and returns a decision.
    In production this triggers an async review workflow.
    """
    start = time.time()
    plan = _PLAN_DB.get(plan_key, {})
    insurer = plan.get("insurer", plan_key)

    required_cpts = plan.get("pre_auth_required_cpts", [])
    auth_needed = [c for c in cpt_codes if c in required_cpts]

    if not auth_needed:
        # No pre-auth needed for these codes
        return PreAuthDecision(
            insurer=insurer,
            plan_code=plan_key,
            cpt_codes=cpt_codes,
            decision="not_required",
            auth_number=None,
            validity_days=0,
            conditions=[],
            denial_reason=None,
            response_time_ms=int((time.time() - start) * 1000) + 8,
        )

    # Check coverage
    covered = plan.get("covered_cpt_codes", [])
    uncovered = [c for c in cpt_codes if c not in covered]
    if uncovered:
        return PreAuthDecision(
            insurer=insurer,
            plan_code=plan_key,
            cpt_codes=cpt_codes,
            decision="denied",
            auth_number=None,
            validity_days=0,
            conditions=[],
            denial_reason=f"CPT codes {uncovered} not covered under {plan_key}",
            response_time_ms=int((time.time() - start) * 1000) + 8,
        )

    # Build combined conditions from all requested CPTs
    all_conditions = []
    for cpt in auth_needed:
        rule = _PRE_AUTH_RULES.get(cpt, {})
        all_conditions.extend(rule.get("conditions", []))

    # Generate auth number
    import hashlib
    auth_hash = hashlib.md5(
        f"{plan_key}{patient_name}{''.join(cpt_codes)}".encode()
    ).hexdigest()[:8].upper()
    auth_number = f"AUTH-{insurer[:3].upper()}-2024-{auth_hash}"

    return PreAuthDecision(
        insurer=insurer,
        plan_code=plan_key,
        cpt_codes=cpt_codes,
        decision="approved",
        auth_number=auth_number,
        validity_days=90,
        conditions=list(set(all_conditions)),
        denial_reason=None,
        response_time_ms=int((time.time() - start) * 1000) + 8,
    )


def verify_coverage(plan_key: str, cpt_codes: list[str]) -> dict:
    """
    Tool: verify_coverage
    Simulates GET /api/v1/coverage/verify
    Checks which CPT codes are covered and which need pre-auth.
    """
    plan = _PLAN_DB.get(plan_key, {})
    covered = plan.get("covered_cpt_codes", [])
    pre_auth = plan.get("pre_auth_required_cpts", [])

    return {
        "plan_key":           plan_key,
        "checked_cpts":       cpt_codes,
        "covered":            [c for c in cpt_codes if c in covered],
        "not_covered":        [c for c in cpt_codes if c not in covered],
        "requires_pre_auth":  [c for c in cpt_codes if c in pre_auth],
        "network_status":     plan.get("network_status", "unknown"),
    }


# ─────────────────────────────────────────────────────────────
# TOOL REGISTRY (used by COB engine for tool-use logging)
# ─────────────────────────────────────────────────────────────

AVAILABLE_TOOLS = {
    "get_plan_details":          get_plan_details,
    "request_pre_authorization": request_pre_authorization,
    "verify_coverage":           verify_coverage,
}


def call_tool(tool_name: str, **kwargs) -> dict:
    """
    Unified tool dispatcher.
    All agent tool calls go through here so they can be
    logged, retried, and audited in state.json.
    """
    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"Unknown tool: '{tool_name}'. Available: {list(AVAILABLE_TOOLS)}")

    print(f"  [TOOL CALL] {tool_name}({', '.join(f'{k}={v!r}' for k, v in kwargs.items())})")
    result = AVAILABLE_TOOLS[tool_name](**kwargs)

    if hasattr(result, "to_dict"):
        return result.to_dict()
    return result
