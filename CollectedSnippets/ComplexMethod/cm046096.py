def get_text_quality_signal_pdfium(pdf_doc, page_indices):
    total_chars = 0
    null_char_count = 0
    replacement_char_count = 0
    control_char_count = 0
    private_use_char_count = 0

    for page_index in page_indices:
        page = pdf_doc[page_index]
        text_page = page.get_textpage()
        char_count = text_page.count_chars()
        total_chars += char_count

        for char_index in range(char_count):
            unicode_code = pdfium_c.FPDFText_GetUnicode(text_page, char_index)
            if unicode_code == 0:
                null_char_count += 1
            elif unicode_code == 0xFFFD:
                replacement_char_count += 1
            elif _is_disallowed_control_unicode(unicode_code):
                control_char_count += 1
            elif _PRIVATE_USE_AREA_START <= unicode_code <= _PRIVATE_USE_AREA_END:
                private_use_char_count += 1

    abnormal_chars = (
        null_char_count
        + replacement_char_count
        + control_char_count
        + private_use_char_count
    )

    abnormal_ratio = 0.0
    if total_chars > 0:
        abnormal_ratio = abnormal_chars / total_chars

    return {
        "total_chars": total_chars,
        "abnormal_ratio": abnormal_ratio,
        "null_char_count": null_char_count,
        "replacement_char_count": replacement_char_count,
        "control_char_count": control_char_count,
        "private_use_char_count": private_use_char_count,
    }