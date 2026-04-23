def remove_nested_ocr_text_blocks(
    ocr_res_list,
    layout_res,
    overlap_threshold=0.8,
    min_area_ratio=1.01,
):
    """Remove OCR candidate text blocks that are contained by any larger layout block."""
    if not ocr_res_list or len(layout_res) < 2:
        return ocr_res_list, []

    layout_info = [(block, get_coords_and_area(block)) for block in layout_res]
    blocks_to_remove = []

    for text_block in ocr_res_list:
        text_box = get_coords_and_area(text_block)
        text_area = text_box[4]
        for parent_block, parent_box in layout_info:
            if parent_block is text_block:
                continue
            if parent_box[4] <= text_area * min_area_ratio:
                continue
            if is_inside(text_box, parent_box, overlap_threshold):
                blocks_to_remove.append(text_block)
                break

    remove_ids = {id(block) for block in blocks_to_remove}
    filtered_ocr_res_list = [
        block for block in ocr_res_list if id(block) not in remove_ids
    ]
    return filtered_ocr_res_list, blocks_to_remove