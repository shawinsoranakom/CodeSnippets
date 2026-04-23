def one_to_one(
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
            gt_matching_qualified_sigma_candidates = np.where(
                local_sigma_table[gt_id, :] > tr
            )
            gt_matching_num_qualified_sigma_candidates = (
                gt_matching_qualified_sigma_candidates[0].shape[0]
            )
            gt_matching_qualified_tau_candidates = np.where(
                local_tau_table[gt_id, :] > tp
            )
            gt_matching_num_qualified_tau_candidates = (
                gt_matching_qualified_tau_candidates[0].shape[0]
            )

            det_matching_qualified_sigma_candidates = np.where(
                local_sigma_table[:, gt_matching_qualified_sigma_candidates[0]] > tr
            )
            det_matching_num_qualified_sigma_candidates = (
                det_matching_qualified_sigma_candidates[0].shape[0]
            )
            det_matching_qualified_tau_candidates = np.where(
                local_tau_table[:, gt_matching_qualified_tau_candidates[0]] > tp
            )
            det_matching_num_qualified_tau_candidates = (
                det_matching_qualified_tau_candidates[0].shape[0]
            )

            if (
                (gt_matching_num_qualified_sigma_candidates == 1)
                and (gt_matching_num_qualified_tau_candidates == 1)
                and (det_matching_num_qualified_sigma_candidates == 1)
                and (det_matching_num_qualified_tau_candidates == 1)
            ):
                global_accumulative_recall = global_accumulative_recall + 1.0
                global_accumulative_precision = global_accumulative_precision + 1.0
                local_accumulative_recall = local_accumulative_recall + 1.0
                local_accumulative_precision = local_accumulative_precision + 1.0

                gt_flag[0, gt_id] = 1
                matched_det_id = np.where(local_sigma_table[gt_id, :] > tr)
                # recg start
                if rec_flag:
                    gt_str_cur = global_gt_str[idy][gt_id]
                    pred_str_cur = global_pred_str[idy][matched_det_id[0].tolist()[0]]
                    if pred_str_cur == gt_str_cur:
                        hit_str_num += 1
                    else:
                        if pred_str_cur.lower() == gt_str_cur.lower():
                            hit_str_num += 1
                # recg end
                det_flag[0, matched_det_id] = 1
        return (
            local_accumulative_recall,
            local_accumulative_precision,
            global_accumulative_recall,
            global_accumulative_precision,
            gt_flag,
            det_flag,
            hit_str_num,
        )