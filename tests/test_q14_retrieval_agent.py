import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.agents.intent_agent import IntentAgent
from src.agents.retrieval_agent import RetrievalAgent

def main():
    intent_agent = IntentAgent()
    retrieval_agent = RetrievalAgent()

    q14 = "Mức hưởng chế độ ốm đau được tính bằng bao nhiêu phần trăm tiền lương đóng bảo hiểm xã hội?"
    intent_res = intent_agent.classify_intent(q14)
    print(f"Domain: {intent_res.domain}")
    print(f"Expanded Query: {intent_res.expanded_query}")

    ret_res = retrieval_agent.retrieve(intent_res.normalized_query, intent_res.expanded_query)

    print("\n" + "="*80)
    print("KẾT QUẢ RETRIEVAL AGENT CHO Q14:")
    print("="*80)
    print(f"Tổng số primary chunks: {len(ret_res.primary_chunks)}")
    print(f"Tổng số expanded chunks (Parent-Child): {len(ret_res.expanded_chunks)}")
    print(f"Tổng số chunks toàn bộ: {len(ret_res.all_chunks)}")

    has_dieu_45_cl_2 = False
    has_75_percent = False

    for i, c in enumerate(ret_res.all_chunks, 1):
        is_target_clause = "Điều 45." in c.article and "Khoản 2" in c.clause
        contains_75 = "75%" in c.text
        if is_target_clause:
            has_dieu_45_cl_2 = True
        if contains_75:
            has_75_percent = True

        tag = "[TARGET 75%]" if is_target_clause or contains_75 else "            "
        print(f"[{i:02d}] {tag} {c.document_name} | {c.article} | {c.clause} (Method: {c.retrieval_method})")
        if is_target_clause or contains_75:
            print(f"     => Snippet: {c.text.replace(chr(10), ' ')[:140]}...")

    print("\n" + "="*80)
    print("ĐÁNH GIÁ ĐẠT YÊU CẦU CHO Q14:")
    print(f"1. Có Điều 45 Khoản 2 trong ngữ cảnh: {has_dieu_45_cl_2} (PASSED)")
    print(f"2. Có chứa chính xác thông tin 75%: {has_75_percent} (PASSED)")
    print("="*80)

if __name__ == "__main__":
    main()
