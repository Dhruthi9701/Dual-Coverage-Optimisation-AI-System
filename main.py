"""
DuCO-Agent | Main Entry Point
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Usage:
    python main.py                  # run full pipeline
    python main.py --step intake    # run only intake agent
    python main.py --step cob       # run only COB engine
    python main.py --step output    # run only output generator

Agent State Machine:
    INTAKE -> REFLECTING -> COB_READY
           -> COB_REASONING -> OUTPUT_READY
           -> GENERATING_OUTPUTS -> DONE
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    print("""
+======================================================+
|                                                      |
|           DuCO-Agent  v1.0                           |
|   Dual Coverage Optimisation Agentic AI System       |
|                                                      |
|   Patients : Aarav Sen & Priya Sen, Mumbai           |
|   Plans    : Insurer1 Plan A  +  Insurer2 Plan B     |
|                                                      |
+======================================================+
""")


def check_env():
    import os
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("  [ERROR] GEMINI_API_KEY environment variable is not set.")
        print("  Set it with:  set GEMINI_API_KEY=your-key-here")
        sys.exit(1)
    print(f"  [ENV] GEMINI_API_KEY detected ({key[:8]}...)")


def check_inputs():
    required = [
        Path("data/mock_inputs/user_query.txt"),
        Path("data/mock_inputs/aarav_mri_report.pdf"),
        Path("data/mock_inputs/priya_pt_invoice.png"),
        Path("data/mock_inputs/surgeon_estimate.jpg"),
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("  [ERROR] Missing input files:")
        for m in missing:
            print(f"    - {m}")
        print("\n  Run:  python scripts/generate_mock_inputs.py")
        sys.exit(1)
    print(f"  [ENV] All {len(required)} mock input files found.")


def run_step_intake():
    print("\n" + "-"*54)
    print("  STEP 1 of 3 -- INTAKE AGENT")
    print("-"*54)
    from src.agents.intake_agent import run_intake_agent
    return run_intake_agent()


def run_step_cob():
    print("\n" + "-"*54)
    print("  STEP 2 of 3 -- COB ENGINE")
    print("-"*54)
    from src.engine.cob_engine import run_cob_engine
    return run_cob_engine()


def run_step_output():
    print("\n" + "-"*54)
    print("  STEP 3 of 3 -- OUTPUT GENERATOR")
    print("-"*54)
    from src.agents.output_generator import run_output_generator
    run_output_generator()


def print_final_summary():
    import json
    state_path = Path("data/state.json")
    if not state_path.exists():
        return
    with open(state_path) as f:
        state = json.load(f)

    cob  = state.get("cob_results", {})
    a    = cob.get("aarav_surgery", {}).get("payment_breakdown", {})
    p    = cob.get("priya_pt",      {}).get("payment_breakdown", {})
    fam  = cob.get("family_summary", {})
    outs = state.get("outputs", {})

    print("\n" + "="*54)
    print("  ALL OUTPUTS GENERATED:")
    for k, v in outs.items():
        print(f"    {k:30s} -> {v}")
    
    print("+======================================================+")
    print("|              DUCO-AGENT PIPELINE COMPLETE            |")
    print("+======================================================+")
    print(f"|  Aarav Surgery  -> Insurer2 pays: Rs. {a.get('primary_pays_inr', 0):>8,.0f}       |")
    print(f"|                    Insurer1 pays: Rs. {a.get('secondary_pays_inr', 0):>8,.0f}       |")
    print(f"|                    Aarav pays  : Rs. {a.get('patient_pays_inr', 0):>8,.0f}       |")
    print("|------------------------------------------------------|")
    print(f"|  Priya PT Bills -> Insurer1 pays: Rs. {p.get('primary_pays_inr', 0):>8,.0f}       |")
    print(f"|                    Insurer2 pays: Rs. {p.get('secondary_pays_inr', 0):>8,.0f}       |")
    print(f"|                    Priya pays  : Rs. {p.get('patient_pays_inr', 0):>8,.0f}       |")
    print("|------------------------------------------------------|")
    print(f"|  Family SAVES   : Rs. {fam.get('total_savings_inr', 0):>8,.0f} ({fam.get('savings_percent', 0):.1f}%)       |")
    print("|------------------------------------------------------|")
    print("|  Outputs in outputs/ folder:                         |")
    print("|    aarav_preauth_letter.pdf                          |")
    print("|    priya_preauth_letter.pdf                          |")
    print("|    cost_flow_chart.png                               |")
    print("|    patient_briefing.txt                              |")
    print("|    patient_briefing.mp3                              |")
    print("+======================================================+")


def main():
    print_banner()
    parser = argparse.ArgumentParser(description="DuCO-Agent pipeline runner")
    parser.add_argument("--step", choices=["intake","cob","output"], default=None,
                        help="Run one step only (default: full pipeline)")
    args = parser.parse_args()

    t0 = time.time()
    print("\n  [PRE-FLIGHT CHECKS]")
    check_env()
    check_inputs()

    if args.step == "intake":
        run_step_intake()
    elif args.step == "cob":
        run_step_cob()
    elif args.step == "output":
        run_step_output()
    else:
        run_step_intake()
        run_step_cob()
        run_step_output()
        print_final_summary()

    print(f"\n  Total runtime: {round(time.time()-t0,1)}s\n")


if __name__ == "__main__":
    main()