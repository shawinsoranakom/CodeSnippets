def convert_segmentation_map_to_binary_masks_fast(
    segmentation_map: "torch.Tensor",
    instance_id_to_semantic_id: dict[int, int] | None = None,
    ignore_index: int | None = None,
):
    if ignore_index is not None:
        segmentation_map = torch.where(segmentation_map == 0, ignore_index, segmentation_map - 1)

    all_labels = torch.unique(segmentation_map)

    if ignore_index is not None:
        all_labels = all_labels[all_labels != ignore_index]  # drop background label if applicable

    binary_masks = [(segmentation_map == i) for i in all_labels]
    if binary_masks:
        binary_masks = torch.stack(binary_masks, dim=0)
    else:
        binary_masks = torch.zeros((0, *segmentation_map.shape), device=segmentation_map.device)

    # Convert instance ids to class ids
    if instance_id_to_semantic_id is not None:
        labels = torch.zeros(all_labels.shape[0], device=segmentation_map.device)

        for i, label in enumerate(all_labels):
            class_id = instance_id_to_semantic_id[(label.item() + 1 if ignore_index is not None else label.item())]
            labels[i] = class_id - 1 if ignore_index is not None else class_id
    else:
        labels = all_labels
    return binary_masks.float(), labels.long()