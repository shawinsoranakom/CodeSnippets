def _handle_row_wise_sharding(
    input,
    world_size,
    weight,
    local_shard,
    offsets,
    per_sample_weights,
    mode,
    max_norm,
    norm_type,
    padding_idx,
    rank,
    pg,
):
    """
    Entry-point function to handle the logic of row-wise sharding of weight
    for embeddingBag. (Detailed explanations of the logic can be found in
    the comment for sharded_embedding_bag.)

    Args:
        input: list of ID used for lookup and aggregation.
        world_size: number of ranks.
        weight: sharded weight tensor.
        local_shard: row-wise shared local weight used for lookup.
        offsets: list of start positions of each bag for 1D input.
        per_sample_weights: weights for weighted sum mode.
        mode: aggregation method of each bag.
        max_norm: If given, each embedding vector with norm larger
            than max_norm is renormalized to have norm max_norm.
            Note: this will modify weight in-place.
        norm_type: The p in the p-norm to compute for the max_norm option.
        padding_idx: If specified, the entries at padding_idx do
            not contribute to the gradient; therefore, the embedding
            vector at padding_idx is not updated during training,
            i.e. it remains as a fixed "pad".
            Note that the embedding vector at padding_idx is
            excluded from the reduction.
        rank: # of cuda process.
        pg: process group.

    Returns:
        gathered_output: final result of lookup and aggregation.
    """
    if input.dim() > 1 and per_sample_weights is None:
        # allgather the inputs first for non Replicated Tensor.
        gather_inp = _all_gather_base_input(input, pg)
    else:
        (
            gathered_inputs,
            gathered_per_sample_weights,
            gathered_offsets,
        ) = _all_gather_embedding_bag_input(input, per_sample_weights, offsets, pg)
        cat_dim = 0 if input.dim() != 1 else -1
        gather_inp = torch.cat(gathered_inputs, dim=cat_dim)
        if per_sample_weights is not None:
            per_sample_weights = torch.cat(gathered_per_sample_weights, dim=cat_dim)
        offset_add = 0 if input.dim() > 1 else input.size(0)
        if offsets is not None:
            offsets_list = torch.cat(
                [gathered_offsets[i] + (offset_add * i) for i in range(pg.size())],
                dim=cat_dim,
            )

    # Mask the input according to sharding spec.
    lookup_input, padding_local, padding_row = _handle_row_wise_mask(
        gather_inp, padding_idx, weight, world_size, rank
    )
    if mode == "max":
        padding_row[:] = -float("Inf")

    # When input is a large tensor, the value of weight is changed.
    # This is a walk-around for now. GH issue: #81717.
    if max_norm is not None:
        torch.nn.functional.embedding_bag(
            torch.unique(lookup_input)[:-1],
            local_shard,
            offsets=torch.tensor([0], device=local_shard.device, dtype=torch.long),
            mode=mode,
            per_sample_weights=None,
            max_norm=max_norm,
            norm_type=norm_type,
            padding_idx=padding_local,
        )
        max_norm = None
    result = torch.nn.functional.embedding_bag(
        lookup_input,
        torch.cat([local_shard, padding_row]),
        offsets=offsets_list if offsets is not None else offsets,  # type: ignore[possibly-undefined]
        mode=mode if mode != "mean" else "sum",
        per_sample_weights=per_sample_weights,
        max_norm=max_norm,
        norm_type=norm_type,
        padding_idx=padding_local,
    )

    op = ReduceOp.SUM if mode != "max" else ReduceOp.MAX
    # TODO: Make the result a PartialTensor and move the logic below there.
    local_shards = result.chunk(pg.size())
    result = reduce_scatter(
        torch.empty_like(local_shards[0]),
        list(local_shards),
        op=op,
        group=pg,
    )

    # For Mean, we cannot do the division until very end because the sum of means
    # not equal to the mean of sum. (Divisor is different)
    if mode == "mean":
        if input.dim() > 1:
            padding_idx = padding_idx if padding_idx is not None else -1
            split_sizes = torch.sum(
                torch.ne(input, padding_idx), dim=-1, dtype=local_shard.dtype
            )
        else:
            split_sizes = torch.cat(
                (
                    offsets[1 : offsets.size(0)] - offsets[0:-1],
                    (input.size(0) - offsets[-1]).unsqueeze(0),
                ),
                dim=-1,
            )
        return torch.div(result, split_sizes.unsqueeze(1))

    # Return the appropriate local result.
    return result