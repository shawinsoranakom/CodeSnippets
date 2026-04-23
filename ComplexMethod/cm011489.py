def expand_to_full_mesh_op_strategy(
    mesh: DeviceMesh,
    op_schema: OpSchema,
    single_mesh_dim_strategies: list[PlacementList],
    *,
    output_tensor_meta: TensorMeta | Sequence[TensorMeta | None] | None = None,
    input_index: int = 1,
    inplace_op: bool = False,
    allow_unbacked_sharding: bool | None = None,
    allow_uneven_sharding: bool = False,
    is_valid_strategy_cb: Callable[
        [list[DTensorSpec], DTensorSpec | tuple[DTensorSpec | None, ...]], bool
    ]
    | None = None,
    different_mesh_args: list[int] | None = None,
) -> OpStrategy:
    """
    Convenience function to allow writing a sharding strategy considering only a single mesh dimension,
    and have it expanded combinatorially to all mesh dimensions.

    Args:
        mesh (DeviceMesh): the device mesh to expand the strategy to
        op_schema (OpSchema): the op schema
        single_mesh_dim_strategies (list[PlacementList]): the sharding strategies to expand. The outer list is over
            different strategies.  The inner PlacementList is over the outputs and inputs of the op. If input_index is 1,
            a PlacementList looks like [output_placement, input_placement1, input_placement2, ...].
        output_tensor_meta: tensor metadata for the output(s), used to populate DTensorSpec.tensor_meta field
        input_index: the number of outputs of the op, defaults to 1
        inplace_op: whether the op is inplace or not, defaults to False
        is_valid_strategy_cb: a callback function to filter out invalid sharding rules, defaults to None.

    Example: Let's say `my_op(tensor_x, tensor_y) - > output_tensor`  can support sharding or replicating tensor_x,
    but always requires tensor_y to be replicated.  We can specify these valid combinations ignoring mesh dims.
    Then, we can rely on `expand_to_full_mesh_op_strategy` to create every possible combination of these shardings
    over multiple mesh dimensions, filtering out any combinations that are invalid based on the actual mesh dim size.

        single_mesh_dim_strategies = [
            # first strategy: return output sharded on first dim, shard tensor_x on its first dim, replicate tensor_y
            [Shard(0), Shard(0), Replicate()]
            # second strategy: replicate output, and both inputs
            [Replicate(), Replicate(), Replicate()]
        ]
    """
    # Expand the single_mesh_dim_strategies to full mesh dim strategies.
    all_mesh_dim_strategies = [single_mesh_dim_strategies] * mesh.ndim

    strategy_combs = itertools.product(*all_mesh_dim_strategies)

    args_strategy = op_schema.args_strategy
    kwargs_strategy = op_schema.kwargs_strategy
    input_args_strategy = args_strategy + kwargs_strategy

    # Propagate use_strided_shard_as_shard_order from inputs so that
    # strategy specs with _StridedShard get the correct flag (and thus
    # correct shard_order) at construction time, avoiding shard_order
    # mismatches in redistribute_cost computation.
    _input_use_strided: bool | None = None
    for input_strat in input_args_strategy:
        input_spec = input_strat.strategies[0].output_spec
        if any(isinstance(p, _StridedShard) for p in input_spec.placements):
            _input_use_strided = input_spec.use_strided_shard_as_shard_order
            break

    all_strategies = []
    # Track input placements if we skip strategies due to inplace placement mismatch
    blocking_inplace_input_placements: tuple[Placement, ...] | None = None
    for strategy_comb in strategy_combs:
        spec_list: list[DTensorSpec | None] = []
        # Track how many non-None output specs we've seen (for output_tensor_meta indexing).
        # This is needed because output_tensor_meta may contain only non-None entries,
        # so we can't use position directly when there are None entries in the output.
        output_spec_count = 0
        # Track input args separately since not all tensor inputs have OpStrategy
        # (e.g., philox_seed/offset in SDPA are scalar tensors without OpStrategy)
        input_strategy_counter = 0
        for position, specs in enumerate(zip(*strategy_comb, strict=True)):
            if specs[0] is not None:
                # Populate tensor_meta field for both output and input specs,
                # including for tuple output cases
                tensor_meta = None
                # Use position to determine output vs input territory
                # (position includes None entries, unlike the old spec_index)
                if position < input_index:
                    # This is an output position
                    if output_tensor_meta is not None:
                        if isinstance(output_tensor_meta, TensorMeta):
                            tensor_meta = output_tensor_meta
                        elif isinstance(output_tensor_meta, (tuple, list)):
                            if output_spec_count < len(output_tensor_meta):
                                tensor_meta = output_tensor_meta[output_spec_count]
                    output_spec_count += 1
                else:
                    # This is an input position
                    # Only get tensor_meta if we have a corresponding input_args_strategy entry
                    if input_strategy_counter < len(input_args_strategy):
                        tensor_meta = input_args_strategy[
                            input_strategy_counter
                        ].tensor_meta
                        input_strategy_counter += 1

                # pyrefly: ignore [bad-argument-type]
                use_strided = (
                    _input_use_strided
                    if _input_use_strided is not None
                    and any(isinstance(p, _StridedShard) for p in specs)
                    else None
                )
                spec_list.append(
                    DTensorSpec(
                        mesh,
                        specs,
                        tensor_meta=tensor_meta,
                        use_strided_shard_as_shard_order=use_strided,
                    )
                )
            else:
                spec_list.append(None)

        # Skip strategy combinations that would create mixed partial types
        # (except sum+avg which commute with each other).
        # We check (type, reduce_op) pairs rather than just reduce_op because
        # Partial subclasses like _MaskPartial have different reduction semantics
        # even when they share the same reduce_op string.
        has_mixed_partial = False
        for spec in spec_list:
            if spec is not None:
                partial_kinds = {
                    (type(p), p.reduce_op)
                    for p in spec.placements
                    if isinstance(p, Partial)
                }
                if len(partial_kinds) > 1:
                    reduce_ops = {ro for _, ro in partial_kinds}
                    types = {t for t, _ in partial_kinds}
                    if not (len(types) == 1 and reduce_ops == {"sum", "avg"}):
                        has_mixed_partial = True
                        break
        if has_mixed_partial:
            continue

        input_specs: list[DTensorSpec] = [
            s for s in spec_list[input_index:] if isinstance(s, DTensorSpec)
        ]

        if len(input_specs) != len(input_args_strategy):
            raise AssertionError(
                f"input_specs({len(input_specs)}) != strategies({len(input_args_strategy)}: "
                f"{len(args_strategy)} args + {len(kwargs_strategy)} kwargs)"
            )

        # Note [Multi-mesh args]
        #
        # Some ops accept args whose DTensor lives on a different DeviceMesh
        # than the op's primary compute mesh.  We call these "multi-mesh
        # args".  They arise in fused optimizer ops (e.g. _fused_adam_)
        # where *state_steps* is a per-rank scalar counter allocated on a
        # smaller sub-mesh (e.g. 1-D DP) while params and grads live on a
        # larger mesh (e.g. 2-D DP × TP).
        #
        # Why must these args be Replicate?
        #   Sharding implies a specific partitioning of a tensor's data
        #   across the ranks of a mesh.  If a tensor doesn't even *exist*
        #   on the compute mesh, there is no meaningful way to interpret a
        #   Shard placement for it.  Replicate, on the other hand, is
        #   mesh-agnostic: every rank already holds the full data, so the
        #   op can simply read the value regardless of which mesh owns it.
        #
        # What we do here:
        #   We preserve the original mesh and Replicate placement for these
        #   args so the propagator does not try to redistribute them onto
        #   the compute mesh (which would fail or produce wrong results).
        #
        # This is distinct from the *element_mesh* handling in
        # single_dim_strategy.py, which deals with foreach ops where
        # different *elements* in a tensor list may live on different
        # sub-meshes (e.g. param group A on 2-D mesh, param group B on
        # 1-D mesh).
        # TODO: refactor fused_ops handling so that there are no longer
        # args on different meshes
        if different_mesh_args is not None:
            for idx in different_mesh_args:
                if idx < len(input_args_strategy):
                    cross_mesh_input = input_args_strategy[idx]
                    original_spec = cross_mesh_input.strategies[0].output_spec
                    if original_spec.mesh != mesh:
                        if not all(p == Replicate() for p in original_spec.placements):
                            raise RuntimeError(
                                f"Cross-mesh input at index {idx} must be Replicate, "
                                f"but got {original_spec.placements}"
                            )
                        input_specs[idx] = DTensorSpec(
                            mesh=original_spec.mesh,
                            placements=original_spec.placements,
                            tensor_meta=original_spec.tensor_meta,
                        )
        self_spec = input_args_strategy[0].strategies[0].output_spec

        redistribute_input = self_spec.placements != input_specs[0].placements
        mismatching_input_output = (
            spec_list[0] is not None and spec_list[0].placements != self_spec.placements
        )
        if inplace_op and (redistribute_input or mismatching_input_output):
            # For inplace ops, both the proposed input[0] and the output must
            # match self's runtime placement: input[0] because self can't be
            # redistributed, output because the result IS self.
            if blocking_inplace_input_placements is None:
                blocking_inplace_input_placements = self_spec.placements
            continue

        # For out= variant ops, output placement must match the "out" kwarg's placement
        if (
            op_schema.is_out_variant_op()
            and "out" in op_schema.kwargs_schema
            and isinstance(op_schema.kwargs_schema["out"], OpStrategy)
        ):
            out_kwarg_spec = op_schema.kwargs_schema["out"].strategies[0].output_spec
            # spec_list[0] is the output spec for this strategy combination
            if spec_list[0] is not None:
                if spec_list[0].placements != out_kwarg_spec.placements:
                    continue

        output_specs: tuple[DTensorSpec | None, ...] | DTensorSpec | None
        if input_index == 0:
            # No outputs (e.g., _linalg_check_errors)
            output_specs = None
        elif input_index > 1:
            output_specs = tuple(spec_list[:input_index])
        else:
            if spec_list[0] is not None:
                output_specs = spec_list[0]
            else:
                raise RuntimeError("output spec is None")

        # check all inputs are shardable
        if not all(
            is_tensor_shardable(
                inp.shape, s, allow_unbacked_sharding=allow_unbacked_sharding
            )
            or (
                allow_uneven_sharding
                and inp.strategies[0].output_spec.placements == s.placements
            )
            for inp, s in zip(input_args_strategy, input_specs)
        ):
            continue

        # perform additional op-specific filtering
        # Skip callback for no-output ops (output_specs is None)
        if is_valid_strategy_cb is not None and output_specs is not None:
            if not is_valid_strategy_cb(input_specs, output_specs):
                continue

        redistribute_cost = [
            generate_redistribute_costs(input_strategy, input_spec)
            for input_strategy, input_spec in zip(input_args_strategy, input_specs)
        ]

        strategy = OpSpec(
            output_specs=output_specs,
            input_specs=input_specs,
            redistribute_cost=redistribute_cost,
        )
        all_strategies.append(strategy)

    # If all strategies were filtered out due to inplace placement mismatch,
    # raise a clear error message instead of returning an empty OpStrategy
    # (which would later cause a cryptic "min() arg is an empty sequence" error)
    if not all_strategies and blocking_inplace_input_placements is not None:
        raise RuntimeError(
            f"{op_schema.op}: in-place operations that require placement changes "
            f"are not supported. The input has placement {blocking_inplace_input_placements}, "
            f"but no valid strategy preserves this placement. "
            f"Please use the out-of-place version of this operation instead."
        )

    return OpStrategy(all_strategies)