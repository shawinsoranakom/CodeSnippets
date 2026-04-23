def eval_e2e(args):
    # gt
    gt_results = parse_ser_results_fp(args.gt_json_path, "gt", args.ignore_background)
    # pred
    dt_results = parse_ser_results_fp(
        args.pred_json_path, "pred", args.ignore_background
    )
    iou_thresh = args.iou_thres
    num_gt_chars = 0
    gt_count = 0
    dt_count = 0
    hit = 0
    ed_sum = 0

    for img_name in dt_results:
        gt_info = gt_results[img_name]
        gt_count += len(gt_info)

        dt_info = dt_results[img_name]
        dt_count += len(dt_info)

        dt_match = [False] * len(dt_info)
        gt_match = [False] * len(gt_info)

        all_ious = defaultdict(tuple)
        # gt: {text, label, bbox or poly}
        for index_gt, gt in enumerate(gt_info):
            if "poly" not in gt:
                gt["poly"] = convert_bbox_to_polygon(gt["bbox"])
            gt_poly = polygon_from_str(gt["poly"])
            for index_dt, dt in enumerate(dt_info):
                if "poly" not in dt:
                    dt["poly"] = convert_bbox_to_polygon(dt["bbox"])
                dt_poly = polygon_from_str(dt["poly"])
                iou = polygon_iou(dt_poly, gt_poly)
                if iou >= iou_thresh:
                    all_ious[(index_gt, index_dt)] = iou
        sorted_ious = sorted(all_ious.items(), key=operator.itemgetter(1), reverse=True)
        sorted_gt_dt_pairs = [item[0] for item in sorted_ious]

        # matched gt and dt
        for gt_dt_pair in sorted_gt_dt_pairs:
            index_gt, index_dt = gt_dt_pair
            if gt_match[index_gt] == False and dt_match[index_dt] == False:
                gt_match[index_gt] = True
                dt_match[index_dt] = True
                # ocr rec results
                gt_text = gt_info[index_gt]["text"]
                dt_text = dt_info[index_dt]["text"]

                # ser results
                gt_label = gt_info[index_gt]["label"]
                dt_label = dt_info[index_dt]["pred"]

                if True:  # ignore_masks[index_gt] == '0':
                    ed_sum += ed(args, gt_text, dt_text)
                    num_gt_chars += len(gt_text)
                    if gt_text == dt_text:
                        if args.ignore_ser_prediction or gt_label == dt_label:
                            hit += 1

        # unmatched dt
        for tindex, dt_match_flag in enumerate(dt_match):
            if dt_match_flag == False:
                dt_text = dt_info[tindex]["text"]
                gt_text = ""
                ed_sum += ed(args, dt_text, gt_text)

        # unmatched gt
        for tindex, gt_match_flag in enumerate(gt_match):
            if gt_match_flag == False:
                dt_text = ""
                gt_text = gt_info[tindex]["text"]
                ed_sum += ed(args, gt_text, dt_text)
                num_gt_chars += len(gt_text)

    eps = 1e-9
    print("config: ", args)
    print("hit, dt_count, gt_count", hit, dt_count, gt_count)
    precision = hit / (dt_count + eps)
    recall = hit / (gt_count + eps)
    fmeasure = 2.0 * precision * recall / (precision + recall + eps)
    avg_edit_dist_img = ed_sum / len(gt_results)
    avg_edit_dist_field = ed_sum / (gt_count + eps)
    character_acc = 1 - ed_sum / (num_gt_chars + eps)

    print("character_acc: %.2f" % (character_acc * 100) + "%")
    print("avg_edit_dist_field: %.2f" % (avg_edit_dist_field))
    print("avg_edit_dist_img: %.2f" % (avg_edit_dist_img))
    print("precision: %.2f" % (precision * 100) + "%")
    print("recall: %.2f" % (recall * 100) + "%")
    print("fmeasure: %.2f" % (fmeasure * 100) + "%")

    return