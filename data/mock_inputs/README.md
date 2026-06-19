# Mock Input Files

These files simulate the real-world documents that DuCO-Agent ingests and processes.

## Files

| File | Type | Simulates |
|---|---|---|
| `user_query.txt` | Text | Aarav's voice-to-text transcript |
| `aarav_mri_report.pdf` | PDF | Radiology MRI report confirming ACL + meniscus tear |
| `priya_pt_invoice.png` | Image | PT clinic invoice — no CPT codes, agent must infer |
| `surgeon_estimate.jpg` | Image | Surgeon billing sheet with CPT 29888 and 29881 |

## Notes
- All files are programmatically generated via `scripts/generate_mock_inputs.py`
- The PT invoice deliberately omits ICD-10 and CPT codes to test agent inference
- ICD-10 codes used: S83.511A (ACL tear), S83.211A (meniscus tear), M54.5 (back pain)
- CPT codes used: 29888, 29881 (surgery), 97161, 97110 (PT — to be inferred)