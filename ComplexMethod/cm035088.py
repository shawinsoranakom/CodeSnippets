def get_socre_A(gt_dir, pred_dict):
    allInputs = 1

    def input_reading_mod(pred_dict):
        """This helper reads input from txt files"""
        det = []
        n = len(pred_dict)
        for i in range(n):
            points = pred_dict[i]["points"]
            text = pred_dict[i]["texts"]
            point = ",".join(
                map(
                    str,
                    points.reshape(
                        -1,
                    ),
                )
            )
            det.append([point, text])
        return det

    def gt_reading_mod(gt_dict):
        """This helper reads groundtruths from mat files"""
        gt = []
        n = len(gt_dict)
        for i in range(n):
            points = gt_dict[i]["points"].tolist()
            h = len(points)
            text = gt_dict[i]["text"]
            xx = [
                np.array(["x:"], dtype="<U2"),
                0,
                np.array(["y:"], dtype="<U2"),
                0,
                np.array(["#"], dtype="<U1"),
                np.array(["#"], dtype="<U1"),
            ]
            t_x, t_y = [], []
            for j in range(h):
                t_x.append(points[j][0])
                t_y.append(points[j][1])
            xx[1] = np.array([t_x], dtype="int16")
            xx[3] = np.array([t_y], dtype="int16")
            if text != "":
                xx[4] = np.array([text], dtype="U{}".format(len(text)))
                xx[5] = np.array(["c"], dtype="<U1")
            gt.append(xx)
        return gt

    def detection_filtering(detections, groundtruths, threshold=0.5):
        for gt_id, gt in enumerate(groundtruths):
            if (gt[5] == "#") and (gt[1].shape[1] > 1):
                gt_x = list(map(int, np.squeeze(gt[1])))
                gt_y = list(map(int, np.squeeze(gt[3])))
                for det_id, detection in enumerate(detections):
                    detection_orig = detection
                    detection = [float(x) for x in detection[0].split(",")]
                    detection = list(map(int, detection))
                    det_x = detection[0::2]
                    det_y = detection[1::2]
                    det_gt_iou = iod(det_x, det_y, gt_x, gt_y)
                    if det_gt_iou > threshold:
                        detections[det_id] = []

                detections[:] = [item for item in detections if item != []]
        return detections

    def sigma_calculation(det_x, det_y, gt_x, gt_y):
        """
        sigma = inter_area / gt_area
        """
        return np.round(
            (area_of_intersection(det_x, det_y, gt_x, gt_y) / area(gt_x, gt_y)), 2
        )

    def tau_calculation(det_x, det_y, gt_x, gt_y):
        if area(det_x, det_y) == 0.0:
            return 0
        return np.round(
            (area_of_intersection(det_x, det_y, gt_x, gt_y) / area(det_x, det_y)), 2
        )

    ##############################Initialization###################################
    # global_sigma = []
    # global_tau = []
    # global_pred_str = []
    # global_gt_str = []
    ###############################################################################

    for input_id in range(allInputs):
        if (
            (input_id != ".DS_Store")
            and (input_id != "Pascal_result.txt")
            and (input_id != "Pascal_result_curved.txt")
            and (input_id != "Pascal_result_non_curved.txt")
            and (input_id != "Deteval_result.txt")
            and (input_id != "Deteval_result_curved.txt")
            and (input_id != "Deteval_result_non_curved.txt")
        ):
            detections = input_reading_mod(pred_dict)
            groundtruths = gt_reading_mod(gt_dir)
            detections = detection_filtering(
                detections, groundtruths
            )  # filters detections overlapping with DC area
            dc_id = []
            for i in range(len(groundtruths)):
                if groundtruths[i][5] == "#":
                    dc_id.append(i)
            cnt = 0
            for a in dc_id:
                num = a - cnt
                del groundtruths[num]
                cnt += 1

            local_sigma_table = np.zeros((len(groundtruths), len(detections)))
            local_tau_table = np.zeros((len(groundtruths), len(detections)))
            local_pred_str = {}
            local_gt_str = {}

            for gt_id, gt in enumerate(groundtruths):
                if len(detections) > 0:
                    for det_id, detection in enumerate(detections):
                        detection_orig = detection
                        detection = [float(x) for x in detection[0].split(",")]
                        detection = list(map(int, detection))
                        pred_seq_str = detection_orig[1].strip()
                        det_x = detection[0::2]
                        det_y = detection[1::2]
                        gt_x = list(map(int, np.squeeze(gt[1])))
                        gt_y = list(map(int, np.squeeze(gt[3])))
                        gt_seq_str = str(gt[4].tolist()[0])

                        local_sigma_table[gt_id, det_id] = sigma_calculation(
                            det_x, det_y, gt_x, gt_y
                        )
                        local_tau_table[gt_id, det_id] = tau_calculation(
                            det_x, det_y, gt_x, gt_y
                        )
                        local_pred_str[det_id] = pred_seq_str
                        local_gt_str[gt_id] = gt_seq_str

            global_sigma = local_sigma_table
            global_tau = local_tau_table
            global_pred_str = local_pred_str
            global_gt_str = local_gt_str

    single_data = {}
    single_data["sigma"] = global_sigma
    single_data["global_tau"] = global_tau
    single_data["global_pred_str"] = global_pred_str
    single_data["global_gt_str"] = global_gt_str
    return single_data