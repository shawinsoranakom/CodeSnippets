def reorder_multi_column_bboxes(pdf_parser, bboxes, zoom=PDF_MULTI_COLUMN_ZOOM):
    text_boxes = [
        box
        for box in bboxes
        if box.get("layout_type") == "text"
        and all(box.get(key) is not None for key in ["x0", "x1", "page_number"])
    ]
    if not text_boxes or not pdf_parser.page_images:
        return bboxes

    column_width = np.median([box["x1"] - box["x0"] for box in text_boxes])
    page_width = pdf_parser.page_images[0].size[0] / zoom
    if column_width >= page_width / 2:
        return bboxes

    return pdf_parser.sort_X_by_page(bboxes, column_width / 2)