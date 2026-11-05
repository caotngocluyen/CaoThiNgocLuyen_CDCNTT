import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from src.retrieval.document_loader import DocumentPage
from src.utils.logger import get_logger

logger = get_logger("LegalChunker")

@dataclass
class LegalChunk:
    chunk_id: str
    document_name: str
    document_number: str
    chapter: str
    article: str
    clause: str
    point: Optional[str]
    page_start: int
    page_end: int
    text: str
    char_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LegalTextChunker:
    """
    Hierarchical legal chunker for Vietnamese legal texts:
    Chương (Chapter) -> Điều (Article) -> Khoản (Clause) -> Điểm (Point)
    """

    def __init__(self, max_chunk_length: int = 1500, min_chunk_length: int = 30):
        self.max_chunk_length = max_chunk_length
        self.min_chunk_length = min_chunk_length

    def chunk_document(self, pages: List[DocumentPage]) -> Tuple[List[LegalChunk], Dict[str, Any]]:
        """
        Parses pages into structured legal chunks while maintaining full metadata.
        """
        if not pages:
            return [], {}

        doc_name = pages[0].document_name
        doc_number = pages[0].document_number
        logger.info(f"Bắt đầu chunking tài liệu: {doc_name} ({doc_number})")

        # 1. Linearize page text with page tracking
        lines_with_pages: List[Tuple[str, int]] = []
        for p in pages:
            raw_lines = p.text.split("\n")
            for line in raw_lines:
                clean_line = line.strip()
                # Filter out pure Cong Bao headers/footers or page numbers
                if re.match(r"^CÔNG BÁO/Số\s+\d+", clean_line):
                    continue
                if re.match(r"^\d+\s+CÔNG BÁO", clean_line):
                    continue
                if clean_line.isdigit() and len(clean_line) <= 4:
                    continue
                if clean_line:
                    lines_with_pages.append((clean_line, p.page_number))

        # 2. Extract Document Preamble / Introduction if any
        # 3. Hierarchy parsing
        chunks: List[LegalChunk] = []
        chunk_counter = 0

        current_chapter = "Lời nói đầu / Căn cứ ban hành"
        current_article = "Quy định mở đầu"
        current_article_num = "0"
        current_clause = "Toàn văn"
        current_clause_num = "0"

        # Buffer for current clause
        clause_lines: List[str] = []
        clause_page_start = 1
        clause_page_end = 1
        point_labels: List[str] = []

        # Statistical counters
        chapters_set = set()
        articles_set = set()
        clauses_count = 0
        points_count = 0
        pages_covered = set()

        # Sanitize document number for ID usage
        doc_tag = re.sub(r"[^\w\d]+", "_", doc_number).strip("_")

        def flush_clause():
            nonlocal clause_lines, clause_page_start, clause_page_end, point_labels, chunk_counter
            if not clause_lines:
                return

            full_clause_text = "\n".join(clause_lines).strip()
            if len(full_clause_text) < self.min_chunk_length:
                clause_lines = []
                point_labels = []
                return

            pages_covered.update(range(clause_page_start, clause_page_end + 1))
            chunk_counter += 1
            clause_id_base = f"{doc_tag}_art_{current_article_num}_cl_{current_clause_num}_{chunk_counter}"

            # Check if clause exceeds max_chunk_length
            if len(full_clause_text) <= self.max_chunk_length:
                points_str = ", ".join(point_labels) if point_labels else None
                # Create context header for search accuracy
                header = f"[{doc_name} - {current_article} - {current_clause}]"
                searchable_text = f"{header}\n{full_clause_text}"

                chunk = LegalChunk(
                    chunk_id=clause_id_base,
                    document_name=doc_name,
                    document_number=doc_number,
                    chapter=current_chapter,
                    article=current_article,
                    clause=current_clause,
                    point=points_str,
                    page_start=clause_page_start,
                    page_end=clause_page_end,
                    text=searchable_text,
                    char_count=len(searchable_text)
                )
                chunks.append(chunk)
            else:
                # Split long clause by points or paragraphs
                sub_chunks = self._split_long_clause(
                    full_clause_text,
                    doc_name,
                    doc_number,
                    current_chapter,
                    current_article,
                    current_clause,
                    clause_id_base,
                    clause_page_start,
                    clause_page_end
                )
                chunks.extend(sub_chunks)

            clause_lines = []
            point_labels = []

        idx = 0
        total_lines = len(lines_with_pages)

        while idx < total_lines:
            line, page_num = lines_with_pages[idx]

            # Detect Chapter
            chap_match = re.match(r"^Chương\s+([IVXLCDM]+)(.*)", line, re.IGNORECASE)
            if chap_match:
                chap_num = chap_match.group(1).upper()
                chap_title = chap_match.group(2).strip(" .:-\t")
                # Lookahead next line if title is on next line
                if not chap_title and idx + 1 < total_lines:
                    next_l, _ = lines_with_pages[idx + 1]
                    if not re.match(r"^Điều\s+\d+", next_l) and not re.match(r"^Mục\s+\d+", next_l):
                        chap_title = next_l.strip()
                        idx += 1
                current_chapter = f"Chương {chap_num}: {chap_title}".strip(": ")
                chapters_set.add(chap_num)
                idx += 1
                continue

            # Detect Section (Mục)
            sec_match = re.match(r"^Mục\s+(\d+)(.*)", line, re.IGNORECASE)
            if sec_match:
                # Add to chapter context
                sec_title = sec_match.group(2).strip(" .:-\t")
                if not sec_title and idx + 1 < total_lines:
                    next_l, _ = lines_with_pages[idx + 1]
                    if not re.match(r"^Điều\s+\d+", next_l):
                        sec_title = next_l.strip()
                        idx += 1
                current_chapter = f"{current_chapter} - Mục {sec_match.group(1)}: {sec_title}".strip(": ")
                idx += 1
                continue

            # Detect Article (Điều)
            art_match = re.match(r"^Điều\s+(\d+[a-z]?)\.\s*(.*)", line)
            if art_match:
                flush_clause()
                art_num = art_match.group(1)
                art_title = art_match.group(2).strip()
                if not art_title and idx + 1 < total_lines:
                    next_l, _ = lines_with_pages[idx + 1]
                    if not re.match(r"^\d+\.\s+", next_l):
                        art_title = next_l.strip()
                        idx += 1

                current_article_num = art_num
                current_article = f"Điều {art_num}. {art_title}".strip(". ")
                articles_set.add(art_num)
                current_clause_num = "1"
                current_clause = "Khoản 1"
                clause_page_start = page_num
                clause_page_end = page_num
                idx += 1
                continue

            # Detect Clause (Khoản)
            cl_match = re.match(r"^(\d+)\.\s+([A-ZÀ-Ỹa-zà-ỹ].*)", line)
            if cl_match:
                flush_clause()
                cl_num = cl_match.group(1)
                current_clause_num = cl_num
                current_clause = f"Khoản {cl_num}"
                clauses_count += 1
                clause_page_start = page_num
                clause_page_end = page_num
                clause_lines.append(line)
                idx += 1
                continue

            # Detect Point (Điểm)
            pt_match = re.match(r"^([a-zđ]\))\s+(.*)", line)
            if pt_match:
                pt_id = pt_match.group(1)
                point_labels.append(pt_id)
                points_count += 1

            # Normal line in current clause
            if not clause_lines:
                clause_page_start = page_num
            clause_page_end = max(clause_page_end, page_num)
            clause_lines.append(line)
            idx += 1

        # Flush any remaining clause
        flush_clause()

        # Quality check & stats
        stats = {
            "document_name": doc_name,
            "document_number": doc_number,
            "total_pages": len(pages),
            "total_chapters": len(chapters_set),
            "total_articles": len(articles_set),
            "total_clauses": clauses_count,
            "total_points": points_count,
            "total_chunks": len(chunks),
            "empty_chunks": sum(1 for c in chunks if not c.text.strip()),
            "missing_metadata_chunks": sum(1 for c in chunks if not c.document_name or not c.article),
            "unmapped_pages": sorted(list(set(range(1, len(pages) + 1)) - pages_covered))
        }

        logger.info(
            f"Chunking hoàn tất {doc_name}: {stats['total_chapters']} Chương | "
            f"{stats['total_articles']} Điều | {stats['total_clauses']} Khoản | "
            f"{stats['total_chunks']} chunks tạo thành."
        )
        return chunks, stats

    def _split_long_clause(
        self,
        clause_text: str,
        doc_name: str,
        doc_number: str,
        chapter: str,
        article: str,
        clause: str,
        base_id: str,
        page_start: int,
        page_end: int
    ) -> List[LegalChunk]:
        """
        Splits a clause that exceeds max_chunk_length into smaller units by Points (Điểm) or paragraphs.
        """
        sub_chunks: List[LegalChunk] = []
        lines = clause_text.split("\n")
        intro_lines: List[str] = []
        point_blocks: List[Tuple[Optional[str], List[str]]] = []
        current_point_tag: Optional[str] = None
        current_block: List[str] = []

        for line in lines:
            pt_match = re.match(r"^([a-zđ]\))\s+", line)
            if pt_match:
                if current_block:
                    point_blocks.append((current_point_tag, current_block))
                    current_block = []
                current_point_tag = pt_match.group(1)
                current_block.append(line)
            elif current_point_tag is None:
                intro_lines.append(line)
            else:
                current_block.append(line)

        if current_block:
            point_blocks.append((current_point_tag, current_block))

        intro_text = "\n".join(intro_lines).strip()

        if not point_blocks:
            # Fallback paragraph splitting
            parts = re.split(r"(?<=[.;])\s*\n", clause_text)
            curr_text = ""
            part_idx = 1
            for p in parts:
                if len(curr_text) + len(p) > self.max_chunk_length and curr_text:
                    header = f"[{doc_name} - {article} - {clause} (Phần {part_idx})]"
                    chunk_text = f"{header}\n{curr_text.strip()}"
                    sub_chunks.append(LegalChunk(
                        chunk_id=f"{base_id}_p{part_idx}",
                        document_name=doc_name,
                        document_number=doc_number,
                        chapter=chapter,
                        article=article,
                        clause=clause,
                        point=None,
                        page_start=page_start,
                        page_end=page_end,
                        text=chunk_text,
                        char_count=len(chunk_text)
                    ))
                    part_idx += 1
                    curr_text = p + "\n"
                else:
                    curr_text += p + "\n"
            if curr_text.strip():
                header = f"[{doc_name} - {article} - {clause} (Phần {part_idx})]"
                chunk_text = f"{header}\n{curr_text.strip()}"
                sub_chunks.append(LegalChunk(
                    chunk_id=f"{base_id}_p{part_idx}",
                    document_name=doc_name,
                    document_number=doc_number,
                    chapter=chapter,
                    article=article,
                    clause=clause,
                    point=None,
                    page_start=page_start,
                    page_end=page_end,
                    text=chunk_text,
                    char_count=len(chunk_text)
                ))
            return sub_chunks

        # Group points into chunks
        buffer_text = intro_text + "\n" if intro_text else ""
        buffer_pts: List[str] = []
        sub_idx = 1

        for tag, blk in point_blocks:
            blk_str = "\n".join(blk)
            if len(buffer_text) + len(blk_str) > self.max_chunk_length and buffer_text.strip():
                pts_str = ", ".join(buffer_pts) if buffer_pts else None
                header = f"[{doc_name} - {article} - {clause} - Điểm {pts_str}]" if pts_str else f"[{doc_name} - {article} - {clause}]"
                chunk_text = f"{header}\n{buffer_text.strip()}"
                sub_chunks.append(LegalChunk(
                    chunk_id=f"{base_id}_sub{sub_idx}",
                    document_name=doc_name,
                    document_number=doc_number,
                    chapter=chapter,
                    article=article,
                    clause=clause,
                    point=pts_str,
                    page_start=page_start,
                    page_end=page_end,
                    text=chunk_text,
                    char_count=len(chunk_text)
                ))
                sub_idx += 1
                buffer_text = (intro_text + " (tiếp tục):\n") if intro_text else ""
                buffer_pts = []

            buffer_text += blk_str + "\n"
            if tag:
                buffer_pts.append(tag)

        if buffer_text.strip():
            pts_str = ", ".join(buffer_pts) if buffer_pts else None
            header = f"[{doc_name} - {article} - {clause} - Điểm {pts_str}]" if pts_str else f"[{doc_name} - {article} - {clause}]"
            chunk_text = f"{header}\n{buffer_text.strip()}"
            sub_chunks.append(LegalChunk(
                chunk_id=f"{base_id}_sub{sub_idx}",
                document_name=doc_name,
                document_number=doc_number,
                chapter=chapter,
                article=article,
                clause=clause,
                point=pts_str,
                page_start=page_start,
                page_end=page_end,
                text=chunk_text,
                char_count=len(chunk_text)
            ))

        return sub_chunks
