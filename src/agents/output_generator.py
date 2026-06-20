"""
DuCO-Agent | Output Generator
State: OUTPUT_READY -> DONE
Produces:
  1. outputs/aarav_preauth_letter.pdf
  2. outputs/priya_preauth_letter.pdf
  3. outputs/cost_flow_chart.png
  4. outputs/patient_briefing.txt
"""

import json
import os
from pathlib import Path
from datetime import date
from fpdf import FPDF, XPos, YPos
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker

STATE_PATH = Path("data/state.json")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class LetterPDF(FPDF):
    def __init__(self, insurer_name):
        super().__init__()
        self.insurer_name = insurer_name
        self.set_margins(20, 48, 20)   # top=48 gives clear gap below the 26px header bar
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        self.set_fill_color(25, 55, 115)
        self.rect(0, 0, 210, 26, "F")  # taller bar so text sits comfortably inside it
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(255, 255, 255)
        self.set_xy(0, 7)
        self.cell(210, 12, "DuCO-Agent | Pre-Authorization Request",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_text_color(0, 0, 0)
        self.set_y(36)  # force cursor well below the blue bar

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 8,
                  f"Confidential | {self.insurer_name} | Page {self.page_no()} | "
                  f"DuCO-Agent {date.today().strftime('%d %b %Y')}",
                  align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(220, 228, 248)
        self.set_text_color(25, 55, 115)
        self.cell(0, 7, f"  {title}",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def kv(self, key, value):
        self.set_font("Helvetica", "B", 9)
        self.cell(55, 6, key)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, str(value)[:80],
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def body(self, text):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5, text)
        self.ln(2)


def generate_aarav_preauth(state):
    print("  [OUTPUT] Generating Aarav pre-auth letter...")
    path = OUTPUT_DIR / "aarav_preauth_letter.pdf"
    mri  = state.get("mri_report", {})
    surg = state.get("surgeon_estimate", {})
    cob  = state.get("cob_results", {}).get("aarav_surgery", {})
    bd   = cob.get("payment_breakdown", {})
    today = date.today().strftime("%d %B %Y")

    pdf = LetterPDF("Insurer2 Plan B")
    pdf.add_page()

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Date: {today}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, f"Ref: PRE-AUTH/DUCO/{date.today().year}/ACL/001", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "To,", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    for line in ["The Pre-Authorization Dept.", "Insurer2 - Plan B (Corporate Health)", "Mumbai, Maharashtra"]:
        pdf.cell(0, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(255, 243, 205)
    pdf.cell(0, 7, "  Subject: Pre-Auth Request -- ACL Reconstruction + Meniscectomy",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.ln(3)

    pdf.section_title("1. PATIENT & POLICY DETAILS")
    for k, v in [
        ("Patient:", "Mr. Aarav Sen"),
        ("DOB:", "12-Mar-1990  (Age: 34)"),
        ("Policy No:", "PLB-2024-AS-00441"),
        ("Plan:", "Plan B -- Insurer2  (Primary Policyholder)"),
        ("Secondary:", "Plan A -- Insurer1  (Dependent under Priya Sen)"),
        ("Employer:", "TechCorp India Pvt. Ltd., Mumbai"),
    ]:
        pdf.kv(k, v)
    pdf.ln(2)

    pdf.section_title("2. CLINICAL JUSTIFICATION")
    diag = mri.get("primary_diagnosis", "Complete ACL tear, Right Knee")
    for k, v in [
        ("Primary Dx:", diag[:70]),
        ("ICD-10:", "S83.511A -- ACL tear, right knee"),
        ("Secondary Dx:", "Medial Meniscus Tear, Posterior Horn"),
        ("ICD-10:", "S83.211A -- Meniscus tear, right knee"),
        ("MRI Ref:", "RAD-2024-08821 | HealthScan Diagnostics | 12-May-2024"),
    ]:
        pdf.kv(k, v)
    pdf.ln(2)
    pdf.body(
        "MRI confirms complete mid-substance ACL tear with pivot-shift bone contusions and "
        "Grade III posterior horn medial meniscus tear. Surgical intervention is medically "
        "necessary to restore knee stability and prevent further cartilage damage."
    )

    pdf.section_title("3. PROPOSED PROCEDURES")
    procedures = surg.get("procedures") or [
        {"cpt_code": "CPT 29888", "description": "ACL Reconstruction (Arthroscopic)", "amount_inr": 350000},
        {"cpt_code": "CPT 29881", "description": "Knee Arthroscopy with Meniscectomy",  "amount_inr": 100000},
    ]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(200, 212, 240)
    pdf.cell(32, 6, "CPT Code", fill=True, border=1)
    pdf.cell(100, 6, "Description", fill=True, border=1)
    pdf.cell(0, 6, "Amount (Rs.)", fill=True, border=1,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    import re as _re
    pdf.set_font("Helvetica", "", 9)
    for p in procedures:
        raw_amt = p.get("amount_inr", 0)
        cleaned = _re.sub(r"[^\d.]", "", str(raw_amt))
        amt_str = f"{float(cleaned):,.0f}" if cleaned else "Included"
        cpt     = str(p.get("cpt_code", ""))[:12]
        desc    = str(p.get("description", ""))[:55]
        pdf.cell(32, 6, cpt, border=1)
        pdf.cell(100, 6, desc, border=1)
        pdf.cell(0, 6, amt_str, border=1, align="R",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    raw_total = surg.get("total_surgical_amount_inr", 450000)
    total_surg = float(_re.sub(r"[^\d.]", "", str(raw_total))) if raw_total else 450000
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(132, 6, "TOTAL SURGICAL ESTIMATE", border=1, fill=True)
    pdf.cell(0, 6, f"{total_surg:,.0f}", border=1, fill=True, align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    pdf.section_title("4. TREATING PHYSICIAN & FACILITY")
    for k, v in [
        ("Surgeon:", "Dr. Kiran Rao, MS Ortho, Fellowship Sports Medicine"),
        ("Facility:", "Apollo Orthopaedic & Sports Medicine Centre, Navi Mumbai"),
        ("Proposed Date:", "Within 30 days of pre-auth approval"),
        ("Expected Stay:", "2 days"),
    ]:
        pdf.kv(k, v)
    pdf.ln(2)

    pdf.section_title("5. DUAL COVERAGE -- COB NOTICE")
    pdf.body(
        f"Plan B (Insurer2) is PRIMARY as Mr. Aarav Sen is the Primary Policyholder.\n"
        f"Plan A (Insurer1) is SECONDARY.\n\n"
        f"  Plan B (Primary) pays  : Rs. {bd.get('primary_pays_inr', 405000):,.0f}\n"
        f"  Plan A (Secondary) pays: Rs. {bd.get('secondary_pays_inr', 36000):,.0f}\n"
        f"  Patient out-of-pocket  : Rs. {bd.get('patient_pays_inr', 9000):,.0f}"
    )

    pdf.section_title("6. DECLARATION")
    pdf.body(
        "I confirm the above information is accurate and the procedure is medically necessary. "
        "Clinical documentation (MRI report, surgeon estimate) is attached. "
        "Kindly approve pre-authorization to avoid delay in surgical care."
    )
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 5, "Dr. Kiran Rao")
    pdf.cell(0, 5, "Mr. Aarav Sen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(80, 5, "Treating Surgeon")
    pdf.cell(0, 5, "Policyholder -- Plan B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(str(path))
    print(f"  [OUTPUT] Saved -> {path}")
    return path


def generate_priya_preauth(state):
    print("  [OUTPUT] Generating Priya pre-auth letter...")
    path = OUTPUT_DIR / "priya_preauth_letter.pdf"
    pt   = state.get("pt_invoice", {})
    cob  = state.get("cob_results", {}).get("priya_pt", {})
    bd   = cob.get("payment_breakdown", {})
    today = date.today().strftime("%d %B %Y")

    pdf = LetterPDF("Insurer1 Plan A")
    pdf.add_page()

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Date: {today}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, f"Ref: PRE-AUTH/DUCO/{date.today().year}/PT/002", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "To,", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    for line in ["The Claims & Pre-Auth Dept.", "Insurer1 - Plan A (Corporate Health)", "Mumbai, Maharashtra"]:
        pdf.cell(0, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(255, 243, 205)
    pdf.cell(0, 7, "  Subject: Claim Submission -- Physical Therapy (Chronic Back Pain)",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.ln(3)

    pdf.section_title("1. PATIENT & POLICY DETAILS")
    for k, v in [
        ("Patient:", "Mrs. Priya Sen"),
        ("DOB:", "05-Sep-1992  (Age: 31)"),
        ("Policy No:", "PLA-2024-PS-00219"),
        ("Plan:", "Plan A -- Insurer1  (Primary Policyholder)"),
        ("Secondary:", "Plan B -- Insurer2  (Dependent under Aarav Sen)"),
        ("Employer:", "FinServ Solutions Ltd., Mumbai"),
    ]:
        pdf.kv(k, v)
    pdf.ln(2)

    pdf.section_title("2. CLINICAL JUSTIFICATION")
    for k, v in [
        ("Diagnosis:", "Chronic Low Back Pain -- Lumbar Region"),
        ("ICD-10:", "M54.5 -- Low back pain"),
        ("Referring Dr:", "Dr. Sunita Mehta, MD (Physical Medicine)"),
        ("Clinic:", "CureMotion Physiotherapy, Andheri West, Mumbai"),
        ("Period:", "01 Apr 2024 -- 18 May 2024  (14 sessions)"),
    ]:
        pdf.kv(k, v)
    pdf.ln(2)
    pdf.body(
        "Mrs. Priya Sen presented with chronic lumbar back pain impacting occupational functioning. "
        "A structured physiotherapy course was prescribed covering functional evaluation, "
        "therapeutic exercise, manual therapy, and neuromuscular re-education -- all "
        "evidence-based per NICE and APTA guidelines for chronic low back pain."
    )

    pdf.section_title("3. SERVICES & CPT CODES (Agent-Inferred)")
    pdf.body("Note: Original invoice had no CPT codes. Codes below inferred by DuCO-Agent.")
    rows = [
        ("97161", "PT Evaluation -- High Complexity",         "1",  "2,000"),
        ("97110", "Therapeutic Exercise (x10 sessions)",      "10", "15,000"),
        ("97140", "Manual Therapy -- Spinal Mobilisation",    "2",  "4,000"),
        ("97112", "Neuromuscular Re-education",               "1",  "2,000"),
        ("97110", "Therapeutic Exercise + Dry Needling",      "1",  "2,500"),
    ]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(200, 212, 240)
    pdf.cell(28, 6, "CPT", fill=True, border=1)
    pdf.cell(100, 6, "Service", fill=True, border=1)
    pdf.cell(15, 6, "Units", fill=True, border=1)
    pdf.cell(0,  6, "Rs.", fill=True, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    for code, desc, units, amt in rows:
        pdf.cell(28, 6, code, border=1)
        pdf.cell(100, 6, desc[:50], border=1)
        pdf.cell(15, 6, units, border=1, align="C")
        pdf.cell(0, 6, amt, border=1, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(143, 6, "TOTAL (incl. GST 5%)", border=1, fill=True)
    pdf.cell(0, 6, "30,000", border=1, fill=True, align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    pdf.section_title("4. DUAL COVERAGE -- COB NOTICE")
    pdf.body(
        f"Plan A (Insurer1) is PRIMARY as Mrs. Priya Sen is the Primary Policyholder.\n"
        f"Plan B (Insurer2) is SECONDARY.\n\n"
        f"  Plan A (Primary) pays  : Rs. {bd.get('primary_pays_inr', 24000):,.0f}\n"
        f"  Plan B (Secondary) pays: Rs. {bd.get('secondary_pays_inr', 5400):,.0f}\n"
        f"  Patient out-of-pocket  : Rs. {bd.get('patient_pays_inr', 600):,.0f}"
    )

    pdf.section_title("5. ATTACHMENTS & DECLARATION")
    pdf.body(
        "Attached: Original invoice INV-2024-PT-0091 | Referral letter (Dr. Sunita Mehta) | "
        "Claim Form 1A.\n\n"
        "I confirm the treatment was medically necessary and all information is accurate. "
        "Please process under Plan A and coordinate with Insurer2 for secondary claim."
    )
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 5, "Dr. Sunita Mehta")
    pdf.cell(0, 5, "Mrs. Priya Sen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(80, 5, "Referring Physiatrist")
    pdf.cell(0, 5, "Policyholder -- Plan A", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(str(path))
    print(f"  [OUTPUT] Saved -> {path}")
    return path


def generate_cost_flow_chart(state):
    print("  [OUTPUT] Generating cost flow chart...")
    path = OUTPUT_DIR / "cost_flow_chart.png"
    cob  = state.get("cob_results", {})
    a    = cob.get("aarav_surgery", {}).get("payment_breakdown", {})
    p    = cob.get("priya_pt",      {}).get("payment_breakdown", {})
    fam  = cob.get("family_summary", {})

    a_vals = [a.get("total_billed_inr",450000), a.get("primary_pays_inr",405000),
              a.get("secondary_pays_inr",36000), a.get("patient_pays_inr",9000)]
    p_vals = [p.get("total_billed_inr",30000),  p.get("primary_pays_inr",24000),
              p.get("secondary_pays_inr",5400),  p.get("patient_pays_inr",600)]

    a_labs = ["Total\nBilled","Plan B\n(Primary)","Plan A\n(Secondary)","Aarav\nPays"]
    p_labs = ["Total\nBilled","Plan A\n(Primary)","Plan B\n(Secondary)","Priya\nPays"]
    cols   = ["#3A5FC8","#27AE60","#F39C12","#E74C3C"]

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.patch.set_facecolor("#F4F6FB")
    fig.suptitle("DuCO-Agent -- Coordination of Benefits: Cost Flow",
                 fontsize=15, fontweight="bold", color="#19376C", y=0.97)

    for ax, vals, labs, title, ymax in [
        (axes[0], a_vals, a_labs, "Aarav Sen -- ACL Surgery (Rs. 4,50,000)", 520000),
        (axes[1], p_vals, p_labs, "Priya Sen -- Physical Therapy (Rs. 30,000)", 36000),
    ]:
        ax.set_facecolor("#FAFBFD")
        bars = ax.bar(labs, vals, color=cols, width=0.5, edgecolor="white", linewidth=1.5, zorder=3)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + ymax*0.015,
                    f"Rs.{val:,.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
        total = vals[0]
        for bar, val in zip(bars[1:], vals[1:]):
            pct = round(val/total*100, 1)
            if bar.get_height() > ymax*0.04:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                        f"{pct}%", ha="center", va="center", fontsize=9,
                        color="white", fontweight="bold")
        ax.set_title(title, fontsize=11, fontweight="bold", color="#19376C", pad=10)
        ax.set_ylim(0, ymax*1.18)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"Rs.{x:,.0f}"))
        ax.set_ylabel("Amount (INR)", fontsize=9, color="#555")
        ax.tick_params(axis="x", labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)

    legend_items = [
        mpatches.Patch(color="#3A5FC8", label="Total Billed"),
        mpatches.Patch(color="#27AE60", label="Primary Insurer Pays"),
        mpatches.Patch(color="#F39C12", label="Secondary Insurer Pays"),
        mpatches.Patch(color="#E74C3C", label="Patient Out-of-Pocket"),
    ]
    fig.legend(handles=legend_items, loc="lower center", ncol=4,
               fontsize=9, frameon=True, bbox_to_anchor=(0.5, 0.01))

    summary = (
        f"Family Total Billed: Rs.{fam.get('total_billed_inr',480000):,.0f}  |  "
        f"Family Pays: Rs.{fam.get('family_pays_inr',9600):,.0f}  |  "
        f"Savings via Dual Coverage: Rs.{fam.get('total_savings_inr',470400):,.0f} "
        f"({fam.get('savings_percent',98.0)}%)"
    )
    fig.text(0.5, 0.07, summary, ha="center", fontsize=9, color="#19376C", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#E8EDF8", edgecolor="#19376C", alpha=0.8))

    plt.tight_layout(rect=[0, 0.12, 1, 0.94])
    plt.savefig(str(path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  [OUTPUT] Saved -> {path}")
    return path


def generate_patient_briefing(state):
    print("  [OUTPUT] Generating patient briefing...")
    path = OUTPUT_DIR / "patient_briefing.txt"
    cob  = state.get("cob_results", {})
    a    = cob.get("aarav_surgery", {}).get("payment_breakdown", {})
    p    = cob.get("priya_pt",      {}).get("payment_breakdown", {})
    fam  = cob.get("family_summary", {})

    # Dynamic counterfactual savings (from COB engine, not hardcoded)
    aarav_single_plan_oop = a.get(
        "counterfactual_single_plan_oop",
        round(a.get("total_billed_inr", 450000) * 0.10)  # fallback: primary coinsurance only
    )
    priya_single_plan_oop = p.get(
        "counterfactual_single_plan_oop",
        round(p.get("total_billed_inr", 30000) * 0.20)
    )
    aarav_savings = a.get("dual_coverage_savings_inr", aarav_single_plan_oop - a.get("patient_pays_inr", 9000))
    priya_savings = p.get("dual_coverage_savings_inr", priya_single_plan_oop - p.get("patient_pays_inr", 600))

    # Dynamic coinsurance label from actual plan data
    a_primary_pct  = a.get("primary_coinsurance",   "10%").replace(".0%", "%")
    a_secondary_pct = a.get("secondary_coinsurance", "20%").replace(".0%", "%")
    p_primary_pct  = p.get("primary_coinsurance",   "20%").replace(".0%", "%")
    p_secondary_pct = p.get("secondary_coinsurance", "10%").replace(".0%", "%")

    # Aarav primary pays rate = 100% - coinsurance%
    a_primary_pays_pct = 100 - int(a_primary_pct.replace("%","").replace(".0",""))
    p_primary_pays_pct = 100 - int(p_primary_pct.replace("%","").replace(".0",""))

    text = f"""
DuCO-AGENT -- YOUR INSURANCE SUMMARY
Plain Language Briefing for Aarav & Priya Sen
Generated: {date.today().strftime('%d %B %Y')}
==========================================================

Hi Aarav and Priya,

Here is a simple breakdown of what your dual insurance means
for your current medical bills. No jargon, just the numbers.

----------------------------------------------------------
AARAV'S KNEE SURGERY (ACL + Meniscectomy)
----------------------------------------------------------
Total surgeon bill          : Rs. {a.get('total_billed_inr', 450000):,.0f}

Your own policy (Plan B / Insurer2) pays FIRST:
  Plan B pays               : Rs. {a.get('primary_pays_inr', 405000):,.0f}  ({a_primary_pays_pct}%)
  Plan A picks up the rest  : Rs. {a.get('secondary_pays_inr', 36000):,.0f}

AARAV, YOU PAY              : Rs. {a.get('patient_pays_inr', 9000):,.0f}  ONLY!

Without dual cover you would have paid ~Rs. {aarav_single_plan_oop:,.0f}.
With both plans: just Rs. {a.get('patient_pays_inr', 9000):,.0f}.
Dual coverage saves you    : Rs. {aarav_savings:,.0f} on this claim!

ACTION REQUIRED:
  Submit aarav_preauth_letter.pdf to Insurer2 (Plan B) NOW.
  Get approval BEFORE surgery. No approval = risk of rejection.

----------------------------------------------------------
PRIYA'S PHYSIOTHERAPY BILL
----------------------------------------------------------
Total clinic bill           : Rs. {p.get('total_billed_inr', 30000):,.0f}

Your own policy (Plan A / Insurer1) pays FIRST:
  Plan A pays               : Rs. {p.get('primary_pays_inr', 24000):,.0f}  ({p_primary_pays_pct}%)
  Plan B picks up the rest  : Rs. {p.get('secondary_pays_inr', 5400):,.0f}

PRIYA, YOU PAY              : Rs. {p.get('patient_pays_inr', 600):,.0f}  ONLY!

Without dual cover you would have paid ~Rs. {priya_single_plan_oop:,.0f}.
With both plans: just Rs. {p.get('patient_pays_inr', 600):,.0f}.
Dual coverage saves you    : Rs. {priya_savings:,.0f} on this claim!

ACTION REQUIRED:
  Submit priya_preauth_letter.pdf + original invoice to Insurer1 (Plan A).

----------------------------------------------------------
FAMILY TOTAL
----------------------------------------------------------
Total medical bills         : Rs. {fam.get('total_billed_inr', 480000):,.0f}
Your family actually pays   : Rs. {fam.get('family_pays_inr', 9600):,.0f}
Money SAVED via dual cover  : Rs. {fam.get('total_savings_inr', 470400):,.0f}
                              ({fam.get('savings_percent', 98.0)}% savings!)

----------------------------------------------------------
NEXT STEPS (in order)
----------------------------------------------------------
1. Submit aarav_preauth_letter.pdf to Insurer2 (Plan B) immediately.
2. Wait for approval (3-5 working days).
3. Schedule Aarav's surgery ONLY after approval is received.
4. Submit priya_preauth_letter.pdf + original invoice to Insurer1 (Plan A).
5. After Plan A settles, submit remaining balance claim to Insurer2.

----------------------------------------------------------
Generated by DuCO-Agent | {date.today().strftime('%d %B %Y')}
Re-run anytime: python src/agents/intake_agent.py
----------------------------------------------------------
"""
    path.write_text(text.strip(), encoding="utf-8")
    print(f"  [OUTPUT] Saved -> {path}")
    return path


def run_output_generator():
    print("\n" + "="*50)
    print("DuCO-Agent | OUTPUT STATE")
    print("="*50)

    if not STATE_PATH.exists():
        raise FileNotFoundError("data/state.json not found. Run cob_engine.py first.")

    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)

    state["agent_state"] = "GENERATING_OUTPUTS"

    letter_a = generate_aarav_preauth(state)
    letter_p = generate_priya_preauth(state)
    chart    = generate_cost_flow_chart(state)
    briefing = generate_patient_briefing(state)

    state["agent_state"] = "DONE"
    state["outputs"] = {
        "aarav_preauth_letter": str(letter_a),
        "priya_preauth_letter": str(letter_p),
        "cost_flow_chart":      str(chart),
        "patient_briefing":     str(briefing),
    }

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(f"\n  [STATE] Agent state -> {state['agent_state']}")
    print("="*50)
    print("\n  ALL OUTPUTS GENERATED:")
    for k, v in state["outputs"].items():
        print(f"    {k:30s} -> {v}")
    print()


if __name__ == "__main__":
    run_output_generator()