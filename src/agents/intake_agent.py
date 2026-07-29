"""
DuCO-Agent | Intake Agent
State: INTAKE
Reads all 4 mock input files, extracts structured medical/billing data,
validates completeness, and saves state to data/state.json
"""

import os
import re
import json
import base64
from pathlib import Path
from google import genai
from google.genai import types

DATA_DIR   = Path("data/mock_inputs")
STATE_PATH = Path("data/state.json")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.6-flash"


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_pdf_as_text(path: Path) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    import fitz  # PyMuPDF
    doc = fitz.open(str(path))
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def image_to_base64(path: Path) -> tuple[str, str]:
    """Return (base64_data, media_type) for an image file."""
    suffix = path.suffix.lower()
    media_type_map = {
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    media_type = media_type_map.get(suffix, "image/jpeg")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return data, media_type


def to_number(value) -> float:
    """Coerce a possibly-string/None money value into a number.
    Handles 350000, "350000", "₹3,50,000", "Rs. 3,50,000", and None —
    returns 0 if nothing numeric can be found."""
    if isinstance(value, (int, float)):
        return value
    if value is None:
        return 0
    digits = re.sub(r"[^\d.]", "", str(value))
    return float(digits) if digits else 0


def ask_gemini(system_prompt: str, user_content: list) -> str:
    """Send a message to Gemini and return the text response.

    Accepts the SAME content-block format the rest of this file already
    uses (Anthropic-style: {"type": "text", ...} / {"type": "image", ...}),
    so none of the extract_* functions below needed to change — only this
    adapter and the client setup at the top did.
    """
    parts = []
    for block in user_content:
        if block["type"] == "text":
            parts.append(block["text"])
        elif block["type"] == "image":
            src = block["source"]
            image_bytes = base64.standard_b64decode(src["data"])
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type=src["media_type"]))
        else:
            raise ValueError(f"Unsupported content block type: {block['type']}")

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",  # forces clean JSON, no markdown fences
        ),
    )
    return response.text


# ─────────────────────────────────────────────────────────────
# EXTRACTION FUNCTIONS (one per input file)
# ─────────────────────────────────────────────────────────────

def extract_user_query(path: Path) -> dict:
    """Parse the plain-text voice transcript."""
    print("  [INTAKE] Reading user_query.txt...")
    text = read_text_file(path)

    prompt = """You are a medical intake assistant.
Extract the following from this voice transcript and return ONLY a JSON object, no extra text:
{
  "patient_requesting": "<name>",
  "procedures_mentioned": ["<list>"],
  "insurers_mentioned": ["<list>"],
  "questions_asked": ["<list>"]
}"""

    result = ask_gemini(prompt, [{"type": "text", "text": text}])
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        # Strip markdown fences if present (kept as a safety net)
        clean = result.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)


def extract_mri_report(path: Path) -> dict:
    """Parse the MRI PDF and extract clinical findings."""
    print("  [INTAKE] Reading aarav_mri_report.pdf...")
    text = read_pdf_as_text(path)

    prompt = """You are a clinical data extraction assistant.
Extract the following from this MRI radiology report and return ONLY a JSON object, no extra text:
{
  "patient_name": "<name>",
  "patient_age": "<age>",
  "study_date": "<date>",
  "primary_diagnosis": "<main diagnosis>",
  "findings": ["<finding 1>", "<finding 2>", "..."],
  "icd10_codes": ["<code: description>", "..."],
  "surgical_recommendation": "<yes/no and details>"
}"""

    result = ask_gemini(prompt, [{"type": "text", "text": text}])
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        clean = result.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)


def extract_pt_invoice(path: Path) -> dict:
    """Extract billing info from the PT invoice image.
    Note: invoice has NO CPT codes — agent must infer them."""
    print("  [INTAKE] Reading priya_pt_invoice.png (vision)...")
    img_data, media_type = image_to_base64(path)

    prompt = """You are a medical billing assistant with expert knowledge of CPT codes.
Extract the following from this physical therapy invoice image and return ONLY a JSON object, no extra text.
IMPORTANT: The invoice does NOT list CPT codes. You must infer them per LINE ITEM from each
service description, using your clinical/billing knowledge. Only list line items that are
literally printed on the invoice with their actual date and amount — do not add or invent rows.
Reference mappings (apply the closest match per line, not just these four):
  "Physical Therapy Evaluation" -> CPT 97161
  "Therapeutic Exercise" -> CPT 97110
  "Manual Therapy" / "Spinal Mobilisation" -> CPT 97140
  "Neuromuscular Re-education" -> CPT 97112
  "Heat Therapy" / "hot or cold packs" -> CPT 97010
  "Dry Needling" -> CPT 20560
  "Flexibility / Posture / Advanced Progression / Home Programme" -> CPT 97110 (therapeutic exercise variant)
Also capture any referring doctor, clinic address, GST/invoice number, and billing-admin
handwritten notes that are visible — these are real fields on the document, extract them
if present rather than leaving them out.

Return ONLY this JSON:
{
  "patient_name": "<name>",
  "patient_age_gender": "<as printed, e.g. '31 Years / Female'>",
  "clinic_name": "<clinic>",
  "clinic_address": "<address if visible, else empty string>",
  "invoice_no": "<invoice number if visible>",
  "invoice_date": "<date>",
  "referring_doctor": "<name + title if printed on the invoice, else empty string>",
  "diagnosis_mentioned": "<diagnosis>",
  "line_items": [
    {
      "date": "<DD-Mon-YY as printed>",
      "description": "<exact service description printed>",
      "amount_inr": <number>,
      "inferred_cpt_code": "<best-matching CPT code>",
      "inferred_cpt_description": "<short CPT description>"
    }
  ],
  "inferred_icd10_codes": ["<ICD-10 code: description>"],
  "subtotal_inr": <number, if shown separately>,
  "gst_inr": <number, if shown, else 0>,
  "total_amount_inr": <number>,
  "payment_status": "<paid/unpaid, as printed>",
  "billing_admin_notes": ["<any handwritten/note line, verbatim>"],
  "cpt_inference_note": "Codes inferred per line item by agent as invoice did not list them explicitly"
}"""

    result = ask_gemini(
        prompt,
        [{"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_data}}],
    )
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        clean = result.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)


def extract_surgeon_estimate(path: Path) -> dict:
    """Extract CPT codes and costs from the surgeon billing estimate image."""
    print("  [INTAKE] Reading surgeon_estimate.jpg (vision)...")
    img_data, media_type = image_to_base64(path)

    prompt = """You are a surgical billing assistant.
Extract the following from this surgeon cost estimate image and return ONLY a JSON object, no extra text.
IMPORTANT: Only include procedures that are literally printed on the estimate. Do not add
typical/standard line items (e.g. anesthesia, implants) unless they are explicitly itemized
in the image — an empty or shorter "procedures" list is correct if that's all that's shown.
{
  "patient_name": "<name>",
  "surgeon_name": "<name>",
  "hospital_name": "<name>",
  "estimate_date": "<date>",
  "diagnosis": "<diagnosis>",
  "procedures": [
    {
      "cpt_code": "<code>",
      "description": "<description>",
      "icd10_code": "<code>",
      "amount_inr": <number>
    }
  ],
  "total_surgical_amount_inr": <number>,
  "pre_auth_required": <true/false>,
  "dual_coverage_noted": <true/false>
}"""

    result = ask_gemini(
        prompt,
        [{"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_data}}],
    )
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        clean = result.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)


# ─────────────────────────────────────────────────────────────
# REFLECTION STATE
# ─────────────────────────────────────────────────────────────

def reflect_and_audit(state: dict, surgeon_image_path: Path) -> dict:
    """
    Agentic REFLECT state.
    Re-examines the assembled intake state instead of trusting each of the
    four extractions in isolation. Two checks:
      1. Patient identity — resolves who "I" is in the voice transcript by
         cross-referencing the clinical evidence (MRI patient), rather than
         trusting whichever name the transcript-only extraction happened to see.
      2. Re-grounding — re-sends the surgeon estimate image alongside its own
         earlier extraction and asks the model to remove any line item that
         isn't literally visible in the image, catching hallucinated entries.
    Corrections are applied to state AND logged in state["reflection_audit"]
    so the reasoning is auditable, not silently overwritten.
    """
    print("\n  [REFLECT] Cross-checking patient identity and re-grounding surgeon estimate...")

    img_data, media_type = image_to_base64(surgeon_image_path)

    system_prompt = """You are a senior medical-billing auditor agent. You are reviewing
output that was already extracted by an earlier AI step, and your job is to catch its
mistakes — do not assume it is correct.

TASK 1 — Patient identity check:
The user_query transcript is a first-person recording. The speaker says "I need my knee
operated on soon, and Priya has some physical therapy bills." Cross-reference this against
the MRI report's patient (the knee-surgery patient) to determine who the speaker actually is.
If user_query.patient_requesting does not match, correct it and explain why in one sentence.

TASK 2 — Re-ground the surgeon estimate against the attached image:
Compare the extracted "procedures" list line-by-line against the image. Keep ONLY items that
are literally printed there. Remove anything inferred, templated, or invented — including
standard items like anesthesia or implants if they are not explicitly itemized in the image.

Return ONLY this JSON, no extra text:
{
  "corrected_patient_requesting": "<name>",
  "patient_correction_reason": "<one sentence, or empty string if no correction needed>",
  "validated_procedures": [<the procedures array, corrected>],
  "removed_hallucinated_items": ["<short description of anything removed>"],
  "audit_notes": ["<any other cross-document inconsistency found, if any>"]
}"""

    user_content = [
        {"type": "text", "text": f"FULL EXTRACTED STATE:\n{json.dumps(state, indent=2)}"},
        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_data}},
    ]

    result = ask_gemini(system_prompt, user_content)
    try:
        audit = json.loads(result)
    except json.JSONDecodeError:
        clean = result.strip().removeprefix("```json").removesuffix("```").strip()
        audit = json.loads(clean)

    # --- Apply corrections (the agent acting on its own reflection) ---
    if audit.get("corrected_patient_requesting"):
        state["user_query"]["patient_requesting"] = audit["corrected_patient_requesting"]

    if audit.get("validated_procedures"):
        state["surgeon_estimate"]["procedures"] = audit["validated_procedures"]
        state["surgeon_estimate"]["total_surgical_amount_inr"] = sum(
            to_number(p.get("amount_inr", 0)) for p in audit["validated_procedures"]
        )

    state["reflection_audit"] = audit

    if audit.get("patient_correction_reason"):
        print(f"  [REFLECT] Patient identity corrected: {audit['patient_correction_reason']}")
    if audit.get("removed_hallucinated_items"):
        print(f"  [REFLECT] Removed {len(audit['removed_hallucinated_items'])} unverified line item(s)")
    if not audit.get("patient_correction_reason") and not audit.get("removed_hallucinated_items"):
        print("  [REFLECT] No corrections needed.")

    return state


# ─────────────────────────────────────────────────────────────
# VALIDATION LOOP
# ─────────────────────────────────────────────────────────────

def validate_extracted_state(state: dict) -> list[str]:
    """
    Agentic validation loop:
    Check that all required fields were successfully extracted.
    Returns a list of missing/invalid fields.
    """
    import re as _re
    issues = []

    # Check MRI
    mri = state.get("mri_report", {})
    if not mri.get("primary_diagnosis"):
        issues.append("mri_report.primary_diagnosis is missing")
    if not mri.get("icd10_codes"):
        issues.append("mri_report.icd10_codes is missing")

    # Check PT invoice
    pt = state.get("pt_invoice", {})
    line_items = pt.get("line_items", [])
    if not line_items:
        issues.append("pt_invoice.line_items — agent failed to extract/infer any line items")
    elif any(not li.get("inferred_cpt_code") for li in line_items):
        issues.append("pt_invoice.line_items — one or more rows missing an inferred CPT code")
    if not pt.get("total_amount_inr"):
        issues.append("pt_invoice.total_amount_inr is missing")

    # Check surgeon estimate — also validate CPT code format
    surg = state.get("surgeon_estimate", {})
    procedures = surg.get("procedures", [])
    if not procedures:
        issues.append("surgeon_estimate.procedures is missing")
    else:
        # Warn (non-fatal) if any CPT code is malformed (e.g. "CPT00400" instead of "CPT 00400")
        # The COB engine handles this at runtime, but log it for traceability
        malformed = [
            p.get("cpt_code") for p in procedures
            if p.get("cpt_code") and p["cpt_code"] not in ("IMPLANTS",)
            and not _re.match(r"^(CPT\s*)?\d{5}$|^IMPLANTS$", str(p.get("cpt_code", "")).strip())
        ]
        if malformed:
            issues.append(
                f"surgeon_estimate.procedures — malformed CPT token(s) detected: {malformed}. "
                "COB engine will normalise these; verify source image."
            )
    if not surg.get("total_surgical_amount_inr"):
        issues.append("surgeon_estimate.total_surgical_amount_inr is missing")

    # Check query
    query = state.get("user_query", {})
    if not query.get("insurers_mentioned"):
        issues.append("user_query.insurers_mentioned is missing")

    return issues


# ─────────────────────────────────────────────────────────────
# RETRY LOOP
# ─────────────────────────────────────────────────────────────

# Maps a validation-issue prefix to the extractor that can fix it,
# and where in `state` + which input file to re-run it against.
_ISSUE_TO_EXTRACTOR = {
    "mri_report":     (extract_mri_report,       DATA_DIR / "aarav_mri_report.pdf"),
    "pt_invoice":      (extract_pt_invoice,        DATA_DIR / "priya_pt_invoice.png"),
    "surgeon_estimate": (extract_surgeon_estimate, DATA_DIR / "surgeon_estimate.jpg"),
    "user_query":      (extract_user_query,        DATA_DIR / "user_query.txt"),
}


def retry_failed_extractions(state: dict, issues: list[str], max_retries: int = 1) -> dict:
    """
    Agentic self-correction loop.
    For each distinct top-level field a validation issue points at, re-run
    that field's extractor (LLM call repeated, not just re-read from cache)
    up to `max_retries` times. This is what turns "validation" from a
    reporting step into an actual closed loop: detect -> retry -> re-check.
    """
    broken_keys = {issue.split(".")[0] for issue in issues if "." in issue}
    for key in broken_keys:
        extractor, path = _ISSUE_TO_EXTRACTOR.get(key, (None, None))
        if not extractor:
            continue
        for attempt in range(1, max_retries + 1):
            print(f"  [RETRY] Re-running extractor for '{key}' (attempt {attempt}/{max_retries})...")
            try:
                state[key] = extractor(path)
            except Exception as e:
                print(f"  [RETRY] '{key}' extractor raised {type(e).__name__}: {e}")
                continue
    return state


# ─────────────────────────────────────────────────────────────
# MAIN INTAKE AGENT
# ─────────────────────────────────────────────────────────────

def run_intake_agent():
    print("\n" + "="*50)
    print("DuCO-Agent | INTAKE STATE")
    print("="*50)

    # --- State transition: start ---
    state = {"agent_state": "INTAKE", "validation_status": "PENDING"}

    # --- Extract all 4 inputs ---
    state["user_query"]       = extract_user_query(DATA_DIR / "user_query.txt")
    state["mri_report"]       = extract_mri_report(DATA_DIR / "aarav_mri_report.pdf")
    state["pt_invoice"]       = extract_pt_invoice(DATA_DIR / "priya_pt_invoice.png")
    state["surgeon_estimate"] = extract_surgeon_estimate(DATA_DIR / "surgeon_estimate.jpg")

    # --- State transition: reflection / self-audit ---
    state["agent_state"] = "REFLECTING"
    state = reflect_and_audit(state, DATA_DIR / "surgeon_estimate.jpg")

    # --- Validation loop ---
    print("\n  [VALIDATE] Running completeness check...")
    issues = validate_extracted_state(state)

    if issues:
        print(f"  [VALIDATE] WARNING — {len(issues)} issue(s) found:")
        for issue in issues:
            print(f"    - {issue}")

        # --- Agentic self-correction: retry the specific broken extractors ---
        state = retry_failed_extractions(state, issues, max_retries=1)

        print("\n  [VALIDATE] Re-checking after retry...")
        issues = validate_extracted_state(state)
        if issues:
            print(f"  [VALIDATE] STILL {len(issues)} issue(s) after retry:")
            for issue in issues:
                print(f"    - {issue}")
            state["validation_status"] = "INCOMPLETE"
            state["validation_issues"] = issues
        else:
            print("  [VALIDATE] All issues resolved after retry.")
            state["validation_status"] = "COMPLETE"
            state["validation_issues"] = []
    else:
        print("  [VALIDATE] All required fields extracted successfully.")
        state["validation_status"] = "COMPLETE"

    # --- State transition: ready for COB ---
    state["agent_state"] = "COB_READY" if state["validation_status"] == "COMPLETE" else "INTAKE_FAILED"

    # --- Save state ---
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(f"\n  [STATE] Saved to {STATE_PATH}")
    print(f"  [STATE] Agent state → {state['agent_state']}")
    print("="*50 + "\n")

    return state


if __name__ == "__main__":
    result = run_intake_agent()
    print(json.dumps(result, indent=2, ensure_ascii=False))