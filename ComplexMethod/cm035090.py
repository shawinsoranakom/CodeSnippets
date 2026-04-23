def combine_results(all_data, rec_flag=True):
    tr = 0.7
    tp = 0.6
    fsc_k = 0.8
    k = 2
    global_sigma = []
    global_tau = []
    global_pred_str = []
    global_gt_str = []

    for data in all_data:
        global_sigma.append(data["sigma"])
        global_tau.append(data["global_tau"])
        global_pred_str.append(data["global_pred_str"])
        global_gt_str.append(data["global_gt_str"])

    global_accumulative_recall = 0
    global_accumulative_precision = 0
    total_num_gt = 0
    total_num_det = 0
    hit_str_count = 0
    hit_count = 0

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

    for idx in range(len(global_sigma)):
        local_sigma_table = np.array(global_sigma[idx])
        local_tau_table = global_tau[idx]

        num_gt = local_sigma_table.shape[0]
        num_det = local_sigma_table.shape[1]

        total_num_gt = total_num_gt + num_gt
        total_num_det = total_num_det + num_det

        local_accumulative_recall = 0
        local_accumulative_precision = 0
        gt_flag = np.zeros((1, num_gt))
        det_flag = np.zeros((1, num_det))

        #######first check for one-to-one case##########
        (
            local_accumulative_recall,
            local_accumulative_precision,
            global_accumulative_recall,
            global_accumulative_precision,
            gt_flag,
            det_flag,
            hit_str_num,
        ) = one_to_one(
            local_sigma_table,
            local_tau_table,
            local_accumulative_recall,
            local_accumulative_precision,
            global_accumulative_recall,
            global_accumulative_precision,
            gt_flag,
            det_flag,
            idx,
            rec_flag,
        )

        hit_str_count += hit_str_num
        #######then check for one-to-many case##########
        (
            local_accumulative_recall,
            local_accumulative_precision,
            global_accumulative_recall,
            global_accumulative_precision,
            gt_flag,
            det_flag,
            hit_str_num,
        ) = one_to_many(
            local_sigma_table,
            local_tau_table,
            local_accumulative_recall,
            local_accumulative_precision,
            global_accumulative_recall,
            global_accumulative_precision,
            gt_flag,
            det_flag,
            idx,
            rec_flag,
        )
        hit_str_count += hit_str_num
        #######then check for many-to-one case##########
        (
            local_accumulative_recall,
            local_accumulative_precision,
            global_accumulative_recall,
            global_accumulative_precision,
            gt_flag,
            det_flag,
            hit_str_num,
        ) = many_to_one(
            local_sigma_table,
            local_tau_table,
            local_accumulative_recall,
            local_accumulative_precision,
            global_accumulative_recall,
            global_accumulative_precision,
            gt_flag,
            det_flag,
            idx,
            rec_flag,
        )
        hit_str_count += hit_str_num

    try:
        recall = global_accumulative_recall / total_num_gt
    except ZeroDivisionError:
        recall = 0

    try:
        precision = global_accumulative_precision / total_num_det
    except ZeroDivisionError:
        precision = 0

    try:
        f_score = 2 * precision * recall / (precision + recall)
    except ZeroDivisionError:
        f_score = 0

    try:
        seqerr = 1 - float(hit_str_count) / global_accumulative_recall
    except ZeroDivisionError:
        seqerr = 1

    try:
        recall_e2e = float(hit_str_count) / total_num_gt
    except ZeroDivisionError:
        recall_e2e = 0

    try:
        precision_e2e = float(hit_str_count) / total_num_det
    except ZeroDivisionError:
        precision_e2e = 0

    try:
        f_score_e2e = 2 * precision_e2e * recall_e2e / (precision_e2e + recall_e2e)
    except ZeroDivisionError:
        f_score_e2e = 0

    final = {
        "total_num_gt": total_num_gt,
        "total_num_det": total_num_det,
        "global_accumulative_recall": global_accumulative_recall,
        "hit_str_count": hit_str_count,
        "recall": recall,
        "precision": precision,
        "f_score": f_score,
        "seqerr": seqerr,
        "recall_e2e": recall_e2e,
        "precision_e2e": precision_e2e,
        "f_score_e2e": f_score_e2e,
    }
    return final