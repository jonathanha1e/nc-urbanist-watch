import pdfplumber


def extract_pdf_text(path: str) -> str:
    """Extracts all text from a PDF, page by page, joined with blank lines."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n".join(pages)
