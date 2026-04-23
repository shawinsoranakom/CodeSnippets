def normalize_bbox_to_unit(item, page_width, page_height):
    """将像素级bbox归一化为[0, 1]区间"""
    bbox = item.get('bbox')
    if bbox is None or len(bbox) != 4:
        return False

    x0, y0, x1, y1 = [float(v) for v in bbox]
    if (
        0.0 <= x0 <= 1.0
        and 0.0 <= y0 <= 1.0
        and 0.0 <= x1 <= 1.0
        and 0.0 <= y1 <= 1.0
    ):
        normalized_bbox = [x0, y0, x1, y1]
    else:
        normalized_bbox = [
            x0 / page_width,
            y0 / page_height,
            x1 / page_width,
            y1 / page_height,
        ]
    item['bbox'] = [round(min(max(v, 0), 1), 3) for v in normalized_bbox]
    return True