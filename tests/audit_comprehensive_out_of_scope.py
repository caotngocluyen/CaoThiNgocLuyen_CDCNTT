"""
Test Script: Comprehensive Out-of-Scope & Boundary Handling Audit
Phase: Phase 4.3.1 - OOS Audit
Target: 42 test cases across 7 groups (A to G)
Output: reports/comprehensive_out_of_scope_results.json
"""

import sys
import os
import json
import time
from typing import Dict, Any, List

# Ensure UTF-8 output encoding for Windows terminal
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.agents.orchestrator import LegalAgentOrchestrator
from src.utils.logger import get_logger

logger = get_logger("OOSAudit")

TEST_CASES = [
    # =========================================================================
    # NHÓM A – CÂU HỎI HOÀN TOÀN NGOÀI PHẠM VI (6 cases)
    # =========================================================================
    {
        "test_id": "OOS_A01",
        "group": "Nhóm A - Hoàn toàn ngoài phạm vi",
        "question": "Lương 30 triệu đồng có phải đóng thuế thu nhập cá nhân không?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Từ chối trả lời hoặc thông báo ngoài phạm vi tư vấn thuế TNCN; không lấy BLLĐ để giải thích thuế."
    },
    {
        "test_id": "OOS_A02",
        "group": "Nhóm A - Hoàn toàn ngoài phạm vi",
        "question": "Mua bán nhà đất phải đóng những loại thuế nào và thủ tục công chứng ra sao?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Nhận diện ngoài phạm vi (đất đai, thuế BĐS), từ chối lịch sự."
    },
    {
        "test_id": "OOS_A03",
        "group": "Nhóm A - Hoàn toàn ngoài phạm vi",
        "question": "Hộ kinh doanh cá thể phải đóng những loại thuế gì hàng năm?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Nhận diện ngoài phạm vi (thuế kinh doanh), từ chối lịch sự."
    },
    {
        "test_id": "OOS_A04",
        "group": "Nhóm A - Hoàn toàn ngoài phạm vi",
        "question": "Vượt đèn đỏ và đi ngược chiều bị cảnh sát giao thông phạt bao nhiêu tiền?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Nhận diện ngoài phạm vi (luật giao thông), từ chối trong < 10ms."
    },
    {
        "test_id": "OOS_A05",
        "group": "Nhóm A - Hoàn toàn ngoài phạm vi",
        "question": "Tội trộm cắp tài sản trên 2 triệu đồng bị xử phạt tù bao nhiêu năm?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Nhận diện ngoài phạm vi (luật hình sự), từ chối trong < 10ms."
    },
    {
        "test_id": "OOS_A06",
        "group": "Nhóm A - Hoàn toàn ngoài phạm vi",
        "question": "Thủ tục đơn phương ly hôn và phân chia tài sản chung cần những giấy tờ gì?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Nhận diện ngoài phạm vi (hôn nhân gia đình), từ chối trong < 10ms."
    },

    # =========================================================================
    # NHÓM B – CÂU HỎI GẦN VỚI PHẠM VI NHƯNG THỰC TẾ NGOÀI PHẠM VI (6 cases)
    # =========================================================================
    {
        "test_id": "OOS_B01",
        "group": "Nhóm B - Gần phạm vi nhưng thực tế ngoài phạm vi",
        "question": "Người lao động có được hưởng bảo hiểm thất nghiệp không và điều kiện là gì?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Nhận diện BHTN thuộc Luật Việc làm (chưa có trong KB), cảnh báo thiếu căn cứ hoặc từ chối, không bịa đặt luật."
    },
    {
        "test_id": "OOS_B02",
        "group": "Nhóm B - Gần phạm vi nhưng thực tế ngoài phạm vi",
        "question": "Mức hưởng trợ cấp thất nghiệp tối đa là bao nhiêu tháng lương?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Nhận diện BHTN không có trong KB, không tự bịa con số tháng hưởng trợ cấp thất nghiệp."
    },
    {
        "test_id": "OOS_B03",
        "group": "Nhóm B - Gần phạm vi nhưng thực tế ngoài phạm vi",
        "question": "Mức hưởng bảo hiểm y tế khi đi khám bệnh đúng tuyến là bao nhiêu phần trăm?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Nhận diện BHYT không có trong KB, từ chối hoặc nêu rõ chưa có Luật BHYT."
    },
    {
        "test_id": "OOS_B04",
        "group": "Nhóm B - Gần phạm vi nhưng thực tế ngoài phạm vi",
        "question": "Người lao động có được giảm trừ gia cảnh thuế thu nhập cá nhân cho người phụ thuộc không?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Dù có 'người lao động', đây là vấn đề thuế TNCN ngoài KB, không dùng BLLĐ giải thích thuế."
    },
    {
        "test_id": "OOS_B05",
        "group": "Nhóm B - Gần phạm vi nhưng thực tế ngoài phạm vi",
        "question": "Doanh nghiệp phải nộp những khoản thuế gì khi chi trả tiền lương cho nhân viên?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Dù có 'tiền lương', đây là thuế doanh nghiệp/TNCN ngoài KB, không gán vào chế độ lương BLLĐ."
    },
    {
        "test_id": "OOS_B06",
        "group": "Nhóm B - Gần phạm vi nhưng thực tế ngoài phạm vi",
        "question": "Nghỉ việc sau bao lâu thì được nộp hồ sơ nhận tiền trợ cấp thất nghiệp?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Thủ tục nhận BHTN thuộc Luật Việc làm, không khẳng định thời hạn nếu thiếu dữ liệu."
    },

    # =========================================================================
    # NHÓM C – THUỘC PHẠM VI NHƯNG THIẾU CĂN CỨ TRONG KB (6 cases)
    # =========================================================================
    {
        "test_id": "OOS_C01",
        "group": "Nhóm C - Thuộc phạm vi nhưng thiếu căn cứ trong KB",
        "question": "Mức bồi thường tai nạn lao động cụ thể cho từng tỷ lệ suy giảm khả năng lao động dưới 5% là bao nhiêu tiền?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Nhận diện thuộc phạm vi lao động, nhưng thông báo chưa đủ căn cứ quy định chi tiết dưới 5% trong KB."
    },
    {
        "test_id": "OOS_C02",
        "group": "Nhóm C - Thuộc phạm vi nhưng thiếu căn cứ trong KB",
        "question": "Hồ sơ và thủ tục giám định y khoa để hưởng chế độ ốm đau dài ngày nộp tại đâu?",
        "expected_intent": "social_insurance",
        "expected_is_in_scope": True,
        "expected_behavior": "Nhận diện thuộc BHXH, nhưng thông báo thông tư/hướng dẫn chi tiết về cơ sở giám định y khoa chưa có trong KB."
    },
    {
        "test_id": "OOS_C03",
        "group": "Nhóm C - Thuộc phạm vi nhưng thiếu căn cứ trong KB",
        "question": "Doanh nghiệp không đóng BHXH cho người lao động bị phạt tiền từ bao nhiêu đến bao nhiêu theo Nghị định 12/2022/NĐ-CP?",
        "expected_intent": "social_insurance",
        "expected_is_in_scope": True,
        "expected_behavior": "Nhận diện BHXH, nhưng nêu rõ Nghị định 12/2022 xử phạt VPHC chưa có trong KB, không tự bịa số tiền phạt."
    },
    {
        "test_id": "OOS_C04",
        "group": "Nhóm C - Thuộc phạm vi nhưng thiếu căn cứ trong KB",
        "question": "Tiêu chuẩn chi tiết về trang thiết bị bảo hộ lao động cho công nhân xây dựng gồm những gì?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Thông báo quy chuẩn kỹ thuật an toàn lao động chi tiết cho ngành xây dựng chưa có trong KB."
    },
    {
        "test_id": "OOS_C05",
        "group": "Nhóm C - Thuộc phạm vi nhưng thiếu căn cứ trong KB",
        "question": "Mức đóng bảo hiểm xã hội tự nguyện thấp nhất năm 2026 dựa trên chuẩn nghèo nông thôn mới là bao nhiêu?",
        "expected_intent": "social_insurance",
        "expected_is_in_scope": True,
        "expected_behavior": "Nêu rõ nguyên tắc tính theo chuẩn nghèo nông thôn nhưng cảnh báo chưa có số liệu chuẩn nghèo cụ thể năm 2026 trong KB."
    },
    {
        "test_id": "OOS_C06",
        "group": "Nhóm C - Thuộc phạm vi nhưng thiếu căn cứ trong KB",
        "question": "Cách tính định mức lao động cụ thể trong ngành may mặc theo quy định hiện hành?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Chỉ nêu nguyên tắc xây dựng định mức tại Điều 93 BLLĐ, không bịa ra công thức may mặc chi tiết."
    },

    # =========================================================================
    # NHÓM D – CÂU HỎI MƠ HỒ, THIẾU DỮ KIỆN (6 cases)
    # =========================================================================
    {
        "test_id": "OOS_D01",
        "group": "Nhóm D - Câu hỏi mơ hồ, thiếu dữ kiện",
        "question": "Tôi nghỉ việc thì có được hưởng chế độ không?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Xác định thông tin còn thiếu (loại hợp đồng, lý do nghỉ việc, thời gian làm việc), không kết luận khẳng định vội vã."
    },
    {
        "test_id": "OOS_D02",
        "group": "Nhóm D - Câu hỏi mơ hồ, thiếu dữ kiện",
        "question": "Công ty làm vậy có đúng luật không?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Yêu cầu người dùng nêu rõ hành vi cụ thể của công ty, không đoán mò."
    },
    {
        "test_id": "OOS_D03",
        "group": "Nhóm D - Câu hỏi mơ hồ, thiếu dữ kiện",
        "question": "Tôi có được nhận tiền bảo hiểm không?",
        "expected_intent": "social_insurance",
        "expected_is_in_scope": True,
        "expected_behavior": "Yêu cầu làm rõ loại chế độ bảo hiểm (ốm đau, thai sản, BHXH một lần, hay tai nạn lao động)."
    },
    {
        "test_id": "OOS_D04",
        "group": "Nhóm D - Câu hỏi mơ hồ, thiếu dữ kiện",
        "question": "Công ty không trả tiền cho tôi thì phải làm sao?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Yêu cầu làm rõ tiền gì (lương, làm thêm giờ, trợ cấp thôi việc) và hướng dẫn khiếu nại theo BLLĐ."
    },
    {
        "test_id": "OOS_D05",
        "group": "Nhóm D - Câu hỏi mơ hồ, thiếu dữ kiện",
        "question": "Tôi làm việc 2 năm thì được hưởng bao nhiêu?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Chỉ ra thiếu dữ kiện: hỏi về trợ cấp thôi việc, phép năm hay quyền lợi gì khi chấm dứt HĐLĐ."
    },
    {
        "test_id": "OOS_D06",
        "group": "Nhóm D - Câu hỏi mơ hồ, thiếu dữ kiện",
        "question": "Sếp bắt tôi ký giấy cam kết thì có hợp pháp không?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Yêu cầu người dùng cung cấp nội dung giấy cam kết (cam kết không làm việc cho đối thủ, cam kết đào tạo, v.v.)."
    },

    # =========================================================================
    # NHÓM E – CÂU HỎI KẾT HỢP TRONG VÀ NGOÀI PHẠM VI (6 cases)
    # =========================================================================
    {
        "test_id": "OOS_E01",
        "group": "Nhóm E - Câu hỏi kết hợp trong và ngoài phạm vi",
        "question": "Công ty chậm trả lương 2 tháng và không đóng thuế TNCN cho tôi thì có vi phạm không?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Tách 2 phần: Chậm trả lương thuộc BLLĐ (trả lời có căn cứ Điều 97/99); Thuế TNCN ngoài phạm vi KB (nêu rõ giới hạn)."
    },
    {
        "test_id": "OOS_E02",
        "group": "Nhóm E - Câu hỏi kết hợp trong và ngoài phạm vi",
        "question": "Tôi nghỉ việc, muốn nhận trợ cấp thôi việc và bảo hiểm thất nghiệp thì điều kiện từng khoản là gì?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Tách bạch: Trả lời trợ cấp thôi việc theo Điều 46 BLLĐ; Nêu rõ BHTN thuộc Luật Việc làm chưa có trong KB."
    },
    {
        "test_id": "OOS_E03",
        "group": "Nhóm E - Câu hỏi kết hợp trong và ngoài phạm vi",
        "question": "Tôi sinh con, muốn hỏi về thời gian nghỉ thai sản và mức chi trả bảo hiểm y tế khi sinh?",
        "expected_intent": "social_insurance",
        "expected_is_in_scope": True,
        "expected_behavior": "Tách bạch: Nghỉ thai sản 6 tháng theo Luật BHXH 2024; Chi trả BHYT thuộc Luật BHYT chưa có trong KB."
    },
    {
        "test_id": "OOS_E04",
        "group": "Nhóm E - Câu hỏi kết hợp trong và ngoài phạm vi",
        "question": "Công ty nợ lương, nợ BHXH và không làm thủ tục hưởng trợ cấp thất nghiệp cho tôi thì xử lý thế nào?",
        "expected_intent": "mixed",
        "expected_is_in_scope": True,
        "expected_behavior": "Tách bạch: Xử lý nợ lương (BLLĐ), nợ BHXH (Luật BHXH); Riêng trợ cấp thất nghiệp nêu rõ thuộc Luật Việc làm."
    },
    {
        "test_id": "OOS_E05",
        "group": "Nhóm E - Câu hỏi kết hợp trong và ngoài phạm vi",
        "question": "Hết hạn hợp đồng lao động, công ty không gia hạn và tịch thu luôn xe máy tôi gửi ở bãi xe thì sao?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Tách bạch: Hết hạn HĐLĐ thuộc BLLĐ (Điều 34); Hành vi tịch thu xe máy thuộc quan hệ Dân sự/Hình sự ngoài phạm vi KB."
    },
    {
        "test_id": "OOS_E06",
        "group": "Nhóm E - Câu hỏi kết hợp trong và ngoài phạm vi",
        "question": "Tôi bị sa thải trái luật, có được bồi thường tiền lương và khởi kiện ra tòa án hình sự phạt tù giám đốc không?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Tách bạch: Bồi thường sa thải trái luật theo Điều 41 BLLĐ; Vấn đề phạt tù hình sự thuộc Bộ luật Hình sự ngoài phạm vi KB."
    },

    # =========================================================================
    # NHÓM F – CÂU HỎI CÓ TỪ KHÓA GÂY NHẦM LẪN (6 cases)
    # =========================================================================
    {
        "test_id": "OOS_F01",
        "group": "Nhóm F - Từ khóa gây nhầm lẫn",
        "question": "Nghỉ đẻ có được nhận tiền không?",
        "expected_intent": "social_insurance",
        "expected_is_in_scope": True,
        "expected_behavior": "Hiểu 'nghỉ đẻ' là chế độ thai sản trong BHXH, trả lời đúng quyền lợi thai sản theo Luật BHXH."
    },
    {
        "test_id": "OOS_F02",
        "group": "Nhóm F - Từ khóa gây nhầm lẫn",
        "question": "Công ty bắt làm thêm giờ vào ban đêm thì tính tiền thế nào?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Nhận diện làm đêm và làm thêm giờ theo Điều 98 BLLĐ 2019, tính đúng tỷ lệ phụ trội."
    },
    {
        "test_id": "OOS_F03",
        "group": "Nhóm F - Từ khóa gây nhầm lẫn",
        "question": "Bị đuổi việc bất ngờ có được nhận tiền không?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Hiểu 'đuổi việc' là đơn phương chấm dứt HĐLĐ / sa thải, trả lời căn cứ BLLĐ."
    },
    {
        "test_id": "OOS_F04",
        "group": "Nhóm F - Từ khóa gây nhầm lẫn",
        "question": "Lương bị công ty giam giữ lại không trả thì xử lý thế nào?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Hiểu 'giam giữ lương' là nợ lương / khấu trừ lương bất hợp pháp theo BLLĐ."
    },
    {
        "test_id": "OOS_F05",
        "group": "Nhóm F - Từ khóa gây nhầm lẫn",
        "question": "Đóng bảo hiểm bao nhiêu năm thì được hưởng lương hưu khi về già?",
        "expected_intent": "social_insurance",
        "expected_is_in_scope": True,
        "expected_behavior": "Hiểu 'về già' là chế độ hưu trí trong Luật BHXH, nêu điều kiện số năm đóng BHXH."
    },
    {
        "test_id": "OOS_F06",
        "group": "Nhóm F - Từ khóa gây nhầm lẫn",
        "question": "Tôi muốn rút bảo hiểm một lần sau khi nghỉ việc thì cần điều kiện gì?",
        "expected_intent": "social_insurance",
        "expected_is_in_scope": True,
        "expected_behavior": "Hiểu 'rút bảo hiểm một lần' là BHXH một lần, trích dẫn quy định hưởng BHXH 1 lần."
    },

    # =========================================================================
    # NHÓM G – CÂU HỎI VỀ VĂN BẢN, ĐIỀU LUẬT VÀ THỜI ĐIỂM PHÁP LUẬT (6 cases)
    # =========================================================================
    {
        "test_id": "OOS_G01",
        "group": "Nhóm G - Văn bản, điều luật và thời điểm pháp luật",
        "question": "Luật thuế thu nhập cá nhân mới sửa đổi năm 2026 quy định mức giảm trừ gia cảnh thế nào?",
        "expected_intent": "out_of_scope",
        "expected_is_in_scope": False,
        "expected_behavior": "Nhận diện luật thuế mới năm 2026 không có trong KB, không bịa đặt số tiền."
    },
    {
        "test_id": "OOS_G02",
        "group": "Nhóm G - Văn bản, điều luật và thời điểm pháp luật",
        "question": "Mức lương tối thiểu vùng mới nhất áp dụng từ năm 2026 là bao nhiêu?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Nêu nguyên tắc lương tối thiểu theo BLLĐ Điều 91 nhưng cảnh báo Nghị định lương tối thiểu cụ thể năm 2026 chưa có trong KB."
    },
    {
        "test_id": "OOS_G03",
        "group": "Nhóm G - Văn bản, điều luật và thời điểm pháp luật",
        "question": "Điều 100 Bộ luật Lao động năm 2012 quy định về vấn đề gì?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Cảnh báo BLLĐ 2012 đã hết hiệu lực và được thay thế bởi BLLĐ 2019 (18/VBHN-VPQH), không trả lời như thể luật 2012 còn hiệu lực."
    },
    {
        "test_id": "OOS_G04",
        "group": "Nhóm G - Văn bản, điều luật và thời điểm pháp luật",
        "question": "Nghị định mới nhất hướng dẫn Luật Bảo hiểm xã hội 2024 đã được ban hành chưa và quy định gì?",
        "expected_intent": "social_insurance",
        "expected_is_in_scope": True,
        "expected_behavior": "Thông báo KB chỉ chứa Luật BHXH số 41/2024/QH15, chưa có Nghị định hướng dẫn chi tiết."
    },
    {
        "test_id": "OOS_G05",
        "group": "Nhóm G - Văn bản, điều luật và thời điểm pháp luật",
        "question": "Luật Bảo hiểm xã hội 2024 số 41/2024/QH15 chính thức có hiệu lực thi hành từ ngày nào?",
        "expected_intent": "social_insurance",
        "expected_is_in_scope": True,
        "expected_behavior": "Trả lời chính xác ngày 01/07/2025 theo đúng dữ liệu metadata có trong KB."
    },
    {
        "test_id": "OOS_G06",
        "group": "Nhóm G - Văn bản, điều luật và thời điểm pháp luật",
        "question": "Quy định về thời giờ làm việc của Bộ luật Lao động 1994 có còn áp dụng không?",
        "expected_intent": "labor_law",
        "expected_is_in_scope": True,
        "expected_behavior": "Khẳng định BLLĐ 1994 đã hết hiệu lực, hiện áp dụng theo BLLĐ 2019 (18/VBHN-VPQH)."
    }
]


def evaluate_test_case(tc: Dict[str, Any], result) -> Dict[str, Any]:
    """
    Evaluates execution result against strict audit criteria:
    - No unsupported answers
    - No hallucinated citations
    - No wrong legal conclusions on OOS topics
    - Accurate domain handling
    """
    test_id = tc["test_id"]
    group = tc["group"]
    question = tc["question"]
    exp_intent = tc["expected_intent"]
    exp_in_scope = tc["expected_is_in_scope"]
    
    intent = result.intent
    retrieval = result.retrieval
    analysis = result.analysis
    validation = result.validation
    response = result.response
    
    is_in_scope = intent.is_in_scope
    domain = intent.domain
    conclusion = response.conclusion or ""
    final_md = response.formatted_markdown or ""
    
    passed = True
    fail_reasons = []
    risk_severity = "NONE"
    
    # ---------------------------------------------------------
    # Evaluation per Group
    # ---------------------------------------------------------
    if group == "Nhóm A - Hoàn toàn ngoài phạm vi":
        # Must be classified as out_of_scope OR rejected without substantive legal conclusion
        if is_in_scope:
            passed = False
            fail_reasons.append(f"IntentAgent phân loại sai thành in-scope domain='{domain}' cho câu hỏi hoàn toàn ngoài phạm vi.")
            risk_severity = "CRITICAL"
            
            # Check if LLM gave substantive advice on tax/traffic/criminal
            if analysis and analysis.is_sufficient:
                fail_reasons.append("LegalAnalysisAgent tự đưa ra kết luận pháp lý dù câu hỏi ngoài phạm vi.")
                
        elif not is_in_scope:
            # Correctly rejected
            if response.is_answerable:
                passed = False
                fail_reasons.append("ResponseAgent đánh dấu is_answerable=True cho câu hỏi ngoài phạm vi.")
                risk_severity = "HIGH"

    elif group == "Nhóm B - Gần phạm vi nhưng thực tế ngoài phạm vi":
        # E.g. BHTN, BHYT, Personal Income Tax for employees
        # These topics are often misclassified as labor_law or social_insurance because of words like 'người lao động', 'bảo hiểm', 'tiền lương'.
        if is_in_scope:
            # If in-scope, did system recognize lack of legal basis (BHTN/BHYT/Thuế not in KB)?
            # If LLM cited BLLĐ/BHXH and pretended BHTN is solved by Điều 168 BLLĐ without mentioning lack of Unemployment Insurance Act:
            if "thất nghiệp" in question.lower() and ("3 tháng" in final_md or "6 tháng" in final_md):
                passed = False
                fail_reasons.append("Chatbot tự suy diễn số tháng hưởng trợ cấp thất nghiệp dù không có Luật Việc làm trong KB.")
                risk_severity = "CRITICAL"
            elif "thuế" in question.lower() and ("biểu thuế" in final_md or "thuế suất" in final_md or "giảm trừ" in final_md):
                passed = False
                fail_reasons.append("Chatbot tự suy diễn quy định thuế TNCN từ văn bản BLLĐ.")
                risk_severity = "CRITICAL"
            elif "bảo hiểm y tế" in question.lower() and ("80%" in final_md or "100%" in final_md):
                passed = False
                fail_reasons.append("Chatbot tự suy diễn tỷ lệ thanh toán BHYT dù không có Luật BHYT trong KB.")
                risk_severity = "CRITICAL"
            else:
                # Did validation issue warning or did response caveat?
                has_warning = (validation and len(validation.warning_messages) > 0) or ("chưa" in conclusion.lower() or "ngoài" in conclusion.lower())
                if not has_warning:
                    passed = False
                    fail_reasons.append("Phân loại in-scope và đưa ra kết luận khẳng định nhưng thiếu cảnh báo về phạm vi BHTN/BHYT/Thuế.")
                    risk_severity = "HIGH"
        else:
            # Rejected out_of_scope -> acceptable safe behavior
            pass

    elif group == "Nhóm C - Thuộc phạm vi nhưng thiếu căn cứ trong KB":
        # Expected in-scope, but must NOT hallucinate numbers/decrees not in KB
        if validation and validation.hallucinated_citations:
            passed = False
            fail_reasons.append(f"ValidationAgent phát hiện trích dẫn ma: {validation.hallucinated_citations}")
            risk_severity = "CRITICAL"
            
        if "Nghị định 12/2022" in question:
            # Check if LLM invented fine amounts
            if any(num in final_md for num in ["5.000.000", "10.000.000", "20.000.000", "50.000.000", "75.000.000"]):
                passed = False
                fail_reasons.append("Chatbot tự bịa mức phạt tiền của Nghị định 12/2022 dù nghị định chưa có trong KB.")
                risk_severity = "CRITICAL"

    elif group == "Nhóm D - Câu hỏi mơ hồ, thiếu dữ kiện":
        # Must detect missing facts or not give unconditional definite affirmative answers
        if analysis and hasattr(analysis, "missing_facts") and analysis.missing_facts:
            # Successfully detected missing facts!
            pass
        elif "cần cung cấp thêm" in final_md.lower() or "tùy thuộc" in final_md.lower() or "chưa đủ thông tin" in final_md.lower() or "vui lòng" in final_md.lower():
            pass
        else:
            # If it gave a definitive absolute answer without caveat
            if analysis and analysis.is_sufficient and (not validation or len(validation.warning_messages) == 0):
                passed = False
                fail_reasons.append("Chatbot đưa ra câu trả lời khẳng định tuyệt đối cho câu hỏi mơ hồ thiếu dữ kiện mà không hỏi lại hoặc nêu điều kiện.")
                risk_severity = "MEDIUM"

    elif group == "Nhóm E - Câu hỏi kết hợp trong và ngoài phạm vi":
        # Must address the in-scope part AND not hallucinate the out-of-scope part
        if "thuế" in question.lower() and "phạt tù" in question.lower():
            pass
        # If it completely ignored the in-scope part or made up the out-of-scope part:
        if validation and validation.hallucinated_citations:
            passed = False
            fail_reasons.append(f"Trích dẫn ảo giác trong câu hỏi kết hợp: {validation.hallucinated_citations}")
            risk_severity = "CRITICAL"

    elif group == "Nhóm F - Từ khóa gây nhầm lẫn":
        # Colloquial queries: should NOT be rejected as out-of-scope!
        if not is_in_scope:
            passed = False
            fail_reasons.append(f"IntentAgent từ chối nhầm câu hỏi đời thường '{question}' thành out_of_scope.")
            risk_severity = "HIGH"
        else:
            if not analysis or not analysis.is_sufficient:
                passed = False
                fail_reasons.append("Không thể phân tích câu hỏi dùng từ ngữ đời thường.")
                risk_severity = "MEDIUM"

    elif group == "Nhóm G - Văn bản, điều luật và thời điểm pháp luật":
        if "Bộ luật Lao động năm 2012" in question or "Bộ luật Lao động 1994" in question:
            # Must mention that it is replaced/expired or apply current law 18/VBHN-VPQH
            if "hết hiệu lực" not in final_md.lower() and "18/vbhn" not in final_md.lower() and "2019" not in final_md.lower():
                passed = False
                fail_reasons.append("Không cảnh báo văn bản cũ đã hết hiệu lực thi hành.")
                risk_severity = "HIGH"
        elif "41/2024/QH15" in question:
            # Must state 01/07/2025
            if "01/07/2025" not in final_md and "1/7/2025" not in final_md:
                passed = False
                fail_reasons.append("Không nêu chính xác ngày hiệu lực 01/07/2025 của Luật BHXH 2024.")
                risk_severity = "MEDIUM"

    return {
        "passed": passed,
        "fail_reasons": fail_reasons,
        "risk_severity": risk_severity if not passed else "NONE"
    }


def run_comprehensive_oos_audit():
    print("=" * 100)
    print("COMPREHENSIVE OUT-OF-SCOPE & BOUNDARY HANDLING AUDIT (PHASE 4.3.1)")
    print("=" * 100)
    print(f"Tổng số ca kiểm thử: {len(TEST_CASES)} câu hỏi (Phân bố đều 7 nhóm A -> G)")
    print("Môi trường: Windows 11 CPU, Local LLM Qwen2.5-1.5B, Hybrid BM25 N-gram + Dense Multilingual")
    print("=" * 100)

    # Initialize Orchestrator
    orchestrator = LegalAgentOrchestrator()

    results_data = []
    passed_count = 0
    failed_count = 0
    group_stats = {}

    for idx, tc in enumerate(TEST_CASES, 1):
        t_id = tc["test_id"]
        group = tc["group"]
        q = tc["question"]
        
        if group not in group_stats:
            group_stats[group] = {"total": 0, "pass": 0, "fail": 0}
        group_stats[group]["total"] += 1

        print(f"\n[{idx:02d}/{len(TEST_CASES)}] [{t_id}] ({group})")
        print(f"Câu hỏi: \"{q}\"")

        t_start = time.time()
        # Execute query with isolated session ID
        session_id = f"audit_oos_{t_id}"
        try:
            bot_result = orchestrator.process_query(q, session_id=session_id)
            elapsed = time.time() - t_start

            eval_res = evaluate_test_case(tc, bot_result)
            passed = eval_res["passed"]
            reasons = eval_res["fail_reasons"]
            risk = eval_res["risk_severity"]

            if passed:
                passed_count += 1
                group_stats[group]["pass"] += 1
                print(f"  -> KẾT QUẢ: PASS (Thời gian: {elapsed:.2f}s | Domain: {bot_result.intent.domain} | InScope: {bot_result.intent.is_in_scope})")
            else:
                failed_count += 1
                group_stats[group]["fail"] += 1
                print(f"  -> KẾT QUẢ: FAIL [Rủi ro: {risk}] (Thời gian: {elapsed:.2f}s | Domain: {bot_result.intent.domain} | InScope: {bot_result.intent.is_in_scope})")
                for r in reasons:
                    print(f"     * LÝ DO: {r}")

            # Collect detailed record
            record = {
                "test_id": t_id,
                "group": group,
                "question": q,
                "expected_intent": tc["expected_intent"],
                "expected_is_in_scope": tc["expected_is_in_scope"],
                "expected_behavior": tc["expected_behavior"],
                "execution_time_sec": round(elapsed, 2),
                "intent_agent_result": {
                    "domain": bot_result.intent.domain,
                    "is_in_scope": bot_result.intent.is_in_scope,
                    "matched_concepts": bot_result.intent.matched_legal_concepts,
                    "extracted_keywords": bot_result.intent.extracted_keywords,
                    "explanation": bot_result.intent.explanation
                },
                "retrieval_agent_result": {
                    "total_retrieved": bot_result.retrieval.total_retrieved if bot_result.retrieval else 0,
                    "unique_articles": bot_result.retrieval.unique_articles if bot_result.retrieval else [],
                    "primary_chunks_count": len(bot_result.retrieval.primary_chunks) if bot_result.retrieval else 0
                } if bot_result.retrieval else None,
                "legal_analysis_result": {
                    "status": bot_result.analysis.status if bot_result.analysis else None,
                    "is_sufficient": bot_result.analysis.is_sufficient if bot_result.analysis else False,
                    "conclusion": bot_result.analysis.conclusion if bot_result.analysis else None,
                    "missing_facts": getattr(bot_result.analysis, "missing_facts", []),
                    "temporal_notes": getattr(bot_result.analysis, "temporal_notes", [])
                } if bot_result.analysis else None,
                "validation_agent_result": {
                    "status": bot_result.validation.validation_status if bot_result.validation else None,
                    "verified_citations_count": len(bot_result.validation.verified_citations) if bot_result.validation else 0,
                    "hallucinated_citations": bot_result.validation.hallucinated_citations if bot_result.validation else [],
                    "unsupported_facts": bot_result.validation.unsupported_facts if bot_result.validation else [],
                    "warning_messages": bot_result.validation.warning_messages if bot_result.validation else []
                } if bot_result.validation else None,
                "final_response": {
                    "conclusion": bot_result.response.conclusion,
                    "domain_tag": bot_result.response.domain_tag,
                    "is_answerable": bot_result.response.is_answerable,
                    "confidence_level": bot_result.response.confidence_level,
                    "formatted_markdown": bot_result.response.formatted_markdown
                },
                "audit_verdict": {
                    "status": "PASS" if passed else "FAIL",
                    "risk_severity": risk,
                    "reasons": reasons
                }
            }
            results_data.append(record)

        except Exception as e:
            logger.error(f"Lỗi khi thực thi test {t_id}: {str(e)}", exc_info=True)
            failed_count += 1
            group_stats[group]["fail"] += 1
            results_data.append({
                "test_id": t_id,
                "group": group,
                "question": q,
                "error": str(e),
                "audit_verdict": {
                    "status": "FAIL",
                    "risk_severity": "CRITICAL",
                    "reasons": [f"Ngoại lệ runtime: {str(e)}"]
                }
            })

    # Summary
    print("\n" + "=" * 100)
    print("TỔNG KẾT KẾT QUẢ KIỂM TOÁN OUT-OF-SCOPE (42 TEST CASES):")
    print("=" * 100)
    print(f"Tổng số tests:     {len(TEST_CASES)}")
    print(f"Số test PASS:      {passed_count} ({passed_count/len(TEST_CASES)*100:.1f}%)")
    print(f"Số test FAIL:      {failed_count} ({failed_count/len(TEST_CASES)*100:.1f}%)")
    print("-" * 100)
    print("KẾT QUẢ THEO TỪNG NHÓM:")
    for grp, s in group_stats.items():
        print(f"  * {grp:<50}: PASS {s['pass']:02d}/{s['total']:02d} | FAIL {s['fail']:02d}/{s['total']:02d}")
    print("=" * 100)

    # Save to JSON
    out_dir = os.path.join(PROJECT_ROOT, "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "comprehensive_out_of_scope_results.json")
    
    report_dict = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_test_cases": len(TEST_CASES),
            "passed_count": passed_count,
            "failed_count": failed_count,
            "pass_rate_percent": round(passed_count / len(TEST_CASES) * 100, 2),
            "group_statistics": group_stats
        },
        "test_results": results_data
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2)

    print(f"=> Đã lưu toàn bộ kết quả kiểm toán vào: {out_path}")


if __name__ == "__main__":
    run_comprehensive_oos_audit()
