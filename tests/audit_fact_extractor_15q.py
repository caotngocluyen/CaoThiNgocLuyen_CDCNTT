import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.agents.fact_reasoning import FactExtractor

TEST_QUERIES = [
    {
        "id": "FE_01",
        "type": "Người lao động - Đời thường - Sự việc đã xảy ra",
        "query": "Hôm qua công ty đuổi việc tôi vô cớ dù tôi đã làm ở đây được 3 năm và luôn hoàn thành nhiệm vụ.",
        "description": "NLĐ, bị sa thải đột ngột, có thâm niên 3 năm."
    },
    {
        "id": "FE_02",
        "type": "Người sử dụng lao động - Kế hoạch dự định",
        "query": "Công ty chúng tôi dự kiến sang tháng tới sẽ ký hợp đồng thử việc 60 ngày với một bạn tốt nghiệp đại học có được không?",
        "description": "NSDLĐ, kế hoạch thử việc tốt nghiệp ĐH 60 ngày."
    },
    {
        "id": "FE_03",
        "type": "Câu phủ định - Quyền nghỉ việc",
        "query": "Tôi không muốn tiếp tục làm việc nữa nhưng không báo trước cho sếp thì có bị phạt tiền hay bồi thường không?",
        "description": "Nghỉ việc không báo trước, chế tài bồi thường."
    },
    {
        "id": "FE_04",
        "type": "Nhiều điều kiện phức tạp",
        "query": "Tôi là lao động nữ, làm việc trong hầm lò nặng nhọc được 12 tháng, đang mang thai tháng thứ 4 thì có được giảm giờ làm hoặc chuyển việc nhẹ hơn không?",
        "description": "Lao động nữ, hầm lò, 12 tháng, mang thai tháng thứ 4."
    },
    {
        "id": "FE_05",
        "type": "Nhiều vấn đề pháp lý gộp (Multi-issue)",
        "query": "Hết thời gian thử việc công ty không thông báo kết quả, vậy tôi có được tự động nhận chính thức không và mức lương trong thời gian thử việc phải trả ít nhất bao nhiêu %?",
        "description": "Vừa hỏi hệ quả hết thử việc, vừa hỏi mức lương tối thiểu trong thử việc."
    },
    {
        "id": "FE_06",
        "type": "Thiếu dữ kiện trọng yếu",
        "query": "Tôi bị ốm nghỉ 3 ngày thì có được hưởng bảo hiểm xã hội chi trả tiền chế độ ốm đau không?",
        "description": "Hỏi ốm đau nhưng thiếu thông tin có giấy xác nhận khám bệnh/điều trị của cơ sở y tế hay không."
    },
    {
        "id": "FE_07",
        "type": "Thông tin thừa / nhiễu đời thường",
        "query": "Dạo này công ty làm ăn khó khăn, sếp hay cáu gắt và vợ tôi vừa sinh em bé thứ hai được 2 tuần, tôi muốn hỏi tôi là nam thì được nghỉ mấy ngày để chăm vợ con?",
        "description": "Chứa nhiều chuyện bên lề (công ty khó khăn, sếp cáu gắt), ý chính là chế độ thai sản cho lao động nam khi vợ sinh."
    },
    {
        "id": "FE_08",
        "type": "Ngôn ngữ quy phạm pháp lý chặt chẽ",
        "query": "Trường hợp người sử dụng lao động đơn phương chấm dứt hợp đồng lao động trái pháp luật thì nghĩa vụ bồi thường và nhận người lao động trở lại làm việc được thực hiện như thế nào?",
        "description": "Thuật ngữ pháp lý thuần túy (đơn phương trái pháp luật, nghĩa vụ bồi thường)."
    },
    {
        "id": "FE_09",
        "type": "Thời giờ làm việc & làm thêm",
        "query": "Sếp bắt tôi làm việc 12 tiếng một ngày liên tục trong 2 tuần thì có vi phạm luật lao động không?",
        "description": "Số giờ làm việc 12h/ngày, 2 tuần liên tục."
    },
    {
        "id": "FE_10",
        "type": "Thử việc và BHXH",
        "query": "Hợp đồng thử việc 2 tháng có phải đóng bảo hiểm xã hội bắt buộc không?",
        "description": "Phân định hợp đồng thử việc riêng với thỏa thuận thử việc trong HĐLĐ."
    },
    {
        "id": "FE_11",
        "type": "Chế độ thai sản nữ",
        "query": "Tôi đóng bảo hiểm xã hội được 5 tháng thì sinh con, vậy tôi có đủ điều kiện hưởng chế độ thai sản không?",
        "description": "Thời gian đóng 5 tháng trước khi sinh (thiếu so với mốc 6 tháng)."
    },
    {
        "id": "FE_12",
        "type": "Ốm đau dài ngày",
        "query": "Người lao động mắc bệnh thuộc danh mục chữa trị dài ngày thì thời gian nghỉ hưởng chế độ ốm đau tối đa trong một năm là bao nhiêu ngày?",
        "description": "Bệnh dài ngày, thời gian tối đa."
    },
    {
        "id": "FE_13",
        "type": "Lương hưu và tuổi nghỉ hưu",
        "query": "Tôi là nam sinh năm 1968, đóng bảo hiểm xã hội được 18 năm thì đến năm 2026 đã đủ điều kiện nhận lương hưu hàng tháng chưa?",
        "description": "Nam, sinh năm 1968, 18 năm BHXH, mốc năm 2026."
    },
    {
        "id": "FE_14",
        "type": "Trợ cấp thôi việc vs Thất nghiệp",
        "query": "Tôi tự làm đơn xin nghỉ việc và đã báo trước 45 ngày theo đúng hợp đồng thì công ty có phải trả trợ cấp thôi việc và trợ cấp mất việc cho tôi không?",
        "description": "Nghỉ việc đúng luật báo trước 45 ngày, hỏi trợ cấp thôi việc/mất việc."
    },
    {
        "id": "FE_15",
        "type": "Hiệu lực luật tương lai",
        "query": "Theo Luật Bảo hiểm xã hội 2024 mới nhất, từ ngày 01/7/2025 điều kiện hưởng lương hưu có gì thay đổi so với luật cũ?",
        "description": "Mốc thời gian tương lai 01/07/2025, so sánh Luật BHXH 2024."
    }
]

def evaluate_fact_extractor():
    print("=" * 100)
    print("KIỂM TRA CHUYÊN SÂU FACTEXTRACTOR TRÊN 15 CÂU HỎI TIẾNG VIỆT ĐA DẠNG NGỮ CẢNH")
    print("=" * 100)

    results = []
    for item in TEST_QUERIES:
        qid = item["id"]
        qtype = item["type"]
        q = item["query"]
        desc = item["description"]

        profile = FactExtractor.extract(q)

        row = {
            "id": qid,
            "type": qtype,
            "query": q,
            "description": desc,
            "extracted_subjects": profile.subjects,
            "extracted_actions": profile.actions,
            "extracted_numbers": profile.numbers_and_durations,
            "identified_issues": profile.legal_issues,
            "detected_missing_facts": profile.missing_facts,
            "temporal_clues": profile.temporal_clues
        }
        results.append(row)

        print(f"\n[{qid}] {qtype}")
        print(f"Câu hỏi: \"{q}\"")
        print(f"  + Chủ thể:       {profile.subjects}")
        print(f"  + Hành động:     {profile.actions}")
        print(f"  + Dữ kiện số:    {profile.numbers_and_durations}")
        print(f"  + Vấn đề pháp lý: {profile.legal_issues}")
        print(f"  + Dữ kiện thiếu: {profile.missing_facts}")
        print(f"  + Yếu tố thời gian: {profile.temporal_clues}")

    out_file = ROOT_DIR / "reports" / "audit_phase4_3_fact_extractor_15q.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n=> Đã lưu kết quả đánh giá FactExtractor vào: {out_file}")

if __name__ == "__main__":
    evaluate_fact_extractor()
