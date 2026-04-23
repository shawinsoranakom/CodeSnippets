def compute_segments(
    mask_probs: "torch.Tensor",
    pred_scores: "torch.Tensor",
    pred_labels: "torch.Tensor",
    label_ids_to_fuse: set[int] | None,
    mask_threshold: float = 0.5,
    overlap_mask_area_threshold: float = 0.8,
    target_size: tuple[int, int] | None = None,
) -> tuple["torch.Tensor", list[dict[str, int | float]]]:
    """
    Converts per-query mask predictions into a panoptic segmentation map.

    Args:
        mask_probs (`torch.Tensor`):
            Tensor of shape `(num_queries, height, width)` containing per-query mask logits.
        pred_scores (`torch.Tensor`):
            Tensor of shape `(num_queries,)` containing the confidence score of each predicted query.
        pred_labels (`torch.Tensor`):
            Tensor of shape `(num_queries,)` containing the predicted class ID of each query.
        label_ids_to_fuse (`set[int]`, *optional*):
            Label IDs that should be fused across disconnected regions.
        mask_threshold (`float`, *optional*, defaults to 0.5):
            Threshold used to binarize the query mask probabilities.
        overlap_mask_area_threshold (`float`, *optional*, defaults to 0.8):
            Minimum overlap ratio required to keep a predicted segment.
        target_size (`tuple[int, int]`, *optional*):
            Final `(height, width)` of the segmentation map. If unset, uses the spatial size of `mask_probs`.

    Returns:
        `tuple[torch.Tensor, list[dict[str, int | float]]]`: The panoptic segmentation map and the metadata for each
        predicted segment.
    """
    height = mask_probs.shape[1] if target_size is None else target_size[0]
    width = mask_probs.shape[2] if target_size is None else target_size[1]

    segmentation = torch.zeros((height, width), dtype=torch.long, device=mask_probs.device) - 1
    segments: list[dict] = []

    mask_probs = mask_probs.sigmoid()
    mask_labels = (pred_scores[:, None, None] * mask_probs).argmax(0)

    current_segment_id = 0
    stuff_memory_list: dict[int, int] = {}

    for query_idx in range(pred_labels.shape[0]):
        pred_class = pred_labels[query_idx].item()

        mask_exists, final_mask = check_segment_validity(
            mask_labels, mask_probs, query_idx, mask_threshold, overlap_mask_area_threshold
        )

        if not mask_exists:
            continue

        if label_ids_to_fuse and pred_class in label_ids_to_fuse:
            if pred_class in stuff_memory_list:
                segmentation[final_mask] = stuff_memory_list[pred_class]
                continue
            else:
                stuff_memory_list[pred_class] = current_segment_id

        segmentation[final_mask] = current_segment_id
        segment_score = round(pred_scores[query_idx].item(), 6)
        segments.append(
            {
                "id": current_segment_id,
                "label_id": pred_class,
                "score": segment_score,
            }
        )
        current_segment_id += 1
    return segmentation, segments