def gen_single_dim_einsum_strategies(
    equation: str,
    *,
    bias_shape: torch.Size | None = None,
) -> list[list[Placement | _ShardingPlaceholder]]:
    """
    Generate a strategy list for the ops that follow einsum style notation.

    In principle, each mesh dim is independent of other device mesh dim when we
    generate strategies. So we generate strategy over each device mesh dim and
    do product combination on all mesh dims. We basically follow the below rule
    for each device mesh dim:

    1. Shard on contracting dim: When both inputs shard on contracting dim over
       the same device dim. The result will be Partial over that device dim.

    2. Shard on noncontracting dim:
        2.1: Shard on batch dim: output, both inputs all should shard on batch
        dim.
        2.2: Shard on lhs only dim or rhs only dim: both output and lhs or rhs
        input should shard on this free dim.

    3. Per-input linearity (Partial): Since matmul is linear in each input
       independently, one input can remain Partial while others are Replicate,
       producing a Partial output.

    4. Batch-dimension linearity (all-Partial): When all dims are batch dims
       (no contracting or free dims), the operation is element-wise and linear
       in all inputs simultaneously, so all inputs can be Partial.

    5. Bias input (optional): If bias_shape is provided, a bias placement
       is inserted after the output placement. The bias placement is derived from
       the output placement, accounting for broadcast semantics (based on ndim
       difference between output and bias). This is used for addmm-like ops
       (addmm, baddbmm) where bias + mat1 @ mat2.
    """
    # parse einop equation and extract dims
    input_dims, output_dim = EinsumDims.parse_equation(equation)
    edims = EinsumDims.parse_dims(input_dims, output_dim)

    # Compute broadcast dims map for bias if provided
    # Maps output dims to bias dims, -1 for broadcast dims (dims that don't exist in bias
    # or have size 1)
    broadcast_dims_map: list[int] | None = None
    if bias_shape is not None:
        output_ndim = len(output_dim)
        bias_ndim = len(bias_shape)
        pad_size = output_ndim - bias_ndim
        broadcast_dims_map = []
        for i in range(output_ndim):
            if i < pad_size:
                # Padded dimension (not in bias)
                broadcast_dims_map.append(-1)
            else:
                bias_dim_idx = i - pad_size
                if bias_shape[bias_dim_idx] == 1:
                    # Size-1 dimension (broadcasts)
                    broadcast_dims_map.append(-1)
                else:
                    broadcast_dims_map.append(bias_dim_idx)

    def _derive_bias_placement(
        output_placement: Placement | _ShardingPlaceholder,
    ) -> Placement | _ShardingPlaceholder:
        """Derive bias placement from output placement, accounting for broadcast."""
        if broadcast_dims_map is None:
            return copy.copy(output_placement)
        if isinstance(output_placement, _ShardingPlaceholder):
            output_dim_idx = output_placement.dim
            bias_dim = broadcast_dims_map[output_dim_idx]
            if bias_dim == -1:
                # Dim doesn't exist in bias (broadcast), replicate
                return Replicate()
            else:
                return _ShardingPlaceholder(bias_dim)
        else:
            # Clone Partial, Replicate, or other placements
            return copy.copy(output_placement)

    def _maybe_add_bias(
        placement_list: list[Placement | _ShardingPlaceholder],
    ) -> list[Placement | _ShardingPlaceholder]:
        """Insert bias placement after output if bias_shape is provided."""
        if bias_shape is None:
            return placement_list
        output_placement = placement_list[0]
        bias_placement = _derive_bias_placement(output_placement)
        return [placement_list[0], bias_placement] + placement_list[1:]

    # generate strategies for each mesh dim and do cartesian product for final strategy. E.g., for a 2D mesh, we can have [P(),R,R]
    strategies_over_one_mesh_dim: list[list[Placement | _ShardingPlaceholder]] = []
    placement_list: list[Placement | _ShardingPlaceholder]
    # split batch dim
    for batch_dim in edims.batch_dims:
        output_batch_dim = output_dim.index(batch_dim)
        placement_list = [_ShardingPlaceholder(output_batch_dim)]
        for input_dim in input_dims:
            input_batch_dim = input_dim.index(batch_dim)
            placement_list.append(_ShardingPlaceholder(input_batch_dim))

        strategies_over_one_mesh_dim.append(_maybe_add_bias(placement_list))

    # split contracting dim
    for contracting_dim in edims.contracting_dims:
        # Contracting dim can shard on same device axis for both inputs. This
        # results in the output being Partial on that device axis. For example:
        # bmk_{x},k_{x}n -> bmn{Ux} (becomes partial over device axis x)
        placement_list = [Partial()]
        for input_dim in input_dims:
            input_contracting_dim = input_dim.index(contracting_dim)
            placement_list.append(_ShardingPlaceholder(input_contracting_dim))

        strategies_over_one_mesh_dim.append(_maybe_add_bias(placement_list))

    # split lhs free dim
    for lhs_dim in edims.lhs_out_only_dims:
        lhs_free_dim_output = output_dim.index(lhs_dim)
        lhs_free_dim_input = input_dims[0].index(lhs_dim)
        # this means split the lhs input and output
        # i.e. S(0), R -> S(0)
        lhs_placement_list: list[Placement | _ShardingPlaceholder] = [
            _ShardingPlaceholder(lhs_free_dim_output),
            _ShardingPlaceholder(lhs_free_dim_input),
            Replicate(),
        ]
        strategies_over_one_mesh_dim.append(_maybe_add_bias(lhs_placement_list))

    # split rhs free dim
    for rhs_dim in edims.rhs_out_only_dims:
        rhs_free_dim_output = output_dim.index(rhs_dim)
        rhs_free_dim_input = input_dims[1].index(rhs_dim)
        rhs_placement_list: list[Placement | _ShardingPlaceholder] = [
            _ShardingPlaceholder(rhs_free_dim_output),
            Replicate(),
            _ShardingPlaceholder(rhs_free_dim_input),
        ]
        strategies_over_one_mesh_dim.append(_maybe_add_bias(rhs_placement_list))

    # Per-input linearity: matmul is linear in each input independently.
    # One input Partial, the other Replicate → output Partial.
    for reduce_op in Partial.LINEAR_REDUCE_OPS:
        output_placement = Partial(reduce_op)
        strategies_over_one_mesh_dim.append(
            _maybe_add_bias([output_placement, Partial(reduce_op), Replicate()])
        )
        strategies_over_one_mesh_dim.append(
            _maybe_add_bias([output_placement, Replicate(), Partial(reduce_op)])
        )

    # Batch-dimension linearity: when the einsum has no contracting dims and
    # no free dims (all dims are batch dims), the operation is element-wise
    # and linear in all inputs simultaneously. Add all-Partial strategies.
    if (
        not edims.contracting_dims
        and not edims.lhs_out_only_dims
        and not edims.rhs_out_only_dims
    ):
        for reduce_op in Partial.LINEAR_REDUCE_OPS:
            linearity_placements: list[Placement | _ShardingPlaceholder] = [
                Partial(reduce_op)
            ] + [Partial(reduce_op) for _ in input_dims]
            strategies_over_one_mesh_dim.append(_maybe_add_bias(linearity_placements))

    return strategies_over_one_mesh_dim