def generate_pivot_list_curved(
    p_score,
    p_char_maps,
    f_direction,
    score_thresh=0.5,
    is_expand=True,
    is_backbone=False,
    image_id=0,
):
    """
    return center point and end point of TCL instance; filter with the char maps;
    """
    p_score = p_score[0]
    f_direction = f_direction.transpose(1, 2, 0)
    p_tcl_map = (p_score > score_thresh) * 1.0
    skeleton_map = thin(p_tcl_map)
    instance_count, instance_label_map = cv2.connectedComponents(
        skeleton_map.astype(np.uint8), connectivity=8
    )

    # get TCL Instance
    all_pos_yxs = []
    center_pos_yxs = []
    end_points_yxs = []
    instance_center_pos_yxs = []
    pred_strs = []
    if instance_count > 0:
        for instance_id in range(1, instance_count):
            pos_list = []
            ys, xs = np.where(instance_label_map == instance_id)
            pos_list = list(zip(ys, xs))

            ### FIX-ME, eliminate outlier
            if len(pos_list) < 3:
                continue

            if is_expand:
                pos_list_sorted = sort_and_expand_with_direction_v2(
                    pos_list, f_direction, p_tcl_map
                )
            else:
                pos_list_sorted, _ = sort_with_direction(pos_list, f_direction)
            all_pos_yxs.append(pos_list_sorted)

    # use decoder to filter background points.
    p_char_maps = p_char_maps.transpose([1, 2, 0])
    decode_res = ctc_decoder_for_image(
        all_pos_yxs, logits_map=p_char_maps, keep_blank_in_idxs=True
    )
    for decoded_str, keep_yxs_list in decode_res:
        if is_backbone:
            keep_yxs_list_with_id = add_id(keep_yxs_list, image_id=image_id)
            instance_center_pos_yxs.append(keep_yxs_list_with_id)
            pred_strs.append(decoded_str)
        else:
            end_points_yxs.extend((keep_yxs_list[0], keep_yxs_list[-1]))
            center_pos_yxs.extend(keep_yxs_list)

    if is_backbone:
        return pred_strs, instance_center_pos_yxs
    else:
        return center_pos_yxs, end_points_yxs