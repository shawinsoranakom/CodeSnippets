def _query_dtensor_rules(
    aten_op: OpOverload | None,
    tensors: list[tuple[str, torch.Tensor]],
    captured_args: tuple[Any, ...],
    captured_kwargs: dict[str, Any],
    input_shapes: tuple[tuple[int, ...], ...],
    output_shapes: tuple[tuple[int, ...], ...],
    world_size: int,
    verbose: bool,
) -> set[ComboKey]:
    """Query DTensor's claimed sharding rules via single-dim, op_strategy, or decomp paths.

    TODO: This reimplements strategy resolution logic from ShardingPropagator.
    Refactor ShardingPropagator to expose a public API for querying sharding
    rules given an op and tensor metadata, so this function can be replaced
    with a single call.
    """
    if not aten_op:
        return set()

    num_tensors = len(tensors)
    non_tensor_kwargs = {
        k: v for k, v in captured_kwargs.items() if not isinstance(v, torch.Tensor)
    }
    n_outputs = len(output_shapes)
    propagator = DTensor._op_dispatcher.sharding_propagator
    rules: set[ComboKey] = set()

    if aten_op in propagator.op_single_dim_strategy_funcs:
        strategy_result = query_single_dim_strategy(
            aten_op, captured_args, captured_kwargs
        )
        if strategy_result:
            for combo in strategy_result:
                if len(combo) >= n_outputs + num_tensors:
                    output_plcs = combo[:n_outputs]
                    input_plcs = tuple(combo[n_outputs : n_outputs + num_tensors])
                    rule_key: ComboKey = (
                        tuple(str(p) for p in input_plcs),
                        tuple(str(p) for p in output_plcs),
                    )
                    normalized_rule = normalize_combo_key(
                        rule_key, input_shapes, output_shapes
                    )
                    if not is_fully_replicated(
                        tuple(
                            parse_placement(p) or Replicate()
                            for p in normalized_rule[0]
                        )
                    ):
                        rules.add(normalized_rule)

    elif aten_op in propagator.op_strategy_funcs:
        try:
            mesh = init_device_mesh("cpu", (world_size,))
            # Build OpStrategy objects for each tensor, keyed by identity
            tensor_to_strategy: dict[int, OpStrategy] = {}
            for _, t in tensors:
                input_placements = get_1d_input_placements_for_tensor(
                    t, include_partial=True
                )
                specs = []
                for p in input_placements:
                    spec = DTensorSpec(
                        mesh=mesh,
                        placements=(p,),
                        tensor_meta=TensorMeta(
                            shape=t.shape, stride=t.stride(), dtype=t.dtype
                        ),
                    )
                    specs.append(OpSpec(output_specs=spec, input_specs=tuple()))
                tensor_to_strategy[id(t)] = OpStrategy(specs)
            # Interleave strategies and non-tensor args at original positions
            args_schema = [
                tensor_to_strategy[id(a)] if isinstance(a, torch.Tensor) else a
                for a in captured_args
            ]
            op_schema = OpSchema(aten_op, tuple(args_schema), non_tensor_kwargs)
            strategy_func = propagator.op_strategy_funcs[aten_op]
            output_strategy = strategy_func(op_schema)
            rules |= _extract_rules_from_op_strategy(
                output_strategy, input_shapes, output_shapes
            )
        except Exception as e:
            if verbose:
                print(f"        Error querying op_strategy: {e}")

    else:
        # Decomp-based strategy: only discovers rules reachable from a single
        # seed (Shard(0) on the first input). Rules requiring other input
        # placements (e.g., Shard(1), Partial, or sharding on non-first inputs)
        # will not be found, so this under-reports DTensor's capabilities.
        if DecompShardingStrategy.has_decomp(aten_op):
            try:
                mesh = init_device_mesh("cpu", (world_size,))
                # Interleave DTensorSpec and non-tensor args at original positions
                tensor_idx = 0
                args_schema: list[Any] = []
                for a in captured_args:
                    if isinstance(a, torch.Tensor):
                        # First tensor gets Shard(0) to seed candidate
                        # placement generation in _get_candidate_placements
                        plc = Shard(0) if tensor_idx == 0 else Replicate()
                        spec = DTensorSpec(
                            mesh=mesh,
                            placements=(plc,),
                            tensor_meta=TensorMeta(
                                shape=a.shape, stride=a.stride(), dtype=a.dtype
                            ),
                        )
                        args_schema.append(spec)
                        tensor_idx += 1
                    else:
                        args_schema.append(a)
                op_schema = OpSchema(aten_op, tuple(args_schema), non_tensor_kwargs)
                propagator.decomp_strategy.ensure_schema_info(aten_op)
                output_strategy = propagator.decomp_strategy.propagate_strategy(
                    op_schema,
                )
                if output_strategy is not None:
                    rules |= _extract_rules_from_op_strategy(
                        output_strategy, input_shapes, output_shapes
                    )
            except Exception as e:
                if verbose:
                    print(f"        Error querying decomp strategy: {e}")

    return rules