import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
chunks = json.load(open(ROOT_DIR / "data" / "processed" / "legal_chunks.json", encoding="utf-8"))

questions = [
    {
        "id": "Q1",
        "query": "Hợp đồng lao động có những loại nào?",
        "article": "Điều 20.",
        "keywords": ["loại hợp đồng", "không xác định", "xác định thời hạn"]
    },
    {
        "id": "Q2",
        "query": "Thời gian thử việc tối đa đối với công việc có trình độ cao đẳng trở lên là bao lâu?",
        "article": "Điều 25.",
        "keywords": ["trình độ cao đẳng", "60 ngày", "30 ngày"]
    },
    {
        "id": "Q3",
        "query": "Người lao động được nghỉ phép hàng năm bao nhiêu ngày trong điều kiện bình thường?",
        "article": "Điều 113.",
        "keywords": ["12 ngày làm việc", "nghỉ hằng năm"]
    },
    {
        "id": "Q4",
        "query": "Thời giờ làm việc bình thường không quá bao nhiêu giờ trong một ngày và một tuần?",
        "article": "Điều 105.",
        "keywords": ["08 giờ", "8 giờ", "48 giờ"]
    },
    {
        "id": "Q5",
        "query": "Làm thêm giờ vào ngày nghỉ hàng tuần được trả lương tính như thế nào?",
        "article": "Điều 98.",
        "keywords": ["200%", "ngày nghỉ hằng tuần"]
    },
    {
        "id": "Q6",
        "query": "Người sử dụng lao động có phải trả lương khi người lao động phải ngừng việc do lỗi của người sử dụng lao động không?",
        "article": "Điều 99.",
        "keywords": ["lỗi của người sử dụng lao động", "trả đủ tiền lương"]
    },
    {
        "id": "Q7",
        "query": "Người lao động có quyền đơn phương chấm dứt hợp đồng lao động không cần báo trước trong những trường hợp nào?",
        "article": "Điều 35.",
        "keywords": ["không cần báo trước"]
    },
    {
        "id": "Q8",
        "query": "Trường hợp nào người sử dụng lao động không được thực hiện quyền đơn phương chấm dứt hợp đồng lao động?",
        "article": "Điều 37.",
        "keywords": ["không được thực hiện quyền đơn phương", "nghỉ việc", "điều trị"]
    },
    {
        "id": "Q9",
        "query": "Trách nhiệm của người sử dụng lao động khi chấm dứt hợp đồng lao động gồm những gì?",
        "article": "Điều 48.",
        "keywords": ["thanh toán", "sổ bảo hiểm"]
    },
    {
        "id": "Q10",
        "query": "Những đối tượng người lao động nào thuộc diện tham gia bảo hiểm xã hội bắt buộc?",
        "article": "Điều 2.",
        "keywords": ["bảo hiểm xã hội bắt buộc", "người làm việc theo hợp đồng"]
    },
    {
        "id": "Q11",
        "query": "Điều kiện hưởng chế độ thai sản khi sinh con đối với lao động nữ là gì?",
        "article": "Điều 50.",
        "keywords": ["đóng bảo hiểm xã hội từ đủ 06 tháng", "sinh con"]
    },
    {
        "id": "Q12",
        "query": "Thời gian nghỉ việc hưởng chế độ thai sản khi sinh một con là bao nhiêu tháng?",
        "article": "Điều 53.",
        "keywords": ["06 tháng", "6 tháng"]
    },
    {
        "id": "Q13",
        "query": "Điều kiện hưởng chế độ ốm đau đối với người lao động tham gia bảo hiểm xã hội bắt buộc là gì?",
        "article": "Điều 42.",
        "keywords": ["điều trị", "ốm đau"]
    },
    {
        "id": "Q14",
        "query": "Mức hưởng chế độ ốm đau được tính bằng bao nhiêu phần trăm tiền lương đóng bảo hiểm xã hội?",
        "article": "Điều 45.",
        "keywords": ["75%", "mức hưởng"]
    },
    {
        "id": "Q15",
        "query": "Điều kiện hưởng lương hưu và tuổi nghỉ hưu của người lao động được quy định như thế nào?",
        "article": "Điều 64.",
        "keywords": ["lương hưu", "tuổi nghỉ hưu"]
    },
    {
        "id": "Q16",
        "query": "Nghỉ đẻ thì công ty có phải trả lương hay bảo hiểm xã hội chi trả?",
        "article": "Điều 168.",
        "keywords": ["chế độ bảo hiểm xã hội", "không phải trả lương"]
    }
]

print("=== PHÂN TÍCH VÀ XÁC ĐỊNH CHÍNH XÁC ĐIỀU VÀ KHOẢN CHỨA ĐÁP ÁN ===")
for item in questions:
    art = item["article"]
    matched = [c for c in chunks if art in c.get("article", "")]
    print(f"\n--- {item['id']}: {item['query']} ({art}) ---")
    exact_clauses = []
    for c in matched:
        has_kw = any(k.lower() in c["text"].lower() for k in item["keywords"])
        if has_kw:
            exact_clauses.append((c["clause"], c["chunk_id"]))
            print(f"  + PHÙ HỢP: {c['clause']} (ID: {c['chunk_id']}) -> {c['text'][:110]}...")
    if not exact_clauses:
        print("  ! Chưa tìm thấy exact clause với keyword, kiểm tra tất cả khoản:")
        for c in matched:
            print(f"    - {c['clause']} (ID: {c['chunk_id']}) -> {c['text'][:90]}...")
