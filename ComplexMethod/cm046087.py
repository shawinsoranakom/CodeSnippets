def fill_char_in_spans(spans, all_chars, median_span_height):
    # 简单从上到下排一下序
    spans = sorted(spans, key=lambda x: x['bbox'][1])

    grid_size = median_span_height
    grid = collections.defaultdict(list)
    for i, span in enumerate(spans):
        start_cell = int(span['bbox'][1] / grid_size)
        end_cell = int(span['bbox'][3] / grid_size)
        for cell_idx in range(start_cell, end_cell + 1):
            grid[cell_idx].append(i)

    for char in all_chars:
        char_center_y = (char['bbox'][1] + char['bbox'][3]) / 2
        cell_idx = int(char_center_y / grid_size)

        candidate_span_indices = grid.get(cell_idx, [])

        for span_idx in candidate_span_indices:
            span = spans[span_idx]
            if calculate_char_in_span(char['bbox'], span['bbox'], char['char']):
                span['chars'].append(char)
                break

    need_ocr_spans = []
    for span in spans:
        chars_to_content(span)
        # 有的span中虽然没有字但有一两个空的占位符，用宽高和content长度过滤
        if len(span['content']) * span['height'] < span['width'] * 0.5:
            # logger.info(f"maybe empty span: {len(span['content'])}, {span['height']}, {span['width']}")
            need_ocr_spans.append(span)
        del span['height'], span['width']
    return need_ocr_spans