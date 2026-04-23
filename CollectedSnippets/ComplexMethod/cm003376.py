def post_process_instance_segmentation(
        self,
        outputs,
        threshold: float = 0.5,
        mask_threshold: float = 0.5,
        overlap_mask_area_threshold: float = 0.8,
        target_sizes: list[tuple[int, int]] | None = None,
        return_coco_annotation: bool | None = False,
        return_binary_maps: bool | None = False,
    ) -> list[dict]:
        """
        Converts the output of [`Mask2FormerForUniversalSegmentationOutput`] into instance segmentation predictions.
        Only supports PyTorch. If instances could overlap, set either return_coco_annotation or return_binary_maps
        to `True` to get the correct segmentation result.

        Args:
            outputs ([`Mask2FormerForUniversalSegmentation`]):
                Raw outputs of the model.
            threshold (`float`, *optional*, defaults to 0.5):
                The probability score threshold to keep predicted instance masks.
            mask_threshold (`float`, *optional*, defaults to 0.5):
                Threshold to use when turning the predicted masks into binary values.
            overlap_mask_area_threshold (`float`, *optional*, defaults to 0.8):
                The overlap mask area threshold to merge or discard small disconnected parts within each binary
                instance mask.
            target_sizes (`List[Tuple]`, *optional*):
                List of length (batch_size), where each list item (`Tuple[int, int]]`) corresponds to the requested
                final size (height, width) of each prediction. If left to None, predictions will not be resized.
            return_coco_annotation (`bool`, *optional*, defaults to `False`):
                If set to `True`, segmentation maps are returned in COCO run-length encoding (RLE) format.
            return_binary_maps (`bool`, *optional*, defaults to `False`):
                If set to `True`, segmentation maps are returned as a concatenated tensor of binary segmentation maps
                (one per detected instance).
        Returns:
            `List[Dict]`: A list of dictionaries, one per image, each dictionary containing two keys:
            - **segmentation** -- A tensor of shape `(height, width)` where each pixel represents a `segment_id`, or
              `List[List]` run-length encoding (RLE) of the segmentation map if return_coco_annotation is set to
              `True`, or a tensor of shape `(num_instances, height, width)` if return_binary_maps is set to `True`.
              Set to `None` if no mask if found above `threshold`.
            - **segments_info** -- A dictionary that contains additional information on each segment.
                - **id** -- An integer representing the `segment_id`.
                - **label_id** -- An integer representing the label / semantic class id corresponding to `segment_id`.
                - **score** -- Prediction score of segment with `segment_id`.
        """
        requires_backends(self, ["torch"])
        if return_coco_annotation and return_binary_maps:
            raise ValueError("return_coco_annotation and return_binary_maps can not be both set to True.")

        # [batch_size, num_queries, num_classes+1]
        class_queries_logits = outputs.class_queries_logits
        # [batch_size, num_queries, height, width]
        masks_queries_logits = outputs.masks_queries_logits

        # Scale back to preprocessed image size - (384, 384) for all models
        masks_queries_logits = torch.nn.functional.interpolate(
            masks_queries_logits, size=(384, 384), mode="bilinear", align_corners=False
        )

        device = masks_queries_logits.device
        num_classes = class_queries_logits.shape[-1] - 1
        num_queries = class_queries_logits.shape[-2]

        # Loop over items in batch size
        results: list[dict[str, TensorType]] = []

        for i in range(class_queries_logits.shape[0]):
            mask_pred = masks_queries_logits[i]
            mask_cls = class_queries_logits[i]

            scores = torch.nn.functional.softmax(mask_cls, dim=-1)[:, :-1]
            labels = torch.arange(num_classes, device=device).unsqueeze(0).repeat(num_queries, 1).flatten(0, 1)

            scores_per_image, topk_indices = scores.flatten(0, 1).topk(num_queries, sorted=False)
            labels_per_image = labels[topk_indices]

            topk_indices = torch.div(topk_indices, num_classes, rounding_mode="floor")
            mask_pred = mask_pred[topk_indices]
            pred_masks = (mask_pred > 0).float()

            # Calculate average mask prob
            mask_scores_per_image = (mask_pred.sigmoid().flatten(1) * pred_masks.flatten(1)).sum(1) / (
                pred_masks.flatten(1).sum(1) + 1e-6
            )
            pred_scores = scores_per_image * mask_scores_per_image
            pred_classes = labels_per_image

            segmentation = torch.zeros((384, 384)) - 1
            if target_sizes is not None:
                segmentation = torch.zeros(target_sizes[i]) - 1
                pred_masks = torch.nn.functional.interpolate(
                    pred_masks.unsqueeze(0), size=target_sizes[i], mode="nearest"
                )[0]

            instance_maps, segments = [], []
            current_segment_id = 0
            for j in range(num_queries):
                score = pred_scores[j].item()

                if not torch.all(pred_masks[j] == 0) and score >= threshold:
                    segmentation[pred_masks[j] == 1] = current_segment_id
                    segments.append(
                        {
                            "id": current_segment_id,
                            "label_id": pred_classes[j].item(),
                            "was_fused": False,
                            "score": round(score, 6),
                        }
                    )
                    current_segment_id += 1
                    instance_maps.append(pred_masks[j])

            # Return segmentation map in run-length encoding (RLE) format
            if return_coco_annotation:
                segmentation = convert_segmentation_to_rle(segmentation)

            # Return a concatenated tensor of binary instance maps
            if return_binary_maps and len(instance_maps) != 0:
                segmentation = torch.stack(instance_maps, dim=0)

            results.append({"segmentation": segmentation, "segments_info": segments})
        return results