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
import pyttsx3

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
    # Extract patient details dynamically from state
    mri_patient = mri.get("patient_name")
    mri_age = mri.get("patient_age")
    if not mri_patient or not mri_age:
        raise ValueError("Missing required patient details from MRI report")

    primary_plan = state.get("plan_details", {}).get(cob.get("primary_insurer", "Insurer2_PlanB"), {})
    secondary_plan = state.get("plan_details", {}).get(cob.get("secondary_insurer", "Insurer1_PlanA"), {})
    primary_policy_no = primary_plan.get("policy_number", "PLB-2024-AS-00441")
    secondary_subscriber = secondary_plan.get("subscriber_name", "Priya Sen")
    
    for k, v in [
        ("Patient:", f"Mr. {mri_patient}"),
        ("DOB:", f"12-Mar-1990  (Age: {mri_age})"),
        ("Policy No:", primary_policy_no),
        ("Plan:", "Plan B -- Insurer2  (Primary Policyholder)"),
        ("Secondary:", f"Plan A -- Insurer1  (Dependent under {secondary_subscriber})"),
        ("Employer:", "TechCorp India Pvt. Ltd., Mumbai"),
    ]:
        pdf.kv(k, v)

    pdf.ln(2)

    pdf.section_title("2. CLINICAL JUSTIFICATION")
    diag = mri.get("primary_diagnosis")
    if not diag:
        raise ValueError("Missing primary diagnosis from MRI report")
    # Extract ICD codes dynamically from surgeon estimate procedures
    procedures = surg.get("procedures", [])
    icd_codes = [p.get("icd10_code") for p in procedures if p.get("icd10_code")]
    primary_icd = icd_codes[0] if len(icd_codes) > 0 else "S83.511A"
    secondary_icd = icd_codes[1] if len(icd_codes) > 1 else "S83.211A"
    mri_date = mri.get("study_date")
    if not mri_date:
        raise ValueError("Missing study date from MRI report")
    
    for k, v in [
        ("Primary Dx:", diag[:70]),
        ("ICD-10:", f"{primary_icd} -- ACL tear, right knee"),
        ("Secondary Dx:", "Medial Meniscus Tear, Posterior Horn"),
        ("ICD-10:", f"{secondary_icd} -- Meniscus tear, right knee"),
        ("MRI Ref:", f"RAD-2024-08821 | HealthScan Diagnostics | {mri_date}"),
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
    surgeon_name = surg.get("surgeon_name")
    hospital_name = surg.get("hospital_name")
    if not surgeon_name or not hospital_name:
        raise ValueError("Missing surgeon/hospital details from surgeon estimate")

    
    for k, v in [
        ("Surgeon:", f"{surgeon_name}, MS Ortho, Fellowship Sports Medicine"),
        ("Facility:", f"{hospital_name}, Navi Mumbai"),
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
    # Extract patient details dynamically from state
    pt_patient = pt.get("patient_name")
    if not pt_patient:
        raise ValueError("Missing required patient name from PT invoice")

    primary_plan = state.get("plan_details", {}).get(cob.get("primary_insurer", "Insurer1_PlanA"), {})
    secondary_plan = state.get("plan_details", {}).get(cob.get("secondary_insurer", "Insurer2_PlanB"), {})
    primary_policy_no = primary_plan.get("policy_number", "PLA-2024-PS-00219")
    secondary_subscriber = secondary_plan.get("subscriber_name", "Aarav Sen")
    
    for k, v in [
        ("Patient:", f"Mrs. {pt_patient}"),
        ("DOB:", "05-Sep-1992  (Age: 31)"),
        ("Policy No:", primary_policy_no),
        ("Plan:", "Plan A -- Insurer1  (Primary Policyholder)"),
        ("Secondary:", f"Plan B -- Insurer2  (Dependent under {secondary_subscriber})"),
        ("Employer:", "FinServ Solutions Ltd., Mumbai"),
    ]:
        pdf.kv(k, v)
    pdf.ln(2)


    pdf.section_title("2. CLINICAL JUSTIFICATION")
    # Extract clinical details dynamically from PT invoice (using actual field names from intake agent)
    diagnosis = pt.get("diagnosis_mentioned")  # intake agent uses "diagnosis_mentioned"
    icd_codes = pt.get("inferred_icd10_codes", [])
    icd_code = icd_codes[0] if icd_codes else None
    referring_doctor = pt.get("referring_doctor")
    clinic_name = pt.get("clinic_name")
    # service_period is constructed from line_items dates
    line_items = pt.get("line_items", [])
    if line_items:
        dates = [item.get("date") for item in line_items if item.get("date")]
        service_period = f"{dates[0]} -- {dates[-1]}  ({len(line_items)} sessions)" if dates else None
    else:
        service_period = None
    
    if not all([diagnosis, icd_code, referring_doctor, clinic_name, service_period]):
        raise ValueError(f"Missing required PT invoice details: diagnosis={diagnosis}, icd_code={icd_code}, referring_doctor={referring_doctor}, clinic_name={clinic_name}, service_period={service_period}")


    
    for k, v in [
        ("Diagnosis:", diagnosis),
        ("ICD-10:", f"{icd_code} -- Low back pain"),
        ("Referring Dr:", referring_doctor),
        ("Clinic:", clinic_name),
        ("Period:", service_period),
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
    
    # Generate service table dynamically from PT invoice line items
    line_items = pt.get("line_items", [])
    if not line_items:
        # Fallback if line_items not found in state
        line_items = [
            {"cpt_code": "97161", "description": "PT Evaluation -- High Complexity", "units": 1, "amount_inr": 2000},
            {"cpt_code": "97110", "description": "Therapeutic Exercise (x10 sessions)", "units": 10, "amount_inr": 15000},
            {"cpt_code": "97140", "description": "Manual Therapy -- Spinal Mobilisation", "units": 2, "amount_inr": 4000},
            {"cpt_code": "97112", "description": "Neuromuscular Re-education", "units": 1, "amount_inr": 2000},
            {"cpt_code": "97110", "description": "Therapeutic Exercise + Dry Needling", "units": 1, "amount_inr": 2500},
        ]
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(200, 212, 240)
    pdf.cell(28, 6, "CPT", fill=True, border=1)
    pdf.cell(100, 6, "Service", fill=True, border=1)
    pdf.cell(15, 6, "Units", fill=True, border=1)
    pdf.cell(0,  6, "Rs.", fill=True, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    
    for item in line_items:
        code = str(item.get("cpt_code", ""))[:12]
        desc = str(item.get("description", ""))[:50]
        units = str(item.get("units", "1"))
        amt = f"{item.get('amount_inr', 0):,.0f}"
        pdf.cell(28, 6, code, border=1)
        pdf.cell(100, 6, desc, border=1)
        pdf.cell(15, 6, units, border=1, align="C")
        pdf.cell(0, 6, amt, border=1, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Extract total dynamically
    total_amount = pt.get("total_amount_inr", 30000)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(143, 6, "TOTAL (incl. GST 5%)", border=1, fill=True)
    pdf.cell(0, 6, f"{total_amount:,.0f}", border=1, fill=True, align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)


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

def generate_patient_audio_briefing(state: dict):
    """Generate audio briefing from text briefing (offline TTS)."""
    print("  [OUTPUT] Generating patient audio briefing...")
    
    text_path = OUTPUT_DIR / "patient_briefing.txt"
    if not text_path.exists():
        raise FileNotFoundError("patient_briefing.txt must be generated first")
    
    briefing_text = text_path.read_text(encoding="utf-8")
    
    # Remove header decorations and focus on patient-friendly content
    lines = briefing_text.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        if 'Hi Aarav and Priya' in line:
            start_idx = i
            break
    
    audio_text = '\n'.join(lines[start_idx:])
    
    # Generate speech using offline TTS
    audio_path = OUTPUT_DIR / "patient_briefing.mp3"
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
        engine.save_to_file(audio_text, str(audio_path))
        engine.runAndWait()
        print(f"  [OUTPUT] Saved -> {audio_path}")
    except Exception as e:
        # Graceful fallback if TTS fails
        print(f"  [OUTPUT] Audio generation skipped (error: {type(e).__name__})")
        print(f"  [OUTPUT] Text briefing available at: {text_path}")
        return None
    
    return audio_path


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
    audio    = generate_patient_audio_briefing(state)  # ADD THIS LINE

    state["agent_state"] = "DONE"
    state["outputs"] = {
        "aarav_preauth_letter": str(letter_a),
        "priya_preauth_letter": str(letter_p),
        "cost_flow_chart":      str(chart),
        "patient_briefing":     str(briefing),
        "patient_audio_briefing": str(audio),  # ADD THIS LINE
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