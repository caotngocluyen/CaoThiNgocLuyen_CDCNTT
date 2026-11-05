# tests/generate_retrieval_traceability_table.py
"""
Generates per-question traceability table for the 16 Canonical Benchmark questions across Stage A, Stage B, and Stage C.
"""
import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

canonical_path = "data/benchmark/gold_standard_benchmark_canonical.json"
results_path = "reports/audit_3stage_retrieval.json"

with open(canonical_path, "r", encoding="utf-8") as f:
    benchmarks = json.load(f)

with open(results_path, "r", encoding="utf-8") as f:
    audit_data = json.load(f)

details = {d["id"]: d for d in audit_data["details"]}

print(f"Total Canonical Questions: {len(benchmarks)}")
print(f"Total Audit Results: {len(details)}")
assert len(benchmarks) == 16, "Must be exactly 16 questions"

table_rows = []
table_rows.append("| QID | Lĩnh vực | Điều mục tiêu | Khoản mục tiêu | Stage A (Raw) | Stage B (Query Exp) | Stage C (P-C Exp) | Trạng thái giải cứu P-C |")
table_rows.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")

rescued_count = 0
direct_hit_count = 0
unreachable_count = 0

for b in benchmarks:
    qid = b["id"]
    det = details.get(qid, {})
    domain = b["domain"]
    doc = b["target_document"]
    art = b["target_article"]
    target_clauses = b["target_clauses"]

    st_a = det.get("stage_a", {})
    st_b = det.get("stage_b", {})
    st_c = det.get("stage_c", {})

    cl_a = st_a.get("clauses", [])
    cl_b = st_b.get("clauses", [])
    cl_c = st_c.get("clauses", [])

    cl_a_str = ", ".join(cl_a) if cl_a else "0 Khoản"
    cl_b_str = ", ".join(cl_b) if cl_b else "0 Khoản"
    cl_c_str = ", ".join(cl_c) if cl_c else "0 Khoản"

    if len(cl_c) > 0 and len(cl_b) == 0:
        status = "**Giải cứu thành công (+1 Hit)**"
        rescued_count += 1
    elif len(cl_c) > len(cl_b):
        status = "**Bổ sung đủ Khoản anh em**"
        rescued_count += 1
    elif len(cl_b) > 0 and len(cl_a) == 0:
        status = "Query Exp đưa vào Top-K"
        direct_hit_count += 1
    elif len(cl_a) > 0:
        status = "Trúng trực tiếp từ câu hỏi gốc"
        direct_hit_count += 1
    else:
        status = "Ngoài phạm vi KB số hóa"
        unreachable_count += 1

    table_rows.append(f"| **{qid}** | `{domain}` | {art} | {', '.join(target_clauses)} | {cl_a_str} | {cl_b_str} | **{cl_c_str}** | {status} |")

print("\n".join(table_rows))
print(f"\nTổng kết: Direct Hit={direct_hit_count}, Rescued via P-C={rescued_count}, Out of KB={unreachable_count}")

# Save markdown table snippet
with open("reports/retrieval_traceability_table.md", "w", encoding="utf-8") as f:
    f.write("\n".join(table_rows))
