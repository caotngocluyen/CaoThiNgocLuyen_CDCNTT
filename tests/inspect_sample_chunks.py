import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

with open("data/processed/legal_chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Tổng số chunks đã nạp: {len(chunks)}")

# 1. Beginning chunk
c1 = chunks[0]
print("\n" + "="*50)
print("1. CHUNK ĐẦU TÀI LIỆU")
print(f"ID: {c1['chunk_id']} | Trang: {c1['page_start']}-{c1['page_end']}")
print(f"Căn cứ: {c1['document_name']} | {c1['article']} | {c1['clause']}")
print("Nội dung:\n" + c1['text'][:350] + "...")

# 2. Chunk with multiple points a), b), c)
c2 = next(c for c in chunks if c.get('point') and len(c['point']) > 4)
print("\n" + "="*50)
print("2. CHUNK CÓ NHIỀU ĐIỂM a, b, c")
print(f"ID: {c2['chunk_id']} | Trang: {c2['page_start']}-{c2['page_end']}")
print(f"Căn cứ: {c2['document_name']} | {c2['article']} | {c2['clause']} | Điểm: {c2['point']}")
print("Nội dung:\n" + c2['text'][:350] + "...")

# 3. Chunk on Labor Contract (Điều 20)
c3 = next(c for c in chunks if "Điều 20" in c['article'])
print("\n" + "="*50)
print("3. CHUNK VỀ LOẠI HỢP ĐỒNG LAO ĐỘNG (Điều 20)")
print(f"ID: {c3['chunk_id']} | Trang: {c3['page_start']}-{c3['page_end']}")
print(f"Căn cứ: {c3['document_name']} | {c3['article']} | {c3['clause']}")
print("Nội dung:\n" + c3['text'][:350] + "...")

# 4. Chunk near end of Labor Code (Điều 220)
c4 = next(c for c in chunks if "Điều 220" in c['article'])
print("\n" + "="*50)
print("4. CHUNK CUỐI BỘ LUẬT LAO ĐỘNG (Điều 220)")
print(f"ID: {c4['chunk_id']} | Trang: {c4['page_start']}-{c4['page_end']}")
print(f"Căn cứ: {c4['document_name']} | {c4['article']} | {c4['clause']}")
print("Nội dung:\n" + c4['text'][:350] + "...")

# 5. Chunk Social Insurance (Chế độ thai sản)
c5 = next(c for c in chunks if "thai sản" in c['text'].lower() and "Luật Bảo hiểm xã hội" in c['document_name'])
print("\n" + "="*50)
print("5. CHUNK BẢO HIỂM XÃ HỘI (Chế độ thai sản)")
print(f"ID: {c5['chunk_id']} | Trang: {c5['page_start']}-{c5['page_end']}")
print(f"Căn cứ: {c5['document_name']} | {c5['article']} | {c5['clause']}")
print("Nội dung:\n" + c5['text'][:350] + "...")
