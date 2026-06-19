"""
DuCO-Agent Mock Input Generator
Generates all 4 required input files into data/mock_inputs/
Run: python generate_mock_inputs.py
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF

OUTPUT_DIR = "data/mock_inputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# FILE 1: user_query.txt
# ─────────────────────────────────────────────
def create_user_query():
    path = os.path.join(OUTPUT_DIR, "user_query.txt")
    content = (
        "Hi DuCO-Agent, I need to get my knee operated on soon, and Priya has some "
        "physical therapy bills lying around. We have Insurer1 (Plan A) and Insurer2 "
        "(Plan B). Can you help us figure out which plan pays first for my surgery and "
        "her bills? How much will we actually have to pay out of our own pocket? Also, "
        "we need the pre-auth letters generated for both insurers so we don't end up "
        "with a claim rejection. Please help!"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [OK] {path}")


# ─────────────────────────────────────────────
# FILE 2: aarav_mri_report.pdf
# ─────────────────────────────────────────────
def create_mri_report():
    path = os.path.join(OUTPUT_DIR, "aarav_mri_report.pdf")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "RADIOLOGY REPORT - MRI KNEE", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "HealthScan Diagnostics Pvt. Ltd.", ln=True, align="C")
    pdf.cell(0, 6, "14, MG Road, Mumbai - 400001 | Tel: 022-4567-8900", ln=True, align="C")
    pdf.ln(4)

    # Divider
    pdf.set_draw_color(100, 100, 100)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    # Patient details table
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(45, 7, "Patient Name:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(80, 7, "Aarav Sen", border=0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 7, "Report No:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "RAD-2024-08821", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(45, 7, "Age / Gender:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(80, 7, "34 Years / Male", border=0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 7, "Date:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "12-May-2024", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(45, 7, "Referring Doctor:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(80, 7, "Dr. Ramesh Nair, Orthopaedic Surgeon", border=0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 7, "Modality:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "MRI 3.0 Tesla", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(45, 7, "Study:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "MRI Right Knee - Sagittal, Coronal & Axial Sequences", ln=True)
    pdf.ln(3)

    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    # Clinical history
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "CLINICAL HISTORY", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "Patient is a 34-year-old male who sustained a sports injury during a football "
        "match approximately 3 weeks prior. Complaints of severe right knee pain, "
        "swelling, and inability to fully extend the knee. Physical examination revealed "
        "positive Lachman test and anterior drawer sign.")
    pdf.ln(3)

    # Findings
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "FINDINGS", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "1. Anterior Cruciate Ligament (ACL):", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "There is a complete tear of the anterior cruciate ligament (ACL) with "
        "disruption of fibres at the mid-substance level. The ligament demonstrates "
        "abnormal signal intensity on all sequences. No residual intact fibres are "
        "identified. Associated bone bruising is noted at the lateral femoral condyle "
        "and posterolateral tibial plateau, consistent with a pivot-shift mechanism "
        "of injury. ICD-10: S83.511A - Sprain of anterior cruciate ligament of right knee.")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "2. Medial Meniscus:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "There is a medial meniscus tear involving the posterior horn. The tear "
        "demonstrates a horizontal cleavage pattern extending to the inferior articular "
        "surface. Grade III signal intensity is observed on proton density sequences. "
        "ICD-10: S83.211A - Bucket-handle tear of medial meniscus, right knee.")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "3. Lateral Meniscus:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "Lateral meniscus appears intact with no evidence of tear or degeneration.")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "4. Posterior Cruciate Ligament (PCL):", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "PCL is intact with normal signal intensity and morphology.")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "5. Articular Cartilage:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "Mild chondromalacia of the medial femoral condyle (Grade I-II). "
        "Patellofemoral cartilage appears preserved.")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "6. Joint Effusion:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "Moderate joint effusion with haemarthrosis noted in the suprapatellar bursa.")
    pdf.ln(3)

    # Impression
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "IMPRESSION", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        "1. Complete tear of the right Anterior Cruciate Ligament (ACL) with "
        "associated pivot-shift bone contusions.\n"
        "2. Horizontal cleavage tear of the posterior horn of the medial meniscus.\n"
        "3. Moderate haemarthrosis.\n"
        "4. Mild medial femoral condyle chondromalacia.\n\n"
        "Clinical correlation recommended. Surgical intervention (ACL reconstruction "
        "with possible meniscal repair/resection) is advised.")
    pdf.ln(5)

    # Signature
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Dr. Prabhavati Iyer, MD (Radiology), DNB", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Senior Radiologist, HealthScan Diagnostics", ln=True)
    pdf.cell(0, 6, "Reg. No: MCI-2024-RAD-04412", ln=True)

    pdf.output(path)
    print(f"  [OK] {path}")


# ─────────────────────────────────────────────
# FILE 3: priya_pt_invoice.png
# ─────────────────────────────────────────────
def create_pt_invoice():
    path = os.path.join(OUTPUT_DIR, "priya_pt_invoice.png")

    # Slightly off-white background to simulate paper
    width, height = 900, 1100
    img = Image.new("RGB", (width, height), color=(248, 245, 238))
    draw = ImageDraw.Draw(img)

    # Simulate slight paper texture (random noise pixels)
    random.seed(42)
    for _ in range(3000):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        shade = random.randint(220, 255)
        img.putpixel((x, y), (shade, shade, shade - 10))

    # Helper to use default font at different sizes
    def font(size):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except:
            return ImageFont.load_default()

    def bold_font(size):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except:
            return ImageFont.load_default()

    # Clinic header
    draw.rectangle([30, 30, 870, 130], outline=(50, 80, 150), width=2)
    draw.text((450, 50), "CureMotion Physiotherapy Clinic", font=bold_font(26), fill=(30, 50, 130), anchor="mm")
    draw.text((450, 82), "B-12, Andheri West, Mumbai - 400058", font=font(16), fill=(80, 80, 80), anchor="mm")
    draw.text((450, 104), "Tel: 022-2689-4410 | GST: 27AADCC1234F1Z5", font=font(14), fill=(100, 100, 100), anchor="mm")

    # Invoice title
    draw.text((450, 155), "PHYSICAL THERAPY INVOICE", font=bold_font(22), fill=(20, 20, 20), anchor="mm")
    draw.line([30, 170, 870, 170], fill=(180, 180, 180), width=1)

    # Patient & invoice details
    draw.text((50, 185), "Patient Name :", font=bold_font(16), fill=(40, 40, 40))
    draw.text((230, 185), "Mrs. Priya Sen", font=font(16), fill=(20, 20, 20))
    draw.text((550, 185), "Invoice No :", font=bold_font(16), fill=(40, 40, 40))
    draw.text((680, 185), "INV-2024-PT-0091", font=font(16), fill=(20, 20, 20))

    draw.text((50, 212), "Age / Gender :", font=bold_font(16), fill=(40, 40, 40))
    draw.text((230, 212), "31 Years / Female", font=font(16), fill=(20, 20, 20))
    draw.text((550, 212), "Invoice Date :", font=bold_font(16), fill=(40, 40, 40))
    draw.text((680, 212), "18-May-2024", font=font(16), fill=(20, 20, 20))

    draw.text((50, 239), "Referring Doctor :", font=bold_font(16), fill=(40, 40, 40))
    draw.text((230, 239), "Dr. Sunita Mehta, Physiatrist", font=font(16), fill=(20, 20, 20))
    draw.text((550, 239), "Period :", font=bold_font(16), fill=(40, 40, 40))
    draw.text((680, 239), "01 Apr - 18 May 2024", font=font(16), fill=(20, 20, 20))

    draw.text((50, 266), "Diagnosis :", font=bold_font(16), fill=(40, 40, 40))
    draw.text((230, 266), "Chronic lower back pain - Lumbar region", font=font(16), fill=(20, 20, 20))

    draw.line([30, 290, 870, 290], fill=(150, 150, 150), width=1)

    # Table header
    draw.rectangle([30, 295, 870, 330], fill=(220, 228, 245))
    draw.text((50, 312), "Date", font=bold_font(15), fill=(20, 20, 80), anchor="lm")
    draw.text((180, 312), "Service Description", font=bold_font(15), fill=(20, 20, 80), anchor="lm")
    draw.text((590, 312), "Sessions", font=bold_font(15), fill=(20, 20, 80), anchor="lm")
    draw.text((710, 312), "Rate (Rs.)", font=bold_font(15), fill=(20, 20, 80), anchor="lm")
    draw.text((840, 312), "Amount", font=bold_font(15), fill=(20, 20, 80), anchor="rm")

    # Table rows - note: NO CPT codes listed (agent must infer them)
    rows = [
        ("01-Apr-24", "Physical Therapy Evaluation & Assessment", "1", "2,000", "2,000"),
        ("03-Apr-24", "Therapeutic Exercise - Core Strengthening", "1", "1,500", "1,500"),
        ("06-Apr-24", "Therapeutic Exercise - Lumbar Stabilisation", "1", "1,500", "1,500"),
        ("10-Apr-24", "Manual Therapy - Spinal Mobilisation", "1", "2,000", "2,000"),
        ("13-Apr-24", "Therapeutic Exercise & Heat Therapy", "1", "1,500", "1,500"),
        ("17-Apr-24", "Therapeutic Exercise - Flexibility Training", "1", "1,500", "1,500"),
        ("22-Apr-24", "Neuromuscular Re-education Session", "1", "2,000", "2,000"),
        ("26-Apr-24", "Therapeutic Exercise & Posture Correction", "1", "1,500", "1,500"),
        ("30-Apr-24", "Manual Therapy & Therapeutic Exercise", "1", "2,000", "2,000"),
        ("04-May-24", "Therapeutic Exercise - Advanced Progression", "1", "1,500", "1,500"),
        ("08-May-24", "Therapeutic Exercise & Dry Needling", "1", "2,500", "2,500"),
        ("12-May-24", "Therapeutic Exercise - Home Programme Review", "1", "1,500", "1,500"),
        ("15-May-24", "Therapeutic Exercise & Progress Evaluation", "1", "1,500", "1,500"),
        ("18-May-24", "Final Therapeutic Exercise & Discharge Plan", "1", "2,500", "2,500"),
    ]

    y = 340
    for i, (date, desc, sess, rate, amt) in enumerate(rows):
        bg = (252, 252, 252) if i % 2 == 0 else (244, 246, 252)
        draw.rectangle([30, y, 870, y + 26], fill=bg)
        draw.text((50, y + 13), date, font=font(13), fill=(40, 40, 40), anchor="lm")
        draw.text((180, y + 13), desc, font=font(13), fill=(40, 40, 40), anchor="lm")
        draw.text((610, y + 13), sess, font=font(13), fill=(40, 40, 40), anchor="mm")
        draw.text((730, y + 13), rate, font=font(13), fill=(40, 40, 40), anchor="mm")
        draw.text((850, y + 13), amt, font=font(13), fill=(40, 40, 40), anchor="rm")
        y += 26

    draw.line([30, y, 870, y], fill=(150, 150, 150), width=1)
    y += 10

    # Totals
    draw.text((680, y + 10), "Subtotal :", font=bold_font(15), fill=(40, 40, 40), anchor="rm")
    draw.text((850, y + 10), "Rs. 28,000", font=font(15), fill=(40, 40, 40), anchor="rm")

    draw.text((680, y + 32), "GST (5%) :", font=bold_font(15), fill=(40, 40, 40), anchor="rm")
    draw.text((850, y + 32), "Rs. 2,000", font=font(15), fill=(40, 40, 40), anchor="rm")

    draw.line([600, y + 50, 870, y + 50], fill=(100, 100, 100), width=1)

    draw.rectangle([600, y + 54, 870, y + 80], fill=(220, 228, 245))
    draw.text((680, y + 67), "TOTAL AMOUNT :", font=bold_font(16), fill=(20, 20, 100), anchor="rm")
    draw.text((850, y + 67), "Rs. 30,000", font=bold_font(16), fill=(20, 20, 100), anchor="rm")

    y += 95

    # Handwritten-style billing note (simulate admin note)
    draw.line([30, y, 870, y], fill=(180, 180, 180), width=1)
    y += 10
    draw.text((50, y + 5), "Billing Administrator Notes:", font=bold_font(14), fill=(80, 40, 40))
    # Slightly rotated feel via italic-ish font
    draw.text((50, y + 28), "Pt. completed full course of physio for lumbar back pain.", font=font(13), fill=(90, 50, 50))
    draw.text((50, y + 48), "Sessions include eval, therap. exercise & manual therapy.", font=font(13), fill=(90, 50, 50))
    draw.text((50, y + 68), "No ICD/CPT codes on file - to be coded by billing dept.", font=font(13), fill=(90, 50, 50))
    draw.text((50, y + 88), "Kindly process claim under corporate health policy.", font=font(13), fill=(90, 50, 50))
    draw.text((700, y + 88), "- Anita R., Billing Dept.", font=font(13), fill=(90, 50, 50))

    y += 115
    draw.line([30, y, 870, y], fill=(180, 180, 180), width=1)
    y += 10

    # Payment status
    draw.text((50, y + 8), "Payment Status:", font=bold_font(14), fill=(40, 40, 40))
    draw.text((230, y + 8), "UNPAID - Pending Insurance Claim", font=bold_font(14), fill=(180, 30, 30))

    draw.text((50, y + 35), "Bank Details:", font=bold_font(13), fill=(40, 40, 40))
    draw.text((50, y + 55), "A/C Name: CureMotion Physio Clinic | Bank: HDFC Bank | A/C: 00212340009871 | IFSC: HDFC0000221", font=font(12), fill=(80, 80, 80))

    y += 85
    draw.line([30, y, 870, y], fill=(150, 150, 150), width=1)

    # Footer
    draw.text((450, y + 20), "Thank you for choosing CureMotion Physiotherapy Clinic", font=font(13), fill=(100, 100, 100), anchor="mm")
    draw.text((450, y + 40), "This is a computer-generated invoice. Subject to verification.", font=font(12), fill=(140, 140, 140), anchor="mm")

    # Add slight rotation to simulate a scanned/crumpled effect
    img = img.rotate(0.8, fillcolor=(245, 242, 235), expand=False)

    img.save(path, "PNG", dpi=(150, 150))
    print(f"  [OK] {path}")


# ─────────────────────────────────────────────
# FILE 4: surgeon_estimate.jpg
# ─────────────────────────────────────────────
def create_surgeon_estimate():
    path = os.path.join(OUTPUT_DIR, "surgeon_estimate.jpg")

    width, height = 900, 780
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    def font(size):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except:
            return ImageFont.load_default()

    def bold_font(size):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except:
            return ImageFont.load_default()

    # Hospital header
    draw.rectangle([0, 0, 900, 90], fill=(30, 60, 120))
    draw.text((450, 30), "Apollo Orthopaedic & Sports Medicine Centre", font=bold_font(22), fill=(255, 255, 255), anchor="mm")
    draw.text((450, 60), "7th Floor, Apollo Hospital, Navi Mumbai - 400614 | Tel: 022-6160-1066", font=font(14), fill=(200, 215, 255), anchor="mm")

    # Title
    draw.text((450, 112), "SURGICAL PROCEDURE COST ESTIMATE", font=bold_font(20), fill=(20, 20, 20), anchor="mm")
    draw.text((450, 138), "This is a preliminary estimate only. Final billing may vary.", font=font(13), fill=(120, 120, 120), anchor="mm")
    draw.line([30, 150, 870, 150], fill=(200, 200, 200), width=1)

    # Patient details
    draw.text((50, 165), "Patient :", font=bold_font(15), fill=(40, 40, 40))
    draw.text((180, 165), "Mr. Aarav Sen", font=font(15), fill=(20, 20, 20))
    draw.text((520, 165), "Estimate No :", font=bold_font(15), fill=(40, 40, 40))
    draw.text((680, 165), "EST-2024-OS-0441", font=font(15), fill=(20, 20, 20))

    draw.text((50, 190), "Age / Sex :", font=bold_font(15), fill=(40, 40, 40))
    draw.text((180, 190), "34 Years / Male", font=font(15), fill=(20, 20, 20))
    draw.text((520, 190), "Date :", font=bold_font(15), fill=(40, 40, 40))
    draw.text((680, 190), "20-May-2024", font=font(15), fill=(20, 20, 20))

    draw.text((50, 215), "Surgeon :", font=bold_font(15), fill=(40, 40, 40))
    draw.text((180, 215), "Dr. Kiran Rao, MS Ortho, Fellowship Sports Med.", font=font(15), fill=(20, 20, 20))

    draw.text((50, 240), "Diagnosis :", font=bold_font(15), fill=(40, 40, 40))
    draw.text((180, 240), "Complete ACL Tear + Medial Meniscus Tear, Right Knee", font=font(15), fill=(20, 20, 20))

    draw.text((50, 265), "Procedure :", font=bold_font(15), fill=(40, 40, 40))
    draw.text((180, 265), "Right Knee Arthroscopic Surgery (ACL Reconstruction + Meniscectomy)", font=font(14), fill=(20, 20, 20))

    draw.line([30, 285, 870, 285], fill=(200, 200, 200), width=1)

    # Table header
    draw.rectangle([30, 290, 870, 325], fill=(30, 60, 120))
    draw.text((60, 307), "CPT Code", font=bold_font(14), fill=(255, 255, 255), anchor="lm")
    draw.text((195, 307), "Procedure Description", font=bold_font(14), fill=(255, 255, 255), anchor="lm")
    draw.text((660, 307), "ICD-10", font=bold_font(14), fill=(255, 255, 255), anchor="lm")
    draw.text((850, 307), "Amount (Rs.)", font=bold_font(14), fill=(255, 255, 255), anchor="rm")

    # Row 1
    draw.rectangle([30, 325, 870, 380], fill=(240, 245, 255))
    draw.text((60, 352), "CPT 29888", font=bold_font(14), fill=(20, 20, 100), anchor="lm")
    draw.text((195, 340), "Arthroscopically Aided ACL Reconstruction,", font=font(13), fill=(20, 20, 20), anchor="lm")
    draw.text((195, 362), "Right Knee (Autograft - Patellar Tendon)", font=font(13), fill=(60, 60, 60), anchor="lm")
    draw.text((660, 352), "S83.511A", font=font(13), fill=(60, 60, 60), anchor="lm")
    draw.text((850, 352), "3,50,000", font=bold_font(14), fill=(20, 20, 20), anchor="rm")

    # Row 2
    draw.rectangle([30, 380, 870, 435], fill=(252, 252, 252))
    draw.text((60, 407), "CPT 29881", font=bold_font(14), fill=(20, 20, 100), anchor="lm")
    draw.text((195, 395), "Arthroscopy, Knee, Surgical; with Meniscectomy", font=font(13), fill=(20, 20, 20), anchor="lm")
    draw.text((195, 417), "(including any meniscal shaving), Medial", font=font(13), fill=(60, 60, 60), anchor="lm")
    draw.text((660, 407), "S83.211A", font=font(13), fill=(60, 60, 60), anchor="lm")
    draw.text((850, 407), "1,00,000", font=bold_font(14), fill=(20, 20, 20), anchor="rm")

    # Row 3 - Anaesthesia
    draw.rectangle([30, 435, 870, 475], fill=(240, 245, 255))
    draw.text((60, 455), "CPT 00400", font=bold_font(14), fill=(20, 20, 100), anchor="lm")
    draw.text((195, 455), "Anaesthesia for Knee Arthroscopy (General)", font=font(13), fill=(20, 20, 20), anchor="lm")
    draw.text((660, 455), "Z98.890", font=font(13), fill=(60, 60, 60), anchor="lm")
    draw.text((850, 455), "Included", font=font(13), fill=(100, 100, 100), anchor="rm")

    # Row 4 - Implants
    draw.rectangle([30, 475, 870, 515], fill=(252, 252, 252))
    draw.text((60, 495), "IMPLANTS", font=bold_font(14), fill=(20, 20, 100), anchor="lm")
    draw.text((195, 495), "ACL Graft Fixation Implants (Screws & Anchors)", font=font(13), fill=(20, 20, 20), anchor="lm")
    draw.text((850, 495), "Included", font=font(13), fill=(100, 100, 100), anchor="rm")

    draw.line([30, 515, 870, 515], fill=(180, 180, 180), width=1)

    # Totals
    draw.text((680, 535), "Surgical Procedure Total :", font=bold_font(15), fill=(40, 40, 40), anchor="rm")
    draw.text((850, 535), "Rs. 4,50,000", font=bold_font(15), fill=(20, 20, 20), anchor="rm")

    draw.text((680, 558), "Estimated Hospital Stay (2 days) :", font=font(14), fill=(80, 80, 80), anchor="rm")
    draw.text((850, 558), "Rs. 40,000", font=font(14), fill=(80, 80, 80), anchor="rm")

    draw.text((680, 580), "Physiotherapy Post-Op (Est.) :", font=font(14), fill=(80, 80, 80), anchor="rm")
    draw.text((850, 580), "Rs. 20,000", font=font(14), fill=(80, 80, 80), anchor="rm")

    draw.line([500, 598, 870, 598], fill=(100, 100, 100), width=1)
    draw.rectangle([500, 602, 870, 632], fill=(30, 60, 120))
    draw.text((680, 617), "GRAND TOTAL ESTIMATE :", font=bold_font(15), fill=(255, 255, 255), anchor="rm")
    draw.text((850, 617), "Rs. 5,10,000", font=bold_font(15), fill=(255, 220, 100), anchor="rm")

    # Note
    draw.line([30, 645, 870, 645], fill=(200, 200, 200), width=1)
    draw.text((50, 660), "Note: Pre-authorisation required from both insurers before procedure.", font=bold_font(13), fill=(160, 40, 40))
    draw.text((50, 682), "Patient has dual coverage - Insurer1 (Plan A) and Insurer2 (Plan B).", font=font(13), fill=(80, 80, 80))
    draw.text((50, 702), "This estimate is valid for 30 days from the date of issue.", font=font(13), fill=(80, 80, 80))

    # Signature area
    draw.text((150, 740), "Dr. Kiran Rao", font=bold_font(13), fill=(20, 20, 20), anchor="mm")
    draw.line([80, 730, 220, 730], fill=(100, 100, 100), width=1)
    draw.text((150, 755), "Surgeon Signature", font=font(11), fill=(120, 120, 120), anchor="mm")

    draw.text((720, 740), "Hospital Stamp & Seal", font=font(13), fill=(180, 180, 180), anchor="mm")
    draw.rectangle([620, 720, 840, 765], outline=(180, 180, 180), width=1)

    img.save(path, "JPEG", quality=88)
    print(f"  [OK] {path}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\nDuCO-Agent Mock Input Generator")
    print("=" * 40)
    print(f"Output folder: {OUTPUT_DIR}\n")

    create_user_query()
    create_mri_report()
    create_pt_invoice()
    create_surgeon_estimate()

    print("\nAll 4 mock input files generated successfully!")
    print("Place this script in: scripts/generate_mock_inputs.py")
    print("Run from project root: python scripts/generate_mock_inputs.py")
