def min_area_rect_box(
    regions, flag=True, W=0, H=0, filtersmall=False, adjust_box=False
):
    """
    多边形外接矩形
    """
    boxes = []
    for region in regions:
        if version.parse(skimage_version) >= version.parse("0.26.0"):
            region_bbox_area = region.area_bbox
        else:
            region_bbox_area = region.bbox_area
        if region_bbox_area > H * W * 3 / 4:  # 过滤大的单元格
            continue
        rect = cv2.minAreaRect(region.coords[:, ::-1])

        box = cv2.boxPoints(rect)
        box = box.reshape((8,)).tolist()
        box = image_location_sort_box(box)
        x1, y1, x2, y2, x3, y3, x4, y4 = box
        angle, w, h, cx, cy = calculate_center_rotate_angle(box)
        # if adjustBox:
        #     x1, y1, x2, y2, x3, y3, x4, y4 = xy_rotate_box(cx, cy, w + 5, h + 5, angle=0, degree=None)
        #     x1, x4 = max(x1, 0), max(x4, 0)
        #     y1, y2 = max(y1, 0), max(y2, 0)

        # if w > 32 and h > 32 and flag:
        #     if abs(angle / np.pi * 180) < 20:
        #         if filtersmall and (w < 10 or h < 10):
        #             continue
        #         boxes.append([x1, y1, x2, y2, x3, y3, x4, y4])
        # else:
        if w * h < 0.5 * W * H:
            if filtersmall and (
                w < 15 or h < 15
            ):  # or w / h > 30 or h / w > 30): # 过滤小的单元格
                continue
            boxes.append([x1, y1, x2, y2, x3, y3, x4, y4])
    return boxes