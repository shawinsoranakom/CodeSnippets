def many_to_one(
        local_sigma_table,
        local_tau_table,
        local_accumulative_recall,
        local_accumulative_precision,
        global_accumulative_recall,
        global_accumulative_precision,
        gt_flag,
        det_flag,
        idy,
        rec_flag,
    ):
        hit_str_num = 0
        for det_id in range(num_det):
            # skip the following if the detection was matched
            if det_flag[0, det_id] > 0:
                continue

            non_zero_in_tau = np.where(local_tau_table[:, det_id] > 0)
            num_non_zero_in_tau = non_zero_in_tau[0].shape[0]

            if num_non_zero_in_tau >= k:
                ####search for all detections that overlaps with this groundtruth
                qualified_sigma_candidates = np.where(
                    (local_sigma_table[:, det_id] >= tp) & (gt_flag[0, :] == 0)
                )
                num_qualified_sigma_candidates = qualified_sigma_candidates[0].shape[0]

                if num_qualified_sigma_candidates == 1:
                    if (local_tau_table[qualified_sigma_candidates, det_id] >= tp) and (
                        local_sigma_table[qualified_sigma_candidates, det_id] >= tr
                    ):
                        # became an one-to-one case
                        global_accumulative_recall = global_accumulative_recall + 1.0
                        global_accumulative_precision = (
                            global_accumulative_precision + 1.0
                        )
                        local_accumulative_recall = local_accumulative_recall + 1.0
                        local_accumulative_precision = (
                            local_accumulative_precision + 1.0
                        )

                        gt_flag[0, qualified_sigma_candidates] = 1
                        det_flag[0, det_id] = 1
                        # recg start
                        if rec_flag:
                            pred_str_cur = global_pred_str[idy][det_id]
                            gt_len = len(qualified_sigma_candidates[0])
                            for idx in range(gt_len):
                                ele_gt_id = qualified_sigma_candidates[0].tolist()[idx]
                                if ele_gt_id not in global_gt_str[idy]:
                                    continue
                                gt_str_cur = global_gt_str[idy][ele_gt_id]
                                if pred_str_cur == gt_str_cur:
                                    hit_str_num += 1
                                    break
                                else:
                                    if pred_str_cur.lower() == gt_str_cur.lower():
                                        hit_str_num += 1
                                    break
                        # recg end
                elif np.sum(local_tau_table[qualified_sigma_candidates, det_id]) >= tp:
                    det_flag[0, det_id] = 1
                    gt_flag[0, qualified_sigma_candidates] = 1
                    # recg start
                    if rec_flag:
                        pred_str_cur = global_pred_str[idy][det_id]
                        gt_len = len(qualified_sigma_candidates[0])
                        for idx in range(gt_len):
                            ele_gt_id = qualified_sigma_candidates[0].tolist()[idx]
                            if ele_gt_id not in global_gt_str[idy]:
                                continue
                            gt_str_cur = global_gt_str[idy][ele_gt_id]
                            if pred_str_cur == gt_str_cur:
                                hit_str_num += 1
                                break
                            else:
                                if pred_str_cur.lower() == gt_str_cur.lower():
                                    hit_str_num += 1
                                    break
                    # recg end

                    global_accumulative_recall = (
                        global_accumulative_recall
                        + num_qualified_sigma_candidates * fsc_k
                    )
                    global_accumulative_precision = (
                        global_accumulative_precision + fsc_k
                    )

                    local_accumulative_recall = (
                        local_accumulative_recall
                        + num_qualified_sigma_candidates * fsc_k
                    )
                    local_accumulative_precision = local_accumulative_precision + fsc_k
        return (
            local_accumulative_recall,
            local_accumulative_precision,
            global_accumulative_recall,
            global_accumulative_precision,
            gt_flag,
            det_flag,
            hit_str_num,
        )