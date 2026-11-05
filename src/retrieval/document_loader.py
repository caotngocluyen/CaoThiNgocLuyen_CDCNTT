from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional
import pypdf

from src.utils.logger import get_logger

logger = get_logger("DocumentLoader")

@dataclass
class DocumentPage:
    document_name: str
    document_number: str
    document_type: str
    page_number: int  # 1-indexed
    source_file: str
    text: str
    char_count: int
    is_empty: bool = False
    warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PDFDocumentLoader:
    """
    Dedicated PDF loader for official legal documents.
    Extracts text page-by-page while preserving structural integrity and metadata.
    """

    def __init__(self, doc_config: Dict[str, Any]):
        self.doc_config = doc_config
        self.file_path = Path(doc_config["file_path"])
        self.document_name = doc_config.get("document_name", "")
        self.document_number = doc_config.get("document_number", "")
        self.document_type = doc_config.get("document_type", "")

    def load(self) -> List[DocumentPage]:
        """
        Loads the PDF and returns a list of DocumentPage objects.
        """
        if not self.file_path.exists():
            logger.error(f"Tài liệu không tồn tại: {self.file_path}")
            raise FileNotFoundError(f"File not found: {self.file_path}")

        logger.info(f"Bắt đầu tải tài liệu: {self.document_name} ({self.file_path.name})")
        reader = pypdf.PdfReader(str(self.file_path))
        total_pages = len(reader.pages)
        pages: List[DocumentPage] = []

        empty_page_count = 0

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            try:
                raw_text = page.extract_text() or ""
            except Exception as e:
                logger.warning(f"Lỗi đọc trang {page_num} trong {self.file_path.name}: {e}")
                raw_text = ""

            char_len = len(raw_text.strip())
            is_empty = char_len < 30
            warning = None

            if is_empty:
                empty_page_count += 1
                warning = "Trang có dung lượng văn bản quá ít (<30 ký tự) hoặc trang trắng."
                logger.warning(f"Trang {page_num} ({self.file_path.name}): {warning}")

            doc_page = DocumentPage(
                document_name=self.document_name,
                document_number=self.document_number,
                document_type=self.document_type,
                page_number=page_num,
                source_file=self.file_path.name,
                text=raw_text,
                char_count=char_len,
                is_empty=is_empty,
                warning=warning
            )
            pages.append(doc_page)

        logger.info(
            f"Hoàn thành nạp {self.document_name}: Tổng số {total_pages} trang | "
            f"Trang có nội dung: {total_pages - empty_page_count} | Trang rỗng/lỗi: {empty_page_count}"
        )
        return pages
