# DuCO-Agent: Dual Coverage Optimisation AI System

An agentic, multi-modal AI system that automates Coordination of Benefits (COB)
for patients with dual health insurance coverage.

Built for: Prudential Health India — Engineering Internship Assessment

---

## The Problem

Priya and Aarav Sen (Mumbai) have dual corporate health insurance:
- **Plan A (Insurer1):** Priya is Primary Policyholder, Aarav is Dependent
- **Plan B (Insurer2):** Aarav is Primary Policyholder, Priya is Dependent

Aarav needs ACL surgery (₹4,50,000). Priya has unpaid PT bills (₹30,000).
Navigating which insurer pays first, calculating exact out-of-pocket costs,
and generating pre-authorization letters manually is error-prone and complex.

DuCO-Agent solves this autonomously.

---

## Quickstart

```bash
# 1. Clone and set up environment
git clone https://github.com/Dhruthi9701/duco-agent-ai-assessment.git
cd duco-agent-ai-assessment
pip install -r requirements.txt

# 2. Set your Gemini API key (free at aistudio.google.com)
set GEMINI_API_KEY=your-key-here        # Windows
export GEMINI_API_KEY=your-key-here     # Mac/Linux

# 3. Generate mock input files
python scripts/generate_mock_inputs.py

# 4. Run the full pipeline
python main.py
```

Run individual steps:
```bash
python main.py --step intake    # extract data from all 4 inputs
python main.py --step cob       # calculate COB payments
python main.py --step output    # generate PDFs and chart
```

---

## Results

| | Aarav (ACL Surgery) | Priya (PT Bills) |
|---|---|---|
| Total Billed | ₹4,50,000 | ₹30,000 |
| Primary Pays | ₹4,05,000 (Insurer2) | ₹24,000 (Insurer1) |
| Secondary Pays | ₹36,000 (Insurer1) | ₹5,400 (Insurer2) |
| **Patient Pays** | **₹9,000** | **₹600** |

**Family saves ₹4,70,400 (98%) through dual coverage coordination.**

---

## Agent Architecture

DuCO-Agent is a true state machine — not a linear script.
Each state has a name, a purpose, and an explicit transition condition.

```
┌─────────────┐     ┌─────────────┐     ┌───────────────┐     ┌──────────────────┐     ┌──────┐
│   INTAKE    │────▶│  REFLECTING │────▶│  COB_READY    │────▶│  COB_REASONING   │────▶│ DONE │
│             │     │             │     │               │     │                  │     │      │
│ 4 extractors│     │ Self-audit  │     │ Validation    │     │ Tool calls +     │     │ PDFs │
│ text/PDF/   │     │ cross-doc   │     │ loop checks   │     │ primary/secondary│     │ Chart│
│ 2x vision   │     │ consistency │     │ completeness  │     │ math + audit     │     │ Brief│
└─────────────┘     └─────────────┘     └───────────────┘     └──────────────────┘     └──────┘
```

### Rubric → Code Mapping

| Rubric Item | Where it lives |
|---|---|
| **State transitions** | `agent_state` field in `data/state.json` — transitions: INTAKE → REFLECTING → COB_READY → COB_REASONING → OUTPUT_READY → DONE |
| **Reflection loop** | `reflect_and_audit()` in `src/agents/intake_agent.py` — re-examines its own extraction, catches hallucinated line items, resolves patient identity across documents |
| **Tool use** | `src/tools/insurer_api.py` — `call_tool()` dispatcher calls `get_plan_details`, `request_pre_authorization`, `verify_coverage` |
| **Validation loop** | `validate_extracted_state()` in `src/agents/intake_agent.py` — checks all required fields before proceeding |
| **Math self-audit** | `audit_cob_math()` in `src/engine/cob_engine.py` — verifies primary + secondary + patient = total billed |
| **Multi-modal extraction** | PDF text (PyMuPDF) + image vision (Gemini) + plain text — all in `src/agents/intake_agent.py` |
| **CPT code inference** | PT invoice has no codes — agent infers CPT 97161, 97110, 97140, 97112 from service descriptions |
| **COB logic** | `src/engine/cob_engine.py` — subscriber rule determines primary/secondary per patient |
| **Pre-auth letters** | `src/agents/output_generator.py` — professional PDFs with ICD-10 codes, clinical justification, COB breakdown |
| **Cost flow visual** | `src/agents/output_generator.py` — matplotlib chart with % labels and family savings summary |
| **Patient briefing** | `outputs/patient_briefing.txt` — plain language summary with next steps |

---

## Project Structure

```
duco-agent-ai-assessment/
│
├── main.py                        # Single entry point — runs full pipeline
├── requirements.txt
│
├── data/
│   └── mock_inputs/
│       ├── user_query.txt         # Aarav's voice transcript
│       ├── aarav_mri_report.pdf   # MRI report (PDF — parsed with PyMuPDF)
│       ├── priya_pt_invoice.png   # PT invoice (image — no CPT codes, agent infers)
│       └── surgeon_estimate.jpg   # Surgeon billing sheet (image — CPT 29888, 29881)
│
├── scripts/
│   └── generate_mock_inputs.py    # Generates all 4 mock input files
│
├── src/
│   ├── agents/
│   │   ├── intake_agent.py        # INTAKE + REFLECTING states
│   │   └── output_generator.py    # GENERATING_OUTPUTS state
│   ├── engine/
│   │   └── cob_engine.py          # COB_REASONING state
│   ├── tools/
│   │   └── insurer_api.py         # Mock insurer API tool (3 endpoints)
│   └── utils/
│       └── helpers.py             # Shared: to_number, format_inr, load/save state
│
└── outputs/                       # Auto-generated (not committed)
    ├── aarav_preauth_letter.pdf
    ├── priya_preauth_letter.pdf
    ├── cost_flow_chart.png
    └── patient_briefing.txt
```

---

## Multi-Modal Inputs

| File | Type | Challenge | How Agent Handles It |
|---|---|---|---|
| `user_query.txt` | Plain text | Ambiguous speaker identity | REFLECT state cross-references MRI patient to resolve "I" |
| `aarav_mri_report.pdf` | PDF | Clinical terminology | PyMuPDF extracts text; Gemini structures findings + ICD-10 codes |
| `priya_pt_invoice.png` | Scanned image | No CPT codes listed | Gemini vision infers CPT 97161/97110/97140/97112 from service names |
| `surgeon_estimate.jpg` | Billing image | Risk of hallucinated line items | REFLECT state re-grounds extraction against source image |

---

## COB Logic

**Subscriber Rule** (standard Indian dual-coverage COB):

- For **Aarav's surgery**: Plan B (Insurer2) is PRIMARY — he is the subscriber.
  Plan A (Insurer1) is SECONDARY — he is a dependent there.

- For **Priya's PT bills**: Plan A (Insurer1) is PRIMARY — she is the subscriber.
  Plan B (Insurer2) is SECONDARY — she is a dependent there.

**Payment formula** (both deductibles already met — mid-year scenario):
```
Primary pays  = Total × (1 - primary_coinsurance%)
Remaining     = Total × primary_coinsurance%
Secondary pays = Remaining × (1 - secondary_coinsurance%)
Patient pays  = Remaining × secondary_coinsurance%
```

Math is verified by `audit_cob_math()` after every calculation.

---

## Mock Insurer API Tools

Three tools in `src/tools/insurer_api.py`:

| Tool | Simulates |
|---|---|
| `get_plan_details(plan_key)` | GET /api/v1/plans/{id} — returns deductible, coinsurance, OOP max |
| `request_pre_authorization(plan, cpts, patient, dx_codes)` | POST /api/v1/preauth — returns decision + auth number |
| `verify_coverage(plan_key, cpt_codes)` | GET /api/v1/coverage/verify — checks which CPTs are covered |

All tool calls are routed through `call_tool()` dispatcher for logging and auditability.

---

## Tech Stack

| Component | Library |
|---|---|
| LLM + Vision | Google Gemini 2.5 Flash (free tier) |
| PDF parsing | PyMuPDF (fitz) |
| PDF generation | fpdf2 |
| Charts | matplotlib |
| Image generation | Pillow |
| Mock input generation | Pillow + fpdf2 |

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `feature/mock-inputs` | Generated all 4 mock input files |
| `feature/intake-agent` | Multi-modal extraction + reflection state |
| `feature/cob-logic` | COB engine + math audit |
| `feature/multi-modal-outputs` | Pre-auth PDFs + cost flow chart |
| `feature/agent-architecture` | Insurer API tool + utils + main.py |

All development on feature branches. No direct commits to `main`.
All merges via Pull Requests with semantic commit messages (`feat:`, `fix:`, `docs:`, `chore:`).

---

## Design Notes

**Why Gemini 2.5 Flash?**
Strong vision capability for reading scanned invoices and billing sheets.
Free tier covers the entire pipeline with no billing setup required.

**Why a state machine instead of a linear chain?**
Each state is independently restartable (`python main.py --step cob`).
State is persisted to `data/state.json` after every transition — full auditability.
The REFLECT state can loop back and correct earlier extractions before proceeding.

**Real-world extension:**
Replace `src/tools/insurer_api.py` mock responses with real insurer REST endpoints.
Replace `data/mock_inputs/` with a document upload UI.
The agent pipeline stays identical.