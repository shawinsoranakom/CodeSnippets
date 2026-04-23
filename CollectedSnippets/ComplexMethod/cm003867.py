def prepare_coco_detection_annotation(
    image,
    target,
    return_segmentation_masks: bool = False,
    input_data_format: ChannelDimension | str | None = None,
):
    """
    Convert the target in COCO format into the format expected by GROUNDING_DINO.
    """
    image_height, image_width = image.size()[-2:]

    image_id = target["image_id"]
    image_id = torch.as_tensor([image_id], dtype=torch.int64, device=image.device)

    # Get all COCO annotations for the given image.
    annotations = target["annotations"]
    classes = []
    area = []
    boxes = []
    keypoints = []
    for obj in annotations:
        if "iscrowd" not in obj or obj["iscrowd"] == 0:
            classes.append(obj["category_id"])
            area.append(obj["area"])
            boxes.append(obj["bbox"])
            if "keypoints" in obj:
                keypoints.append(obj["keypoints"])

    classes = torch.as_tensor(classes, dtype=torch.int64, device=image.device)
    area = torch.as_tensor(area, dtype=torch.float32, device=image.device)
    iscrowd = torch.zeros_like(classes, dtype=torch.int64, device=image.device)
    # guard against no boxes via resizing
    boxes = torch.as_tensor(boxes, dtype=torch.float32, device=image.device).reshape(-1, 4)
    boxes[:, 2:] += boxes[:, :2]
    boxes[:, 0::2] = boxes[:, 0::2].clip(min=0, max=image_width)
    boxes[:, 1::2] = boxes[:, 1::2].clip(min=0, max=image_height)

    keep = (boxes[:, 3] > boxes[:, 1]) & (boxes[:, 2] > boxes[:, 0])

    new_target = {
        "image_id": image_id,
        "class_labels": classes[keep],
        "boxes": boxes[keep],
        "area": area[keep],
        "iscrowd": iscrowd[keep],
        "orig_size": torch.as_tensor([int(image_height), int(image_width)], dtype=torch.int64, device=image.device),
    }

    if keypoints:
        keypoints = torch.as_tensor(keypoints, dtype=torch.float32, device=image.device)
        # Apply the keep mask here to filter the relevant annotations
        keypoints = keypoints[keep]
        num_keypoints = keypoints.shape[0]
        keypoints = keypoints.reshape((-1, 3)) if num_keypoints else keypoints
        new_target["keypoints"] = keypoints

    if return_segmentation_masks:
        segmentation_masks = [obj["segmentation"] for obj in annotations]
        masks = convert_coco_poly_to_mask(segmentation_masks, image_height, image_width, device=image.device)
        new_target["masks"] = masks[keep]

    return new_target