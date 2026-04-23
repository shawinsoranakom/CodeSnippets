def gather_ocr_list_by_row(ocr_list: List[Any], threhold: float = 0.2) -> List[Any]:
    """
    :param ocr_list: [[[xmin,ymin,xmax,ymax], text]]
    :return:
    """
    threshold = 10
    for i in range(len(ocr_list)):
        if not ocr_list[i]:
            continue

        for j in range(i + 1, len(ocr_list)):
            if not ocr_list[j]:
                continue
            cur = ocr_list[i]
            next = ocr_list[j]
            cur_box = cur[0]
            next_box = next[0]
            c_idx = is_single_axis_contained(
                cur[0], next[0], axis="y", threhold=threhold
            )
            if c_idx:
                dis = max(next_box[0] - cur_box[2], 0)
                blank_str = int(dis / threshold) * " "
                cur[1] = cur[1] + blank_str + next[1]
                xmin = min(cur_box[0], next_box[0])
                xmax = max(cur_box[2], next_box[2])
                ymin = min(cur_box[1], next_box[1])
                ymax = max(cur_box[3], next_box[3])
                cur_box[0] = xmin
                cur_box[1] = ymin
                cur_box[2] = xmax
                cur_box[3] = ymax
                ocr_list[j] = None
    ocr_list = [x for x in ocr_list if x]
    return ocr_list