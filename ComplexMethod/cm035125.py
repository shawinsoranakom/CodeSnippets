def sort_bbox(end2end_xywh_bboxes, no_match_end2end_indexes):
    """
    This function will group the render end2end bboxes in row.
    :param end2end_xywh_bboxes:
    :param no_match_end2end_indexes:
    :return:
    """
    groups = []
    bbox_groups = []
    for index, end2end_xywh_bbox in zip(no_match_end2end_indexes, end2end_xywh_bboxes):
        this_bbox = end2end_xywh_bbox
        if len(groups) == 0:
            groups.append([index])
            bbox_groups.append([this_bbox])
        else:
            flag = False
            for g, bg in zip(groups, bbox_groups):
                # this_bbox is belong to bg's row or not
                if is_abs_lower_than_threshold(this_bbox, bg[0]):
                    g.append(index)
                    bg.append(this_bbox)
                    flag = True
                    break
            if not flag:
                # this_bbox is not belong to bg's row, create a row.
                groups.append([index])
                bbox_groups.append([this_bbox])

    # sorted bboxes in a group
    tmp_groups, tmp_bbox_groups = [], []
    for g, bg in zip(groups, bbox_groups):
        g_sorted, bg_sorted = sort_line_bbox(g, bg)
        tmp_groups.append(g_sorted)
        tmp_bbox_groups.append(bg_sorted)

    # sorted groups, sort by coord y's value.
    sorted_groups = [None] * len(tmp_groups)
    sorted_bbox_groups = [None] * len(tmp_bbox_groups)
    ys = [bg[0][1] for bg in tmp_bbox_groups]
    sorted_ys = sorted(ys)
    for g, bg in zip(tmp_groups, tmp_bbox_groups):
        idx = sorted_ys.index(bg[0][1])
        sorted_groups[idx] = g
        sorted_bbox_groups[idx] = bg

    # flatten, get final result
    end2end_sorted_idx_list, end2end_sorted_bbox_list = flatten(
        sorted_groups, sorted_bbox_groups
    )

    return (
        end2end_sorted_idx_list,
        end2end_sorted_bbox_list,
        sorted_groups,
        sorted_bbox_groups,
    )