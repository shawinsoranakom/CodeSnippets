def classify_hybrid(pdf_bytes):
    """
    Fast PDF classification path.

    The hybrid path uses pdfium + pypdf as the main path and falls back to
    pdfminer only for gray-zone samples.
    """

    pdf = None
    page_indices = []
    should_run_pdfminer_fallback = False

    try:
        with pdfium_guard():
            pdf = open_pdfium_document(pdfium.PdfDocument, pdf_bytes)
            page_count = len(pdf)
            if page_count == 0:
                return "ocr"

            page_indices = get_sample_page_indices(page_count, MAX_SAMPLE_PAGES)
            if not page_indices:
                return "ocr"

            extreme_page_index, extreme_ratio = get_extreme_aspect_ratio_page_pdfium(
                pdf,
                page_indices,
            )
            if extreme_page_index is not None:
                logger.info(
                    "Classify PDF as OCR due to extreme sampled-page aspect ratio: "
                    f"page={extreme_page_index + 1}, ratio={extreme_ratio:.2f}"
                )
                return "ocr"

            if (
                get_avg_cleaned_chars_per_page_pdfium(pdf, page_indices)
                < CHARS_THRESHOLD
            ):
                return "ocr"

            if detect_cid_font_signal_pypdf(pdf_bytes, page_indices):
                return "ocr"

            text_quality_signal = get_text_quality_signal_pdfium(pdf, page_indices)
            total_chars = text_quality_signal["total_chars"]
            abnormal_ratio = text_quality_signal["abnormal_ratio"]

            if total_chars >= TEXT_QUALITY_MIN_CHARS:
                if abnormal_ratio >= TEXT_QUALITY_BAD_THRESHOLD:
                    return "ocr"
                should_run_pdfminer_fallback = abnormal_ratio > TEXT_QUALITY_GOOD_THRESHOLD
            else:
                should_run_pdfminer_fallback = True

            if (
                get_high_image_coverage_ratio_pdfium(pdf, page_indices)
                >= HIGH_IMAGE_COVERAGE_THRESHOLD
            ):
                return "ocr"

    except Exception as e:
        logger.error(f"Failed to classify PDF with hybrid strategy: {e}")
        return "ocr"

    finally:
        close_pdfium_document(pdf)

    if should_run_pdfminer_fallback:
        sample_pdf_bytes = extract_selected_pages(pdf_bytes, page_indices)
        if not sample_pdf_bytes:
            return "ocr"
        if detect_invalid_chars_pdfminer_fallback(sample_pdf_bytes):
            return "ocr"

    return "txt"