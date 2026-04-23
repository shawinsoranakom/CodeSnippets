def group_images_by_shape(
    images: Union[list["torch.Tensor"], "torch.Tensor"],
    *paired_inputs,
    disable_grouping: bool | None,
    is_nested: bool = False,
) -> tuple[dict, ...]:
    """
    Groups images by shape.
    Returns a dictionary with the shape as key and a list of images with that shape as value,
    and a dictionary with the index of the image in the original list as key and the shape and index in the grouped list as value.

    The function supports both flat lists of tensors and nested structures.
    The input must be either all flat or all nested, not a mix of both.

    Args:
        images (Union[list["torch.Tensor"], "torch.Tensor"]):
            A list of images or a single tensor
        paired_inputs (Any, *optional*):
            Zero or more lists that mirror the structure of `images` (flat list, or list of lists when
            `is_nested=True`). Each element is paired 1:1 with the corresponding image so it can be grouped by the
            same shape key. These paired values are grouped alongside `images` but are not stacked in the output, so
            they do not need to be tensors.
        disable_grouping (bool):
            Whether to disable grouping. If None, will be set to True if the images are on CPU, and False otherwise.
            This choice is based on empirical observations, as detailed here: https://github.com/huggingface/transformers/pull/38157
        is_nested (bool, *optional*, defaults to False):
            Whether the images are nested.

    Returns:
        tuple[dict, ...]:
            - A dictionary with shape as key and list/batch of images with that shape as value
            - Zero or more dictionaries (one per argument in `*paired_inputs`) grouped consistently with `images`; these carry
              the corresponding per-item values and are not stacked
            - A dictionary mapping original indices to (shape, index) tuples
    """
    # If disable grouping is not explicitly provided, we favor disabling it if the images are on CPU, and enabling it otherwise.
    if disable_grouping is None:
        device = _get_device_from_images(images, is_nested)
        disable_grouping = device == "cpu"

    if disable_grouping:
        grouped_images_index = {key: (key, 0) for key, _ in _iterate_items(images, is_nested)}
        if is_nested:
            grouped_images_index["_num_sublists"] = len(images)

        return (
            {key: img.unsqueeze(0) for key, img in _iterate_items(images, is_nested)},
            *[
                {key: item.unsqueeze(0) for key, item in _iterate_items(paired_list, is_nested)}
                for paired_list in paired_inputs
            ],
            grouped_images_index,
        )

    # Handle single level nested structure
    grouped_images, *paired_grouped_values, grouped_images_index = _group_images_by_shape(
        images, *paired_inputs, is_nested=is_nested
    )

    # Stack images with the same shape
    grouped_images = {shape: torch.stack(images_list, dim=0) for shape, images_list in grouped_images.items()}

    return grouped_images, *paired_grouped_values, grouped_images_index