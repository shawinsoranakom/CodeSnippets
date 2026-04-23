def validate_bounding_boxes(bounding_boxes):
    if (
        not isinstance(bounding_boxes, dict)
        or "labels" not in bounding_boxes
        or "boxes" not in bounding_boxes
    ):
        raise ValueError(
            "Expected `bounding_boxes` agurment to be a "
            "dict with keys 'boxes' and 'labels'. Received: "
            f"bounding_boxes={bounding_boxes}"
        )
    boxes = bounding_boxes["boxes"]
    labels = bounding_boxes["labels"]
    if isinstance(boxes, list):
        if not isinstance(labels, list):
            raise ValueError(
                "If `bounding_boxes['boxes']` is a list, then "
                "`bounding_boxes['labels']` must also be a list."
                f"Received: bounding_boxes['labels']={labels}"
            )
        if len(boxes) != len(labels):
            raise ValueError(
                "If `bounding_boxes['boxes']` and "
                "`bounding_boxes['labels']` are both lists, "
                "they must have the same length. Received: "
                f"len(bounding_boxes['boxes'])={len(boxes)} and "
                f"len(bounding_boxes['labels'])={len(labels)} and "
            )
    elif tf_utils.is_ragged_tensor(boxes):
        if not tf_utils.is_ragged_tensor(labels):
            raise ValueError(
                "If `bounding_boxes['boxes']` is a Ragged tensor, "
                " `bounding_boxes['labels']` must also be a "
                "Ragged tensor. "
                f"Received: bounding_boxes['labels']={labels}"
            )
    else:
        boxes_shape = current_backend.shape(boxes)
        labels_shape = current_backend.shape(labels)
        if len(boxes_shape) == 2:  # (boxes, 4)
            if len(labels_shape) not in {1, 2}:
                raise ValueError(
                    "Found "
                    f"bounding_boxes['boxes'].shape={boxes_shape} "
                    "and expected bounding_boxes['labels'] to have "
                    "rank 1 or 2, but received: "
                    f"bounding_boxes['labels'].shape={labels_shape} "
                )
        elif len(boxes_shape) == 3:
            if len(labels_shape) not in {2, 3}:
                raise ValueError(
                    "Found "
                    f"bounding_boxes['boxes'].shape={boxes_shape} "
                    "and expected bounding_boxes['labels'] to have "
                    "rank 2 or 3, but received: "
                    f"bounding_boxes['labels'].shape={labels_shape} "
                )
        else:
            raise ValueError(
                "Expected `bounding_boxes['boxes']` "
                "to have rank 2 or 3, with shape "
                "(num_boxes, 4) or (batch_size, num_boxes, 4). "
                "Received: "
                f"bounding_boxes['boxes'].shape={boxes_shape}"
            )