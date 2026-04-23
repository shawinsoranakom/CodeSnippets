def meta_embedding_bag(
    weight,
    indices,
    offsets,
    scale_grad_by_freq=False,
    mode=0,
    sparse=False,
    per_sample_weights=None,
    include_last_offset=False,
    padding_idx=-1,
):
    torch._check(
        indices.dtype in (torch.long, torch.int),
        lambda: f"expected indices to be long or int, got {indices.dtype}",
    )
    torch._check(
        offsets.dtype in (torch.long, torch.int),
        lambda: f"expected offsets to be long or int, got {offsets.dtype}",
    )
    torch._check(
        utils.is_float_dtype(weight.dtype),
        lambda: f"expected weight to be floating point type, got {weight.dtype}",
    )

    num_bags = offsets.size(0)
    if include_last_offset:
        torch._check(
            num_bags >= 1,
            lambda: "include_last_offset: numBags should be at least 1",
        )
        num_bags -= 1

    output = weight.new_empty(num_bags, weight.size(1))

    if per_sample_weights is not None:
        torch._check(
            mode == MODE_SUM,
            lambda: "embedding_bag: per_sample_weights only supported with mode='sum'",
        )
        torch._check(
            per_sample_weights.ndim == 1,
            lambda: f"expected per_sample_weights to be 1D tensor, got {per_sample_weights.ndim}D",
        )
        torch._check(
            per_sample_weights.numel() == indices.numel(),
            lambda: (
                f"expected per_sample_weights.numel() ({per_sample_weights.numel()} "
                f"to be the same as indices.numel() ({indices.numel()})"
            ),
        )

    def is_fast_path_index_select_scale(src, scale, output, padding_idx):
        return (
            is_fast_path_index_select(src, output, padding_idx) and scale.stride(0) == 1
        )

    def is_fast_path_index_select(src, output, padding_idx):
        return (
            (src.dtype == torch.float or src.dtype == torch.half)
            and src.stride(1) == 1
            and output.stride(1) == 1
            and padding_idx < 0
        )

    def is_fast_path(src, scale, output, padding_idx):
        if scale is not None:
            return is_fast_path_index_select_scale(src, scale, output, padding_idx)
        else:
            return is_fast_path_index_select(src, output, padding_idx)

    if device_hint(offsets) != "cpu":
        offset2bag = indices.new_empty(indices.size(0))
        bag_size = indices.new_empty(offsets.size())
        if mode == MODE_MAX:
            max_indices = indices.new_empty(num_bags, weight.size(1))
        else:
            max_indices = indices.new_empty(0)
    else:
        fast_path_sum = is_fast_path(weight, per_sample_weights, output, padding_idx)
        if mode in (MODE_MEAN, MODE_MAX) or not fast_path_sum:
            offset2bag = offsets.new_empty(indices.size(0))
        else:
            offset2bag = offsets.new_empty(0)
        bag_size = offsets.new_empty(num_bags)
        # This part of the logic comes from make_max_indices_out in EmbeddingBag.cpp
        numBags = offsets.shape[0]
        if mode == MODE_MAX:
            if include_last_offset:
                torch._check(
                    numBags >= 1,
                    lambda: "include_last_offset: numBags should be at least 1",
                )
                numBags -= 1
            max_indices = offsets.new_empty(numBags, weight.shape[1])
        else:
            max_indices = offsets.new_empty(bag_size.size())
    return output, offset2bag, bag_size, max_indices