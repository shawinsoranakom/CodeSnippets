def compute_segments(
    mask_probs,
    pred_scores,
    pred_labels,
    stuff_classes,
    mask_threshold: float = 0.5,
    overlap_mask_area_threshold: float = 0.8,
    target_size: tuple[int, int] | None = None,
):
    height = mask_probs.shape[1] if target_size is None else target_size[0]
    width = mask_probs.shape[2] if target_size is None else target_size[1]

    segmentation = torch.zeros((height, width), dtype=torch.long, device=mask_probs.device) - 1
    segments: list[dict] = []

    # Compute per-pixel assignment based on weighted mask scores
    mask_probs = mask_probs.sigmoid()
    mask_labels = (pred_scores[:, None, None] * mask_probs).argmax(0)

    # Keep track of instances of each class
    current_segment_id = 0
    stuff_memory_list: dict[str, int] = {}

    for k in range(pred_labels.shape[0]):
        pred_class = pred_labels[k].item()

        # Check if mask exists and large enough to be a segment
        mask_exists, final_mask = check_segment_validity(
            mask_labels, mask_probs, k, mask_threshold, overlap_mask_area_threshold
        )

        if not mask_exists:
            continue

        if stuff_classes and pred_class in stuff_classes:
            if pred_class in stuff_memory_list:
                segmentation[final_mask] = stuff_memory_list[pred_class]
                continue
            else:
                stuff_memory_list[pred_class] = current_segment_id

        segmentation[final_mask] = current_segment_id
        segment_score = round(pred_scores[k].item(), 6)
        segments.append(
            {
                "id": current_segment_id,
                "label_id": pred_class,
                "score": segment_score,
            }
        )
        current_segment_id += 1
    return segmentation, segments