def merge_det_boxes(dt_boxes):
    """
    Merge detection boxes.

    This function takes a list of detected bounding boxes, each represented by four corner points.
    The goal is to merge these bounding boxes into larger text regions.

    Parameters:
    dt_boxes (list): A list containing multiple text detection boxes, where each box is defined by four corner points.

    Returns:
    list: A list containing the merged text regions, where each region is represented by four corner points.
    """
    # Convert the detection boxes into a dictionary format with bounding boxes and type
    dt_boxes_dict_list = []
    angle_boxes_list = []
    for text_box in dt_boxes:
        text_bbox = points_to_bbox(text_box)

        if calculate_is_angle(text_box):
            angle_boxes_list.append(text_box)
            continue

        text_box_dict = {'bbox': text_bbox}
        dt_boxes_dict_list.append(text_box_dict)

    # Merge adjacent text regions into lines
    lines = merge_spans_to_line(dt_boxes_dict_list)

    # Initialize a new list for storing the merged text regions
    new_dt_boxes = []
    for line in lines:
        line_bbox_list = []
        for span in line:
            line_bbox_list.append(span['bbox'])

        # 计算整行的宽度和高度
        min_x = min(bbox[0] for bbox in line_bbox_list)
        max_x = max(bbox[2] for bbox in line_bbox_list)
        min_y = min(bbox[1] for bbox in line_bbox_list)
        max_y = max(bbox[3] for bbox in line_bbox_list)
        line_width = max_x - min_x
        line_height = max_y - min_y

        # 只有当行宽度超过高度4倍时才进行合并
        if line_width > line_height * LINE_WIDTH_TO_HEIGHT_RATIO_THRESHOLD:

            # Merge overlapping text regions within the same line
            merged_spans = merge_overlapping_spans(line_bbox_list)

            # Convert the merged text regions back to point format and add them to the new detection box list
            for span in merged_spans:
                new_dt_boxes.append(bbox_to_points(span))
        else:
            # 不进行合并，直接添加原始区域
            for bbox in line_bbox_list:
                new_dt_boxes.append(bbox_to_points(bbox))

    new_dt_boxes.extend(angle_boxes_list)

    return new_dt_boxes