def txt_spans_extract(pdf_page, spans, pil_img, scale, all_bboxes, all_discarded_blocks):
    page_char_count = None
    try:
        page_char_count = pdf_page.get_textpage().count_chars()
    except Exception as exc:
        logger.debug(f"Failed to get page char count before txt extraction: {exc}")

    if page_char_count is not None and page_char_count > MAX_NATIVE_TEXT_CHARS_PER_PAGE:
        logger.info(
            "Fallback to post-OCR in txt_spans_extract due to high char count: "
            f"count_chars={page_char_count}"
        )
        need_ocr_spans = [
            span for span in spans if span.get('type') == ContentType.TEXT
        ]
        return _prepare_post_ocr_spans(need_ocr_spans, spans, pil_img, scale)

    page_dict = get_page(pdf_page)

    page_all_chars = []
    page_all_lines = []
    for block in page_dict['blocks']:
        for line in block['lines']:
            rotation_degrees = math.degrees(line['rotation'])
            # 旋转角度不为0, 90, 180, 270的行，直接跳过（rotation_degrees的值可能不为整数）
            if not any(abs(rotation_degrees - angle) < 0.1 for angle in [0, 90, 180, 270]):
                continue
            page_all_lines.append(line)
            for span in line['spans']:
                for char in span['chars']:
                    page_all_chars.append(char)

    # 计算所有sapn的高度的中位数
    span_height_list = []
    for span in spans:
        if span['type'] in [ContentType.TEXT]:
            span_height = span['bbox'][3] - span['bbox'][1]
            span['height'] = span_height
            span['width'] = span['bbox'][2] - span['bbox'][0]
            span_height_list.append(span_height)
    if len(span_height_list) == 0:
        return spans
    else:
        median_span_height = statistics.median(span_height_list)

    useful_spans = []
    unuseful_spans = []
    # 纵向span的两个特征：1. 高度超过多个line 2. 高宽比超过某个值
    vertical_spans = []
    for span in spans:
        if span['type'] in [ContentType.TEXT]:
            for block in all_bboxes + all_discarded_blocks:
                if block[7] in [BlockType.IMAGE_BODY, BlockType.TABLE_BODY, BlockType.INTERLINE_EQUATION]:
                    continue
                if calculate_overlap_area_in_bbox1_area_ratio(span['bbox'], block[0:4]) > 0.5:
                    if span['height'] > median_span_height * 2.3 and span['height'] > span['width'] * 2.3:
                        vertical_spans.append(span)
                    elif block in all_bboxes:
                        useful_spans.append(span)
                    else:
                        unuseful_spans.append(span)
                    break

    """垂直的span框直接用line进行填充"""
    if len(vertical_spans) > 0:
        for pdfium_line in page_all_lines:
            for span in vertical_spans:
                if calculate_overlap_area_in_bbox1_area_ratio(pdfium_line['bbox'].bbox, span['bbox']) > 0.5:
                    for pdfium_span in pdfium_line['spans']:
                        span['content'] += pdfium_span['text']
                    break

        for span in vertical_spans:
            if len(span['content']) == 0:
                spans.remove(span)

    """水平的span框先用char填充，再用ocr填充空的span框"""
    new_spans = []

    for span in useful_spans + unuseful_spans:
        if span['type'] in [ContentType.TEXT]:
            span['chars'] = []
            new_spans.append(span)

    need_ocr_spans = fill_char_in_spans(new_spans, page_all_chars, median_span_height)

    return _prepare_post_ocr_spans(need_ocr_spans, spans, pil_img, scale)