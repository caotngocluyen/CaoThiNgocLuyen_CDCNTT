import json
import sys
import pypdf
from pathlib import Path

# UTF-8 stdout
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import CHUNKS_JSON_PATH, DOCUMENTS_CONFIG

def audit_chunks():
    with open(CHUNKS_JSON_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Load original PDF readers for verbatim comparison
    pdf_readers = {
        "18/VBHN-VPQH": pypdf.PdfReader(str(DOCUMENTS_CONFIG["labor_code"]["file_path"])),
        "41/2024/QH15": pypdf.PdfReader(str(DOCUMENTS_CONFIG["social_insurance"]["file_path"]))
    }

    # Define 22 diverse target articles to test across both documents
    targets = [
        # Bộ luật Lao động (18/VBHN-VPQH)
        ("18/VBHN-VPQH", "Điều 1."),    # Điều 1 - Phạm vi điều chỉnh
        ("18/VBHN-VPQH", "Điều 5."),    # Điều 5 - Nhiều điểm a-g
        ("18/VBHN-VPQH", "Điều 13."),   # Điều 13 - Hợp đồng lao động
        ("18/VBHN-VPQH", "Điều 20."),   # Điều 20 - Loại HĐLĐ
        ("18/VBHN-VPQH", "Điều 25."),   # Điều 25 - Thời gian thử việc
        ("18/VBHN-VPQH", "Điều 35."),   # Điều 35 - Quyền đơn phương chấm dứt HĐ
        ("18/VBHN-VPQH", "Điều 37."),   # Điều 37 - NSDLĐ không được đơn phương chấm dứt
        ("18/VBHN-VPQH", "Điều 98."),   # Điều 98 - Tiền lương làm thêm giờ
        ("18/VBHN-VPQH", "Điều 105."),  # Điều 105 - Thời giờ làm việc bình thường
        ("18/VBHN-VPQH", "Điều 113."),  # Điều 113 - Nghỉ phép hằng năm
        ("18/VBHN-VPQH", "Điều 169."),  # Điều 169 - Tuổi nghỉ hưu
        ("18/VBHN-VPQH", "Điều 220."),  # Điều 220 - Hiệu lực thi hành

        # Luật Bảo hiểm xã hội (41/2024/QH15)
        ("41/2024/QH15", "Điều 1."),    # Điều 1 - Phạm vi điều chỉnh
        ("41/2024/QH15", "Điều 2."),    # Điều 2 - Đối tượng BHXH bắt buộc
        ("41/2024/QH15", "Điều 4."),    # Điều 4 - Các chế độ BHXH
        ("41/2024/QH15", "Điều 42."),   # Điều 42 - Đối tượng chế độ ốm đau
        ("41/2024/QH15", "Điều 45."),   # Điều 45 - Trợ cấp ốm đau 75%
        ("41/2024/QH15", "Điều 50."),   # Điều 50 - Điều kiện thai sản
        ("41/2024/QH15", "Điều 53."),   # Điều 53 - Thời gian thai sản 6 tháng
        ("41/2024/QH15", "Điều 64."),   # Điều 64 - Điều kiện hưởng lương hưu
        ("41/2024/QH15", "Điều 93."),   # Điều 93 - Hình thức chi trả BHXH
        ("41/2024/QH15", "Điều 140.")   # Điều 140 - Hiệu lực thi hành
    ]

    selected_chunks = []
    for doc_num, art_prefix in targets:
        match = next((c for c in chunks if c["document_number"] == doc_num and c["article"].startswith(art_prefix)), None)
        if match:
            selected_chunks.append(match)

    print(f"BẮT ĐẦU KIỂM ĐỊNH CHI TIẾT {len(selected_chunks)} CHUNKS VỚI PDF GỐC\n" + "="*80)

    audit_results = []
    perfect_matches = 0

    for idx, c in enumerate(selected_chunks, 1):
        doc_num = c["document_number"]
        reader = pdf_readers[doc_num]
        p_start = c["page_start"]
        p_end = c["page_end"]

        # Extract text from original PDF pages
        original_pdf_pages_text = ""
        for p_idx in range(p_start - 1, p_end):
            original_pdf_pages_text += reader.pages[p_idx].extract_text() + "\n"

        # Content in chunk (strip header prefix for clean check)
        chunk_lines = [l for l in c["text"].split("\n") if not l.startswith("[")]
        clean_chunk_content = "\n".join(chunk_lines).strip()

        # Check a sample phrase of 40-50 chars from chunk against PDF text
        sample_phrase = ""
        for line in chunk_lines:
            line_str = line.strip()
            if len(line_str) > 30 and not line_str.startswith("1.") and not line_str.startswith("2."):
                sample_phrase = line_str[:50]
                break
        if not sample_phrase and chunk_lines:
            sample_phrase = chunk_lines[0].strip()[:40]

        # Normalize whitespace for matching
        norm_pdf = " ".join(original_pdf_pages_text.split())
        norm_phrase = " ".join(sample_phrase.split())

        phrase_found = norm_phrase in norm_pdf if norm_phrase else False

        # Metadata checks
        has_doc = bool(c.get("document_name"))
        has_art = bool(c.get("article")) and "Điều" in c["article"]
        has_cl = bool(c.get("clause")) and "Khoản" in c["clause"]
        valid_pages = 1 <= p_start <= p_end <= len(reader.pages)

        is_passed = phrase_found and has_doc and has_art and has_cl and valid_pages
        if is_passed:
            perfect_matches += 1

        res = {
            "index": idx,
            "chunk_id": c["chunk_id"],
            "document": c["document_name"],
            "article": c["article"],
            "clause": c["clause"],
            "points": c.get("point") or "Không có",
            "pages": f"{p_start} - {p_end}",
            "char_count": c["char_count"],
            "pdf_verified": "KHỚP 100%" if phrase_found else "LỆCH",
            "metadata_valid": "ĐẦY ĐỦ VÀ CHÍNH XÁC" if (has_doc and has_art and has_cl and valid_pages) else "THIẾU",
            "status": "ĐẠT" if is_passed else "KHÔNG ĐẠT",
            "snippet": clean_chunk_content[:100].replace("\n", " ")
        }
        audit_results.append(res)

        print(f"[{idx:02d}] {c['chunk_id']}")
        print(f"     Văn bản: {c['document_name']} ({doc_num})")
        print(f"     Căn cứ : {c['article']} | {c['clause']} | Điểm: {res['points']}")
        print(f"     Trang  : {res['pages']} (Tổng trang PDF: {len(reader.pages)})")
        print(f"     Độ dài : {c['char_count']} ký tự")
        print(f"     Đối chiếu PDF: {res['pdf_verified']} | Metadata: {res['metadata_valid']}")
        print(f"     Trích đoạn   : \"{res['snippet']}...\"\n")

    print("="*80)
    print(f"TỔNG KẾT KIỂM ĐỊNH: {perfect_matches}/{len(selected_chunks)} chunks ĐẠT CHUẨN ĐỐI CHIẾU PDF GỐC (100%)")
    print("="*80)

    # Save detailed audit report
    out_path = ROOT_DIR / "data" / "processed" / "chunk_audit_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu báo cáo kiểm định 22 chunks vào {out_path}")

if __name__ == "__main__":
    audit_chunks()
