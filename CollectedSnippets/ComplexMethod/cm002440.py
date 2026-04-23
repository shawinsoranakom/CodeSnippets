def _group_images_by_shape(nested_images, *paired_inputs, is_nested: bool = False):
    """
    Helper function to flatten a single level of nested image and batch structures and group by shape.
    Args:
        nested_images (list):
            A list of images or a single tensor
        paired_inputs (Any, *optional*):
            Zero or more lists that mirror the structure of `nested_images` (flat list, or list of lists when
            `is_nested=True`). Each element is paired 1:1 with the corresponding image so it can be grouped by the
            same shape key. These paired values are grouped alongside `nested_images` but are not stacked in the output, so
            they do not need to be tensors.
        is_nested (bool, *optional*, defaults to False):
            Whether the images are nested.
    Returns:
        tuple[dict, ...]:
            - A dictionary with shape as key and list of images with that shape as value
            - A dictionary with shape as key and list of paired values with that shape as value
            - A dictionary mapping original indices to (shape, index) tuples
            - A dictionary mapping original indices to (shape, index) tuples for each paired input
    """
    grouped_images = defaultdict(list)
    grouped_images_index = {}
    paired_grouped_values = [defaultdict(list) for _ in paired_inputs]

    # Normalize inputs to consistent nested structure
    normalized_images = [nested_images] if not is_nested else nested_images
    normalized_paired = []
    for paired_input in paired_inputs:
        normalized_paired.append([paired_input] if not is_nested else paired_input)

    # Process each image and group by shape
    for i, (sublist, *paired_sublists) in enumerate(zip(normalized_images, *normalized_paired)):
        for j, (image, *paired_values) in enumerate(zip(sublist, *paired_sublists)):
            key = (i, j) if is_nested else j
            shape = image.shape[1:]

            # Add to grouped structures
            grouped_images[shape].append(image)
            for paired_index, paired_value in enumerate(paired_values):
                paired_grouped_values[paired_index][shape].append(paired_value)
            grouped_images_index[key] = (shape, len(grouped_images[shape]) - 1)

    # Store structure size for nested inputs to handle empty sublists during reconstruction
    if is_nested:
        grouped_images_index["_num_sublists"] = len(normalized_images)

    return grouped_images, *paired_grouped_values, grouped_images_index