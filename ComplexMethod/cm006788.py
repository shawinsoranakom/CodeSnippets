def extract_text_from_bytes(file_name: str, file_content: bytes) -> str:
    """Extract text from binary file content based on file extension.

    Supports PDF (via pypdf), DOCX (via python-docx), and plain text files.

    Raises:
        ValueError: If the file content is corrupted or cannot be parsed.
    """
    lower_name = file_name.lower()
    if lower_name.endswith(".pdf"):
        try:
            with BytesIO(file_content) as f, PdfReader(f) as reader:
                return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            msg = f"Failed to parse PDF file '{file_name}': {e}"
            raise ValueError(msg) from e
    if lower_name.endswith(".docx"):
        try:
            from docx import Document

            doc = Document(BytesIO(file_content))
            return "\n\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            msg = f"Failed to parse DOCX file '{file_name}': {e}"
            raise ValueError(msg) from e
    return file_content.decode("utf-8", errors="ignore")