def _scaled_mm_scale_placement(
    data_placement: Placement | _ShardingPlaceholder,
    scale_shape: torch.Size,
    contracting_dim: int,
) -> Placement | _ShardingPlaceholder | None:
    """
    Derive scale placement from data operand placement for _scaled_mm.

    Handles three cases:

    1. Tensor-wise scale (single element): always Replicate.
    2. 2D (or higher) scale, e.g. row-wise [M,1]: copy data placement directly.
    3. 1D blockwise scale, e.g. MX format [M*K/block_size]: map
       non-contracting shard to Shard(0)/_ShardingPlaceholder(0), and reject
       contracting-dim shards (returns None).
    """
    if prod(scale_shape) == 1:
        return Replicate()

    if len(scale_shape) != 1:
        return data_placement

    # 1D blockwise scale: Shard(>=1) is invalid on a 1D tensor, so we need
    # to map the data operand's placement to a valid 1D placement.
    if isinstance(data_placement, _ShardingPlaceholder):
        if data_placement.dim == contracting_dim:
            return None
        return _ShardingPlaceholder(0)
    # NOTE: isinstance(_, Shard) does not match _StridedShard; see _is_shard_like().
    elif isinstance(data_placement, Shard):
        if data_placement.dim == contracting_dim:
            return None
        return Shard(0)
    elif isinstance(data_placement, (Replicate, Partial)):
        return Replicate()
    return data_placement