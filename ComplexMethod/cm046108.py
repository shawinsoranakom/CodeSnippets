def get_res_list_from_layout_res(layout_res, overlap_threshold=0.8):
    """Extract OCR, table and other regions from layout results."""
    ocr_res_list = []
    text_res_list = []
    table_res_list = []
    single_page_mfdetrec_res = []

    # Categorize regions
    for i, res in enumerate(layout_res):
        label = res.get("label")

        if label in ["display_formula", "inline_formula"]:
            xmin, ymin, xmax, ymax = _get_bbox(res)
            single_page_mfdetrec_res.append({
                "bbox": [xmin, ymin, xmax, ymax],
            })
        elif label == "table":
            table_res_list.append(res)
        elif label in TEXT_REGION_LABELS:
            text_res_list.append(res)

    ocr_res_list.extend(text_res_list)

    ocr_res_list, nested_text_need_remove = remove_nested_ocr_text_blocks(
        ocr_res_list,
        layout_res,
        overlap_threshold=overlap_threshold,
    )
    nested_remove_ids = {id(res) for res in nested_text_need_remove}
    if nested_remove_ids:
        layout_res[:] = [res for res in layout_res if id(res) not in nested_remove_ids]

    return ocr_res_list, table_res_list, single_page_mfdetrec_res