def index_put_single_dim_strategy(
    op: OpOverload, args: ArgsType, kwargs: KwargsType
) -> list[list[Placement | _ShardingPlaceholder]]:
    """Single-dim sharding strategy for index_put(self, indices, values).

    Strategy format: [output, input, *indices, value]

    How index_put works:

      indices is a tuple of index tensors and Nones:
      - an index tensor at entry i means self is indexed on dim i.
      - a None at entry i means all elements along dim i are selected (like :).
      - any trailing dims (if self.ndim > len(indices)) are also not indexed
        (i.e. implicit trailing Nones).

      All non-None index tensors are broadcast together to produce a
      broadcasted indexing shape. Each position in this broadcasted shape
      serves as an indexing coordinate into self. Each coordinate selects a
      tensor element, or a slice (if non-indexed dims exist).

      values is a tensor broadcastable to the indexing output shape.
      When indexed dims are consecutive starting at dim k, this shape is
      (*self[:k], *broadcast_shape, *self[k+n_indexed:]). When indexed
      dims are non-consecutive, it is (*broadcast_shape, *non_indexed_dims).

    Sharding rules (possibly conservative and incomplete):
      - Index tensors: always Replicate (every rank needs all coordinates).
      - Self cannot be sharded on indexed dims (local position != global position).
      - Self and values CAN be sharded on non-indexed dims.
        The exception is broadcasted value dimensions (size 1) - we require Replicate, but can shard self.
      - Additionally, we allow the full Partial rule on non-indexing tensors.

    """
    self_meta = cast(TensorMeta, args[0])
    indices_meta = cast(tuple[TensorMeta | None, ...], args[1])
    values_meta = cast(TensorMeta, args[2])

    # Determine indexed vs non-indexed dims of self.
    indexed_dims = {i for i, idx in enumerate(indices_meta) if idx is not None}
    non_indexed_dims = [d for d in range(len(self_meta.shape)) if d not in indexed_dims]
    n_indexed = len(indexed_dims)
    values_ndim = len(values_meta.shape)

    # Explicitly compute the broadcast shape of the index tensors.
    index_shapes = [idx.shape for idx in indices_meta if idx is not None]
    broadcast_ndim = len(torch.broadcast_shapes(*index_shapes)) if index_shapes else 0

    # Strategy format: [output, input, *indices, value]
    # The infra flattens the indices list and drops None entries, so only
    # non-None index tensors get a placement slot (all Replicate).
    #
    # Values dim mapping depends on whether indexed dims are contiguous:
    #   Contiguous (e.g., (None, idx0, idx1)): broadcast replaces indexed block in-place.
    #     values shape = (*non_indexed_before, *broadcast_shape, *non_indexed_after)
    #   Non-contiguous (e.g., (idx0, None, idx1)): broadcast goes to front.
    #     values shape = (*broadcast_shape, *non_indexed_dim_sizes)
    indexed_dims_sorted = sorted(indexed_dims)
    contiguous_indexed = len(indexed_dims_sorted) <= 1 or (
        indexed_dims_sorted[-1] - indexed_dims_sorted[0] + 1 == len(indexed_dims_sorted)
    )

    strategies: list[list[Placement | _ShardingPlaceholder]] = []
    for i, self_dim in enumerate(non_indexed_dims):
        if contiguous_indexed and indexed_dims_sorted:
            # Broadcast replaces the indexed block in-place.
            first_indexed = indexed_dims_sorted[0]
            if self_dim < first_indexed:
                values_dim = self_dim
            else:
                values_dim = self_dim - n_indexed + broadcast_ndim
        else:
            # Broadcast goes to front (non-contiguous or no indexed dims).
            values_dim = broadcast_ndim + i

        # values_dim is the position in the result tensor, but values may
        # have fewer dims (right-aligned broadcasting). Convert to the
        # actual values tensor dimension.
        result_ndim = broadcast_ndim + len(non_indexed_dims)
        values_tensor_dim = values_dim - (result_ndim - values_ndim)

        if values_tensor_dim < 0:
            values_placement: Placement | _ShardingPlaceholder = Replicate()
        elif values_meta.shape[values_tensor_dim] == 1:
            values_placement = Replicate()
        else:
            values_placement = _ShardingPlaceholder(values_tensor_dim)

        strategies.append(
            [
                _ShardingPlaceholder(self_dim),
                _ShardingPlaceholder(self_dim),
                *([Replicate()] * n_indexed),
                values_placement,
            ]
        )

    # full-partial rule on non-indexing tensors
    strategies.append(
        [
            Partial(),
            Partial(),
            *([Replicate()] * n_indexed),
            Partial(),
        ]
    )
    return strategies