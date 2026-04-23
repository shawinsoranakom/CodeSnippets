def post_process_pose_estimation(
        self,
        outputs: "VitPoseEstimatorOutput",
        boxes: list[list[list[float]]] | np.ndarray,
        kernel_size: int = 11,
        threshold: float | None = None,
        target_sizes: TensorType | list[tuple] | None = None,
    ):
        """
        Transform the heatmaps into keypoint predictions and transform them back to the image.

        Args:
            outputs (`VitPoseEstimatorOutput`):
                VitPoseForPoseEstimation model outputs.
            boxes (`list[list[list[float]]]` or `np.ndarray`):
                List or array of bounding boxes for each image. Each box should be a list of 4 floats representing the bounding
                box coordinates in COCO format (top_left_x, top_left_y, width, height).
            kernel_size (`int`, *optional*, defaults to 11):
                Gaussian kernel size (K) for modulation.
            threshold (`float`, *optional*, defaults to None):
                Score threshold to keep object detection predictions.
            target_sizes (`torch.Tensor` or `list[tuple[int, int]]`, *optional*):
                Tensor of shape `(batch_size, 2)` or list of tuples (`tuple[int, int]`) containing the target size
                `(height, width)` of each image in the batch. If unset, predictions will be resize with the default value.
        Returns:
            `list[list[Dict]]`: A list of dictionaries, each dictionary containing the keypoints and boxes for an image
            in the batch as predicted by the model.
        """
        import torch

        batch_size, num_keypoints, _, _ = outputs.heatmaps.shape
        if target_sizes is not None and batch_size != len(target_sizes):
            raise ValueError("Make sure that you pass in as many target sizes as the batch dimension of the logits")
        centers = np.zeros((batch_size, 2), dtype=np.float32)
        scales = np.zeros((batch_size, 2), dtype=np.float32)
        flattened_boxes = list(itertools.chain(*boxes))
        for i in range(batch_size):
            if target_sizes is not None:
                image_width, image_height = target_sizes[i][0], target_sizes[i][1]
                scale_factor = np.array([image_width, image_height, image_width, image_height])
                flattened_boxes[i] = flattened_boxes[i] * scale_factor
            width, height = self.size["width"], self.size["height"]
            center, scale = box_to_center_and_scale(flattened_boxes[i], image_width=width, image_height=height)
            centers[i, :] = center
            scales[i, :] = scale
        preds, scores = self.keypoints_from_heatmaps(
            outputs.heatmaps.cpu().numpy(), centers, scales, kernel=kernel_size
        )
        all_boxes = np.zeros((batch_size, 4), dtype=np.float32)
        all_boxes[:, 0:2] = centers[:, 0:2]
        all_boxes[:, 2:4] = scales[:, 0:2]
        poses = torch.tensor(preds)
        scores = torch.tensor(scores)
        labels = torch.arange(0, num_keypoints)
        bboxes_xyxy = torch.tensor(coco_to_pascal_voc(all_boxes))
        results: list[list[dict[str, torch.Tensor]]] = []
        pose_bbox_pairs = zip(poses, scores, bboxes_xyxy)
        for image_bboxes in boxes:
            image_results: list[dict[str, torch.Tensor]] = []
            for _ in image_bboxes:
                pose, score, bbox_xyxy = next(pose_bbox_pairs)
                score = score.squeeze()
                keypoints_labels = labels
                if threshold is not None:
                    keep = score > threshold
                    pose = pose[keep]
                    score = score[keep]
                    keypoints_labels = keypoints_labels[keep]
                pose_result = {"keypoints": pose, "scores": score, "labels": keypoints_labels, "bbox": bbox_xyxy}
                image_results.append(pose_result)
            results.append(image_results)
        return results