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