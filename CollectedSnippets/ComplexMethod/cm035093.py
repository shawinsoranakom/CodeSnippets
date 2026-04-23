def detection_filtering(detections, groundtruths, threshold=0.5):
        for gt in groundtruths:
            point_num = gt["points"].shape[1] // 2
            if gt["transcription"] == "###" and (point_num > 1):
                gt_p = np.array(gt["points"]).reshape(point_num, 2).astype("int32")
                gt_p = plg.Polygon(gt_p)

                for det_id, detection in enumerate(detections):
                    det_y = detection[0::2]
                    det_x = detection[1::2]

                    det_p = np.concatenate((np.array(det_x), np.array(det_y)))
                    det_p = det_p.reshape(2, -1).transpose()
                    det_p = plg.Polygon(det_p)

                    try:
                        det_gt_iou = get_intersection(det_p, gt_p) / det_p.area()
                    except:
                        print(det_x, det_y, gt_p)
                    if det_gt_iou > threshold:
                        detections[det_id] = []

                detections[:] = [item for item in detections if item != []]
        return detections