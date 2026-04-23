def blocks_to_page_info(
        page_model_list,
        image_dict,
        page,
        image_writer,
        page_index,
        _ocr_enable,
        _vlm_ocr_enable,
) -> dict:
    """将blocks转换为页面信息"""

    scale = image_dict["scale"]
    page_pil_img = image_dict["img_pil"]
    page_img_md5 = bytes_md5(page_pil_img.tobytes())
    with pdfium_guard():
        width, height = map(int, page.get_size())

    magic_model = MagicModel(
        page_model_list,
        page,
        scale,
        page_pil_img,
        width,
        height,
        _ocr_enable,
        _vlm_ocr_enable,
    )
    image_blocks = magic_model.get_image_blocks()
    table_blocks = magic_model.get_table_blocks()
    chart_blocks = magic_model.get_chart_blocks()
    title_blocks = magic_model.get_title_blocks()
    discarded_blocks = magic_model.get_discarded_blocks()
    code_blocks = magic_model.get_code_blocks()
    ref_text_blocks = magic_model.get_ref_text_blocks()
    phonetic_blocks = magic_model.get_phonetic_blocks()
    list_blocks = magic_model.get_list_blocks()

    # 如果有标题优化需求，计算标题的平均行高
    if title_aided_enable:
        if _vlm_ocr_enable:  # vlm_ocr导致没有line信息，需要重新det获取平均行高
            ocr_model = get_ch_lite_ocr_det_model()
            for title_block in title_blocks:
                ocr_det_res, _ = detect_ocr_boxes_from_padded_crop(
                    title_block.get('bbox'),
                    page_pil_img,
                    scale,
                    ocr_model=ocr_model,
                )
                if len(ocr_det_res) > 0:
                    # 计算所有res的平均高度
                    avg_height = np.mean([box[2][1] - box[0][1] for box in ocr_det_res])
                    title_block['line_avg_height'] = round(avg_height/scale)
        else:  # 有line信息，直接计算平均行高
            for title_block in title_blocks:
                lines = title_block.get('lines', [])
                if lines:
                    # 使用列表推导式和内置函数,一次性计算平均高度
                    avg_height = sum(line['bbox'][3] - line['bbox'][1] for line in lines) / len(lines)
                    title_block['line_avg_height'] = round(avg_height)
                else:
                    title_block['line_avg_height'] = title_block['bbox'][3] - title_block['bbox'][1]

    text_blocks = magic_model.get_text_blocks()
    interline_equation_blocks = magic_model.get_interline_equation_blocks()

    all_spans = magic_model.get_all_spans()
    # 对image/table/chart/interline_equation的span截图
    for span in all_spans:
        if span["type"] in [ContentType.IMAGE, ContentType.TABLE, ContentType.CHART, ContentType.INTERLINE_EQUATION]:
            span = cut_image_and_table(span, page_pil_img, page_img_md5, page_index, image_writer, scale=scale)

    replace_inline_table_images(table_blocks, image_writer, page_index)

    page_blocks = []
    page_blocks.extend([
        *image_blocks,
        *table_blocks,
        *chart_blocks,
        *code_blocks,
        *ref_text_blocks,
        *phonetic_blocks,
        *title_blocks,
        *text_blocks,
        *interline_equation_blocks,
        *list_blocks,
    ])
    # 对page_blocks根据index的值进行排序
    page_blocks.sort(key=lambda x: x["index"])

    page_info = {
        "preproc_blocks": page_blocks,
        "discarded_blocks": discarded_blocks,
        "page_size": [width, height],
        "page_idx": page_index,
    }
    if _vlm_ocr_enable:
        edge_text_line_hints = _detect_edge_text_line_hints(page_blocks, page_pil_img, scale)
        if edge_text_line_hints:
            page_info[edge_text_line_hints_key()] = edge_text_line_hints
    return page_info