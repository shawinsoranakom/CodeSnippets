def extract_selected_pages(src_pdf_bytes: bytes, page_indices) -> bytes:
    """
    Extract specific pages and return them as a new PDF.
    """

    selected_page_indices = sorted(set(page_indices))
    if not selected_page_indices:
        return b""

    pdf = None
    sample_docs = None
    try:
        with pdfium_guard():
            pdf = open_pdfium_document(pdfium.PdfDocument, src_pdf_bytes)
            total_page = len(pdf)
            if total_page == 0:
                logger.warning("PDF is empty, return empty document")
                return b""

            selected_page_indices = [
                page_index
                for page_index in selected_page_indices
                if 0 <= page_index < total_page
            ]
            if not selected_page_indices:
                return b""

            if selected_page_indices == list(range(total_page)):
                return src_pdf_bytes

            sample_docs = open_pdfium_document(pdfium.PdfDocument.new)
            sample_docs.import_pages(pdf, selected_page_indices)

            output_buffer = BytesIO()
            sample_docs.save(output_buffer)
            return output_buffer.getvalue()
    except Exception as e:
        logger.exception(e)
        return src_pdf_bytes
    finally:
        close_pdfium_document(pdf)
        close_pdfium_document(sample_docs)