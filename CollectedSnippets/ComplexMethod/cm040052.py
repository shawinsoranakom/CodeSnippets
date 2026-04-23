def densify_bounding_boxes(
    bounding_boxes,
    is_batched=False,
    max_boxes=None,
    boxes_default_value=0,
    labels_default_value=-1,
    backend=None,
):
    validate_bounding_boxes(bounding_boxes)
    boxes = bounding_boxes["boxes"]
    labels = bounding_boxes["labels"]
    backend = backend or current_backend
    if isinstance(boxes, list):
        if boxes and isinstance(boxes[0], list):
            if boxes[0] and isinstance(boxes[0][0], list):
                # Batched case
                if not isinstance(labels[0][0], int):
                    raise ValueError(
                        "If providing `bounding_boxes['labels']` as a list, "
                        "it should contain integers labels. Received: "
                        f"bounding_boxes['labels']={labels}"
                    )
                if max_boxes is not None:
                    max_boxes = max([len(b) for b in boxes])
                new_boxes = []
                new_labels = []
                for b, l in zip(boxes, labels):
                    if len(b) >= max_boxes:
                        new_boxes.append(b[:max_boxes])
                        new_labels.append(l[:max_boxes])
                    else:
                        num_boxes_to_add = max_boxes - len(b)
                        added_boxes = [
                            [
                                boxes_default_value,
                                boxes_default_value,
                                boxes_default_value,
                                boxes_default_value,
                            ]
                            for _ in range(num_boxes_to_add)
                        ]
                        new_boxes.append(b + added_boxes)
                        new_labels.append(
                            l
                            + [
                                labels_default_value
                                for _ in range(num_boxes_to_add)
                            ]
                        )
            else:
                # Unbatched case
                if max_boxes and len(b) >= max_boxes:
                    new_boxes = b[:max_boxes]
                    new_labels = l[:max_boxes]
                else:
                    num_boxes_to_add = max_boxes - len(b)
                    added_boxes = [
                        [
                            boxes_default_value,
                            boxes_default_value,
                            boxes_default_value,
                            boxes_default_value,
                        ]
                        for _ in range(num_boxes_to_add)
                    ]
                    new_boxes = b + added_boxes
                    new_labels = l + [
                        labels_default_value for _ in range(num_boxes_to_add)
                    ]
            return {
                "boxes": backend.convert_to_tensor(new_boxes, dtype="float32"),
                "labels": backend.convert_to_tensor(new_labels, dtype="int32"),
            }

    if tf_utils.is_ragged_tensor(boxes):
        bounding_boxes["boxes"] = bounding_boxes["boxes"].to_tensor(
            default_value=boxes_default_value,
            shape=_box_shape(
                is_batched, bounding_boxes["boxes"].shape, max_boxes
            ),
        )
        bounding_boxes["labels"] = bounding_boxes["labels"].to_tensor(
            default_value=labels_default_value,
            shape=_classes_shape(
                is_batched, bounding_boxes["labels"].shape, max_boxes
            ),
        )
        return bounding_boxes

    bounding_boxes["boxes"] = backend.convert_to_tensor(boxes, dtype="float32")
    bounding_boxes["labels"] = backend.convert_to_tensor(labels)
    return bounding_boxes