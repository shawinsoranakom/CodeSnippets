def post_process_grounded_object_detection(
        self,
        outputs: "OmDetTurboObjectDetectionOutput",
        text_labels: list[str] | list[list[str]] | None = None,
        threshold: float = 0.3,
        nms_threshold: float = 0.5,
        target_sizes: TensorType | list[tuple] | None = None,
        max_num_det: int | None = None,
    ):
        """
        Converts the raw output of [`OmDetTurboForObjectDetection`] into final bounding boxes in (top_left_x, top_left_y,
        bottom_right_x, bottom_right_y) format and get the associated text class.

        Args:
            outputs ([`OmDetTurboObjectDetectionOutput`]):
                Raw outputs of the model.
            text_labels (Union[list[str], list[list[str]]], *optional*):
                The input classes names. If not provided, `text_labels` will be set to `None` in `outputs`.
            threshold (float, defaults to 0.3):
                Only return detections with a confidence score exceeding this threshold.
            nms_threshold (float, defaults to 0.5):
                The threshold to use for box non-maximum suppression. Value in [0, 1].
            target_sizes (`torch.Tensor` or `list[tuple[int, int]]`, *optional*):
                Tensor of shape `(batch_size, 2)` or list of tuples (`tuple[int, int]`) containing the target size
                `(height, width)` of each image in the batch. If unset, predictions will not be resized.
            max_num_det (`int`, *optional*):
                The maximum number of detections to return.
        Returns:
            `list[Dict]`: A list of dictionaries, each dictionary containing the scores, classes and boxes for an image
            in the batch as predicted by the model.
        """

        batch_size = len(outputs.decoder_coord_logits)

        # Inputs consistency check for target sizes
        if target_sizes is None:
            height, width = self._get_default_image_size()
            target_sizes = [(height, width)] * batch_size

        if any(len(image_size) != 2 for image_size in target_sizes):
            raise ValueError(
                "Each element of target_sizes must contain the size (height, width) of each image of the batch"
            )

        if len(target_sizes) != batch_size:
            raise ValueError("Make sure that you pass in as many target sizes as output sequences")

        # Inputs consistency check for text labels
        if text_labels is not None and isinstance(text_labels[0], str):
            text_labels = [text_labels]

        if text_labels is not None and len(text_labels) != batch_size:
            raise ValueError("Make sure that you pass in as many classes group as output sequences")

        # Convert target_sizes to list for easier handling
        if isinstance(target_sizes, torch.Tensor):
            target_sizes = target_sizes.tolist()

        batch_boxes = outputs.decoder_coord_logits
        batch_logits = outputs.decoder_class_logits
        batch_num_classes = outputs.classes_structure

        batch_scores, batch_labels = compute_score(batch_logits)

        results = []
        for boxes, scores, image_size, image_num_classes in zip(
            batch_boxes, batch_scores, target_sizes, batch_num_classes
        ):
            boxes, scores, labels = _post_process_boxes_for_image(
                boxes=boxes,
                scores=scores,
                labels=batch_labels,
                image_num_classes=image_num_classes,
                image_size=image_size,
                threshold=threshold,
                nms_threshold=nms_threshold,
                max_num_det=max_num_det,
            )
            result = {"boxes": boxes, "scores": scores, "labels": labels, "text_labels": None}
            results.append(result)

        # Add text labels
        if text_labels is not None:
            for result, image_text_labels in zip(results, text_labels):
                result["text_labels"] = [image_text_labels[idx] for idx in result["labels"]]

        return results