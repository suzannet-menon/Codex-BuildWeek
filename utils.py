#PDF Parsing

try:
    from pymupdf import fitz  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - fallback for environments exposing the package as fitz
    import fitz  # type: ignore[import-not-found]


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from a PDF file given as bytes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += str(page.get_text())
    doc.close()
    return text.strip()