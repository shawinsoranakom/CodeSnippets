def convert_segmentation_map_to_binary_masks(
        self,
        segmentation_map: "torch.Tensor",
        instance_id_to_semantic_id: dict[int, int] | None = None,
        ignore_index: int | None = None,
        do_reduce_labels: bool = False,
    ):
        if do_reduce_labels and ignore_index is None:
            raise ValueError("If `do_reduce_labels` is True, `ignore_index` must be provided.")

        if do_reduce_labels:
            segmentation_map = torch.where(segmentation_map == 0, ignore_index, segmentation_map - 1)

        all_labels = torch.unique(segmentation_map)

        if ignore_index is not None:
            all_labels = all_labels[all_labels != ignore_index]

        binary_masks = [(segmentation_map == i) for i in all_labels]

        if binary_masks:
            binary_masks = torch.stack(binary_masks, dim=0)
        else:
            binary_masks = torch.zeros((0, *segmentation_map.shape), device=segmentation_map.device)

        # Convert instance ids to class ids
        if instance_id_to_semantic_id is not None:
            labels = torch.zeros(all_labels.shape[0], device=segmentation_map.device)

            for i, label in enumerate(all_labels):
                class_id = instance_id_to_semantic_id[(label.item() + 1 if do_reduce_labels else label.item())]
                labels[i] = class_id - 1 if do_reduce_labels else class_id
        else:
            labels = all_labels

        return (
            binary_masks.float(),
            labels.long(),
        )