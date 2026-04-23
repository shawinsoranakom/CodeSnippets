def generate_pivot_list_horizontal(
    p_score, p_char_maps, f_direction, score_thresh=0.5, is_backbone=False, image_id=0
):
    """
    return center point and end point of TCL instance; filter with the char maps;
    """
    p_score = p_score[0]
    f_direction = f_direction.transpose(1, 2, 0)
    p_tcl_map_bi = (p_score > score_thresh) * 1.0
    instance_count, instance_label_map = cv2.connectedComponents(
        p_tcl_map_bi.astype(np.uint8), connectivity=8
    )

    # get TCL Instance
    all_pos_yxs = []
    center_pos_yxs = []
    end_points_yxs = []
    instance_center_pos_yxs = []

    if instance_count > 0:
        for instance_id in range(1, instance_count):
            pos_list = []
            ys, xs = np.where(instance_label_map == instance_id)
            pos_list = list(zip(ys, xs))

            ### FIX-ME, eliminate outlier
            if len(pos_list) < 5:
                continue

            # add rule here
            main_direction = extract_main_direction(pos_list, f_direction)  # y x
            reference_directin = np.array([0, 1]).reshape([-1, 2])  # y x
            is_h_angle = abs(np.sum(main_direction * reference_directin)) < math.cos(
                math.pi / 180 * 70
            )

            point_yxs = np.array(pos_list)
            max_y, max_x = np.max(point_yxs, axis=0)
            min_y, min_x = np.min(point_yxs, axis=0)
            is_h_len = (max_y - min_y) < 1.5 * (max_x - min_x)

            pos_list_final = []
            if is_h_len:
                xs = np.unique(xs)
                for x in xs:
                    ys = instance_label_map[:, x].copy().reshape((-1,))
                    y = int(np.where(ys == instance_id)[0].mean())
                    pos_list_final.append((y, x))
            else:
                ys = np.unique(ys)
                for y in ys:
                    xs = instance_label_map[y, :].copy().reshape((-1,))
                    x = int(np.where(xs == instance_id)[0].mean())
                    pos_list_final.append((y, x))

            pos_list_sorted, _ = sort_with_direction(pos_list_final, f_direction)
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
        else:
            end_points_yxs.extend((keep_yxs_list[0], keep_yxs_list[-1]))
            center_pos_yxs.extend(keep_yxs_list)

    if is_backbone:
        return instance_center_pos_yxs
    else:
        return center_pos_yxs, end_points_yxs