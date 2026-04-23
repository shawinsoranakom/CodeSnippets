def post_process_instance_segmentation(
        self,
        outputs,
        threshold: float = 0.3,
        mask_threshold: float = 0.5,
        target_sizes: list[tuple] | None = None,
    ):
        """
        Converts the raw output of [`Sam3Model`] into instance segmentation predictions with bounding boxes and masks.

        Args:
            outputs ([`Sam3ImageSegmentationOutput`]):
                Raw outputs of the model containing pred_boxes, pred_logits, pred_masks, and optionally
                presence_logits.
            threshold (`float`, *optional*, defaults to 0.3):
                Score threshold to keep instance predictions.
            mask_threshold (`float`, *optional*, defaults to 0.5):
                Threshold for binarizing the predicted masks.
            target_sizes (`list[tuple[int, int]]`, *optional*):
                List of tuples (`tuple[int, int]`) containing the target size `(height, width)` of each image in the
                batch. If unset, predictions will not be resized.

        Returns:
            `list[dict]`: A list of dictionaries, each dictionary containing the following keys:
                - **scores** (`torch.Tensor`): The confidence scores for each predicted instance on the image.
                - **boxes** (`torch.Tensor`): Image bounding boxes in (top_left_x, top_left_y, bottom_right_x,
                  bottom_right_y) format.
                - **masks** (`torch.Tensor`): Binary segmentation masks for each instance, shape (num_instances,
                  height, width).
        """
        pred_logits = outputs.pred_logits  # (batch_size, num_queries)
        pred_boxes = outputs.pred_boxes  # (batch_size, num_queries, 4) in xyxy format
        pred_masks = outputs.pred_masks  # (batch_size, num_queries, height, width)
        presence_logits = outputs.presence_logits  # (batch_size, 1) or None

        batch_size = pred_logits.shape[0]

        if target_sizes is not None and len(target_sizes) != batch_size:
            raise ValueError("Make sure that you pass in as many target sizes as images")

        # Compute scores: combine pred_logits with presence_logits if available
        batch_scores = pred_logits.sigmoid()
        if presence_logits is not None:
            presence_scores = presence_logits.sigmoid()  # (batch_size, 1)
            batch_scores = batch_scores * presence_scores  # Broadcast multiplication

        # Apply sigmoid to mask logits
        batch_masks = pred_masks.sigmoid()

        # Boxes are already in xyxy format from the model
        batch_boxes = pred_boxes

        # Scale boxes to target sizes if provided
        if target_sizes is not None:
            batch_boxes = _scale_boxes(batch_boxes, target_sizes)

        results = []
        for idx, (scores, boxes, masks) in enumerate(zip(batch_scores, batch_boxes, batch_masks)):
            # Filter by score threshold
            keep = scores > threshold
            scores = scores[keep]
            boxes = boxes[keep]
            masks = masks[keep]  # (num_keep, height, width)

            # Resize masks to target size if provided
            if target_sizes is not None:
                target_size = target_sizes[idx]
                if len(masks) > 0:
                    masks = torch.nn.functional.interpolate(
                        masks.unsqueeze(0),  # (1, num_keep, height, width)
                        size=target_size,
                        mode="bilinear",
                        align_corners=False,
                    ).squeeze(0)  # (num_keep, target_height, target_width)

            # Binarize masks
            masks = (masks > mask_threshold).to(torch.long)

            results.append({"scores": scores, "boxes": boxes, "masks": masks})

        return results