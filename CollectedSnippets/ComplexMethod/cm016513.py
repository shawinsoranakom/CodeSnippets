def calculate_shape(patches, weight, key, original_weights=None):
    current_shape = weight.shape

    for p in patches:
        v = p[1]
        offset = p[3]

        # Offsets restore the old shape; lists force a diff without metadata
        if offset is not None or isinstance(v, list):
            continue

        if isinstance(v, weight_adapter.WeightAdapterBase):
            adapter_shape = v.calculate_shape(key)
            if adapter_shape is not None:
                current_shape = adapter_shape
            continue

        # Standard diff logic with padding
        if len(v) == 2:
            patch_type, patch_data = v[0], v[1]
            if patch_type == "diff" and len(patch_data) > 1 and patch_data[1]['pad_weight']:
                current_shape = patch_data[0].shape

    return current_shape