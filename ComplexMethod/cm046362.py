def process_batch(
        self,
        detections: dict[str, torch.Tensor],
        batch: dict[str, Any],
        conf: float = 0.25,
        iou_thres: float = 0.45,
    ) -> None:
        """Update confusion matrix for object detection task.

        Args:
            detections (dict[str, torch.Tensor]): Dictionary containing detected bounding boxes and their associated
                information. Should contain 'cls', 'conf', and 'bboxes' keys, where 'bboxes' can be Array[N, 4] for
                regular boxes or Array[N, 5] for OBB with angle.
            batch (dict[str, Any]): Batch dictionary containing ground truth data with 'bboxes' (Array[M, 4]| Array[M,
                5]) and 'cls' (Array[M]) keys, where M is the number of ground truth objects.
            conf (float, optional): Confidence threshold for detections.
            iou_thres (float, optional): IoU threshold for matching detections to ground truth.
        """
        gt_cls, gt_bboxes = batch["cls"], batch["bboxes"]
        if self.matches is not None:  # only if visualization is enabled
            self.matches = {k: defaultdict(list) for k in {"TP", "FP", "FN", "GT"}}
            for i in range(gt_cls.shape[0]):
                self._append_matches("GT", batch, i)  # store GT
        is_obb = gt_bboxes.shape[1] == 5  # check if boxes contains angle for OBB
        conf = 0.25 if conf in {None, 0.01 if is_obb else 0.001} else conf  # apply 0.25 if default val conf is passed
        no_pred = detections["cls"].shape[0] == 0
        if gt_cls.shape[0] == 0:  # Check if labels is empty
            if not no_pred:
                detections = {k: detections[k][detections["conf"] > conf] for k in detections}
                detection_classes = detections["cls"].int().tolist()
                for i, dc in enumerate(detection_classes):
                    self.matrix[dc, self.nc] += 1  # FP
                    self._append_matches("FP", detections, i)
            return
        if no_pred:
            gt_classes = gt_cls.int().tolist()
            for i, gc in enumerate(gt_classes):
                self.matrix[self.nc, gc] += 1  # FN
                self._append_matches("FN", batch, i)
            return

        detections = {k: detections[k][detections["conf"] > conf] for k in detections}
        gt_classes = gt_cls.int().tolist()
        detection_classes = detections["cls"].int().tolist()
        bboxes = detections["bboxes"]
        iou = batch_probiou(gt_bboxes, bboxes) if is_obb else box_iou(gt_bboxes, bboxes)

        x = torch.where(iou > iou_thres)
        if x[0].shape[0]:
            matches = torch.cat((torch.stack(x, 1), iou[x[0], x[1]][:, None]), 1).cpu().numpy()
            if x[0].shape[0] > 1:
                matches = matches[matches[:, 2].argsort()[::-1]]
                matches = matches[np.unique(matches[:, 1], return_index=True)[1]]
                matches = matches[matches[:, 2].argsort()[::-1]]
                matches = matches[np.unique(matches[:, 0], return_index=True)[1]]
        else:
            matches = np.zeros((0, 3))

        n = matches.shape[0] > 0
        m0, m1, _ = matches.transpose().astype(int)
        for i, gc in enumerate(gt_classes):
            j = m0 == i
            if n and sum(j) == 1:
                dc = detection_classes[m1[j].item()]
                self.matrix[dc, gc] += 1  # TP if class is correct else both an FP and an FN
                if dc == gc:
                    self._append_matches("TP", detections, m1[j].item())
                else:
                    self._append_matches("FP", detections, m1[j].item())
                    self._append_matches("FN", batch, i)
            else:
                self.matrix[self.nc, gc] += 1  # FN
                self._append_matches("FN", batch, i)

        for i, dc in enumerate(detection_classes):
            if not any(m1 == i):
                self.matrix[dc, self.nc] += 1  # FP
                self._append_matches("FP", detections, i)