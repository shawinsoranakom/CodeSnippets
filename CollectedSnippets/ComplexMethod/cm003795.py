def post_process_instance_segmentation(
        self,
        outputs,
        task_type: str = "instance",
        is_demo: bool = True,
        threshold: float = 0.5,
        mask_threshold: float = 0.5,
        overlap_mask_area_threshold: float = 0.8,
        target_sizes: list[tuple[int, int]] | None = None,
        return_coco_annotation: bool | None = False,
    ):
        """
        Converts the output of [`OneFormerForUniversalSegmentationOutput`] into image instance segmentation
        predictions. Only supports PyTorch.

        Args:
            outputs ([`OneFormerForUniversalSegmentationOutput`]):
                The outputs from [`OneFormerForUniversalSegmentationOutput`].
            task_type (`str`, *optional*, defaults to "instance"):
                The post processing depends on the task token input. If the `task_type` is "panoptic", we need to
                ignore the stuff predictions.
            is_demo (`bool`, *optional)*, defaults to `True`):
                Whether the model is in demo mode. If true, use threshold to predict final masks.
            threshold (`float`, *optional*, defaults to 0.5):
                The probability score threshold to keep predicted instance masks.
            mask_threshold (`float`, *optional*, defaults to 0.5):
                Threshold to use when turning the predicted masks into binary values.
            overlap_mask_area_threshold (`float`, *optional*, defaults to 0.8):
                The overlap mask area threshold to merge or discard small disconnected parts within each binary
                instance mask.
            target_sizes (`List[Tuple]`, *optional*):
                List of length (batch_size), where each list item (`Tuple[int, int]]`) corresponds to the requested
                final size (height, width) of each prediction in batch. If left to None, predictions will not be
                resized.
            return_coco_annotation (`bool`, *optional)*, defaults to `False`):
                Whether to return predictions in COCO format.

        Returns:
            `List[Dict]`: A list of dictionaries, one per image, each dictionary containing two keys:
            - **segmentation** -- a tensor of shape `(height, width)` where each pixel represents a `segment_id`, set
              to `None` if no mask if found above `threshold`. If `target_sizes` is specified, segmentation is resized
              to the corresponding `target_sizes` entry.
            - **segments_info** -- A dictionary that contains additional information on each segment.
                - **id** -- an integer representing the `segment_id`.
                - **label_id** -- An integer representing the label / semantic class id corresponding to `segment_id`.
                - **was_fused** -- a boolean, `True` if `label_id` was in `label_ids_to_fuse`, `False` otherwise.
                  Multiple instances of the same class / label were fused and assigned a single `segment_id`.
                - **score** -- Prediction score of segment with `segment_id`.
        """
        class_queries_logits = outputs.class_queries_logits  # [batch_size, num_queries, num_classes+1]
        masks_queries_logits = outputs.masks_queries_logits  # [batch_size, num_queries, height, width]

        device = masks_queries_logits.device
        batch_size = class_queries_logits.shape[0]
        num_queries = class_queries_logits.shape[1]
        num_classes = class_queries_logits.shape[-1] - 1

        # Loop over items in batch size
        results: list[dict[str, torch.Tensor]] = []

        for i in range(batch_size):
            # [Q, K]
            scores = nn.functional.softmax(class_queries_logits[i], dim=-1)[:, :-1]
            labels = torch.arange(num_classes, device=device).unsqueeze(0).repeat(num_queries, 1).flatten(0, 1)

            # scores_per_image, topk_indices = scores.flatten(0, 1).topk(self.num_queries, sorted=False)
            scores_per_image, topk_indices = scores.flatten(0, 1).topk(num_queries, sorted=False)
            labels_per_image = labels[topk_indices]

            topk_indices = torch.div(topk_indices, num_classes, rounding_mode="floor")
            # mask_pred = mask_pred.unsqueeze(1).repeat(1, self.sem_seg_head.num_classes, 1).flatten(0, 1)
            mask_pred = masks_queries_logits[i][topk_indices]

            # Only consider scores with confidence over [threshold] for demo
            if is_demo:
                keep = scores_per_image > threshold
                scores_per_image = scores_per_image[keep]
                labels_per_image = labels_per_image[keep]
                mask_pred = mask_pred[keep]

            # if this is panoptic segmentation, we only keep the "thing" classes
            if task_type == "panoptic":
                keep = torch.zeros_like(scores_per_image).bool()
                for j, lab in enumerate(labels_per_image):
                    keep[j] = lab in self.metadata["thing_ids"]

                scores_per_image = scores_per_image[keep]
                labels_per_image = labels_per_image[keep]
                mask_pred = mask_pred[keep]

            if mask_pred.shape[0] <= 0:
                height, width = target_sizes[i] if target_sizes is not None else mask_pred.shape[1:]
                segmentation = torch.zeros((height, width)) - 1
                results.append({"segmentation": segmentation, "segments_info": []})
                continue

            if "ade20k" in self.class_info_file and not is_demo and "instance" in task_type:
                for j in range(labels_per_image.shape[0]):
                    labels_per_image[j] = self.metadata["thing_ids"].index(labels_per_image[j].item())

            # Get segmentation map and segment information of batch item
            target_size = target_sizes[i] if target_sizes is not None else None
            segmentation, segments = compute_segments(
                mask_pred,
                scores_per_image,
                labels_per_image,
                mask_threshold,
                overlap_mask_area_threshold,
                set(),
                target_size,
            )

            # Return segmentation map in run-length encoding (RLE) format
            if return_coco_annotation:
                segmentation = convert_segmentation_to_rle(segmentation)

            results.append({"segmentation": segmentation, "segments_info": segments})
        return results