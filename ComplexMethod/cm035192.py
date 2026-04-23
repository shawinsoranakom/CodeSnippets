def e2e_eval(gt_dir, res_dir, ignore_blank=False):
    print("start testing...")
    iou_thresh = 0.5
    val_names = os.listdir(gt_dir)
    num_gt_chars = 0
    gt_count = 0
    dt_count = 0
    hit = 0
    ed_sum = 0

    for i, val_name in enumerate(val_names):
        with open(os.path.join(gt_dir, val_name), encoding="utf-8") as f:
            gt_lines = [o.strip() for o in f.readlines()]
        gts = []
        ignore_masks = []
        for line in gt_lines:
            parts = line.strip().split("\t")
            # ignore illegal data
            if len(parts) < 9:
                continue
            assert len(parts) < 11
            if len(parts) == 9:
                gts.append(parts[:8] + [""])
            else:
                gts.append(parts[:8] + [parts[-1]])

            ignore_masks.append(parts[8])

        val_path = os.path.join(res_dir, val_name)
        if not os.path.exists(val_path):
            dt_lines = []
        else:
            with open(val_path, encoding="utf-8") as f:
                dt_lines = [o.strip() for o in f.readlines()]
        dts = []
        for line in dt_lines:
            # print(line)
            parts = line.strip().split("\t")
            assert len(parts) < 10, "line error: {}".format(line)
            if len(parts) == 8:
                dts.append(parts + [""])
            else:
                dts.append(parts)

        dt_match = [False] * len(dts)
        gt_match = [False] * len(gts)
        all_ious = defaultdict(tuple)
        for index_gt, gt in enumerate(gts):
            gt_coors = [float(gt_coor) for gt_coor in gt[0:8]]
            gt_poly = polygon_from_str(gt_coors)
            for index_dt, dt in enumerate(dts):
                dt_coors = [float(dt_coor) for dt_coor in dt[0:8]]
                dt_poly = polygon_from_str(dt_coors)
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
                if ignore_blank:
                    gt_str = strQ2B(gts[index_gt][8]).replace(" ", "")
                    dt_str = strQ2B(dts[index_dt][8]).replace(" ", "")
                else:
                    gt_str = strQ2B(gts[index_gt][8])
                    dt_str = strQ2B(dts[index_dt][8])
                if ignore_masks[index_gt] == "0":
                    ed_sum += ed(gt_str, dt_str)
                    num_gt_chars += len(gt_str)
                    if gt_str == dt_str:
                        hit += 1
                    gt_count += 1
                    dt_count += 1

        # unmatched dt
        for tindex, dt_match_flag in enumerate(dt_match):
            if dt_match_flag == False:
                dt_str = dts[tindex][8]
                gt_str = ""
                ed_sum += ed(dt_str, gt_str)
                dt_count += 1

        # unmatched gt
        for tindex, gt_match_flag in enumerate(gt_match):
            if gt_match_flag == False and ignore_masks[tindex] == "0":
                dt_str = ""
                gt_str = gts[tindex][8]
                ed_sum += ed(gt_str, dt_str)
                num_gt_chars += len(gt_str)
                gt_count += 1

    eps = 1e-9
    print("hit, dt_count, gt_count", hit, dt_count, gt_count)
    precision = hit / (dt_count + eps)
    recall = hit / (gt_count + eps)
    fmeasure = 2.0 * precision * recall / (precision + recall + eps)
    avg_edit_dist_img = ed_sum / len(val_names)
    avg_edit_dist_field = ed_sum / (gt_count + eps)
    character_acc = 1 - ed_sum / (num_gt_chars + eps)

    print("character_acc: %.2f" % (character_acc * 100) + "%")
    print("avg_edit_dist_field: %.2f" % (avg_edit_dist_field))
    print("avg_edit_dist_img: %.2f" % (avg_edit_dist_img))
    print("precision: %.2f" % (precision * 100) + "%")
    print("recall: %.2f" % (recall * 100) + "%")
    print("fmeasure: %.2f" % (fmeasure * 100) + "%")