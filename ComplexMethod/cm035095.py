def one_to_many(
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
        for gt_id in range(num_gt):
            # skip the following if the groundtruth was matched
            if gt_flag[0, gt_id] > 0:
                continue

            non_zero_in_sigma = np.where(local_sigma_table[gt_id, :] > 0)
            num_non_zero_in_sigma = non_zero_in_sigma[0].shape[0]

            if num_non_zero_in_sigma >= k:
                ####search for all detections that overlaps with this groundtruth
                qualified_tau_candidates = np.where(
                    (local_tau_table[gt_id, :] >= tp) & (det_flag[0, :] == 0)
                )
                num_qualified_tau_candidates = qualified_tau_candidates[0].shape[0]

                if num_qualified_tau_candidates == 1:
                    if (local_tau_table[gt_id, qualified_tau_candidates] >= tp) and (
                        local_sigma_table[gt_id, qualified_tau_candidates] >= tr
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

                        gt_flag[0, gt_id] = 1
                        det_flag[0, qualified_tau_candidates] = 1
                        # recg start
                        if rec_flag:
                            gt_str_cur = global_gt_str[idy][gt_id]
                            pred_str_cur = global_pred_str[idy][
                                qualified_tau_candidates[0].tolist()[0]
                            ]
                            if pred_str_cur == gt_str_cur:
                                hit_str_num += 1
                            else:
                                if pred_str_cur.lower() == gt_str_cur.lower():
                                    hit_str_num += 1
                        # recg end
                elif np.sum(local_sigma_table[gt_id, qualified_tau_candidates]) >= tr:
                    gt_flag[0, gt_id] = 1
                    det_flag[0, qualified_tau_candidates] = 1
                    # recg start
                    if rec_flag:
                        gt_str_cur = global_gt_str[idy][gt_id]
                        pred_str_cur = global_pred_str[idy][
                            qualified_tau_candidates[0].tolist()[0]
                        ]
                        if pred_str_cur == gt_str_cur:
                            hit_str_num += 1
                        else:
                            if pred_str_cur.lower() == gt_str_cur.lower():
                                hit_str_num += 1
                    # recg end

                    global_accumulative_recall = global_accumulative_recall + fsc_k
                    global_accumulative_precision = (
                        global_accumulative_precision
                        + num_qualified_tau_candidates * fsc_k
                    )

                    local_accumulative_recall = local_accumulative_recall + fsc_k
                    local_accumulative_precision = (
                        local_accumulative_precision
                        + num_qualified_tau_candidates * fsc_k
                    )

        return (
            local_accumulative_recall,
            local_accumulative_precision,
            global_accumulative_recall,
            global_accumulative_precision,
            gt_flag,
            det_flag,
            hit_str_num,
        )