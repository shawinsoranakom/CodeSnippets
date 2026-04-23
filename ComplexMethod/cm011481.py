def _dijkstra_expand_single_dim_strategy_to_mesh(
    mesh: DeviceMesh,
    op_schema: OpSchema,
    single_dim_strategy: _SingleDimStrategyInfo
    | Callable[
        [OpOverload, ArgsType, KwargsType], list[list[Placement | _ShardingPlaceholder]]
    ],
    output_tensor_meta: TensorMeta | Sequence[TensorMeta | None] | None = None,
    _collect_all_matches: set[tuple[tuple[Placement, ...], ...]] | None = None,
) -> OpStrategy | None:
    """
    Find the lowest cost sharding for the given op_schema.

    Uses a Dijkstra-like priority-queue search over input placement states. Each
    state is a tuple of per-input placement tuples, and neighbors are generated
    by changing one placement on one mesh dim for one input. The search
    terminates when a state matches a single-dim strategy on every mesh dim.

    This avoids the O(S^N) exhaustive expansion of _expand_single_dim_strategy_to_mesh
    (S = single-dim strategies, N = mesh dims).  Benchmarks with mm on fake
    process groups show:

        1D(4):     S^N=8,   avg 0.2ms
        2D(2,2):   S^N=64,  avg 2.3ms
        3D(2,2,2): S^N=512, avg 41ms, worst 392ms

    The step count is small (avg 0.6-2.0 pops) but per-step cost is dominated
    by cost computation.  Each transition computes an incremental cost via
    _compute_placement_transition_cost for the single changed placement, matching
    the per-step costs used by graph-based transform info planning.

    Returns None if any input has _StridedShard placement, signaling the caller
    to fall back to full expansion.

    Args:
        _collect_all_matches: Testing-only. When non-None, exhaustively explores the
            full transition graph, adding every shardable match to the set. Still
            returns the optimal (first) match.
    """
    # Extract input DTensorSpecs from OpStrategy-wrapped args.
    # Fall back for TupleStrategy (e.g. index tensors in index_put) since the PQ
    # search doesn't model variable-length tuple inputs.
    input_specs: list[DTensorSpec] = []
    for arg in op_schema.args_schema:
        if isinstance(arg, OpStrategy):
            if len(arg.strategies) != 1:
                raise AssertionError
            input_specs.append(arg.strategies[0].output_spec)
        elif isinstance(arg, TupleStrategy):
            return None

    # Fall back if any kwargs are tensor inputs — the PQ search only tracks
    # positional tensor args and would miss redistribute costs for kwargs.
    for kwarg in op_schema.kwargs_schema.values():
        if isinstance(kwarg, (OpStrategy, TupleStrategy)):
            return None

    if len(input_specs) == 0:
        raise AssertionError("broken input")
    num_inputs = len(input_specs)

    # Fall back to full expansion if any input has _StridedShard or symbolic shapes
    # (symbolic shapes produce SymFloat costs that can't be compared in the PQ)
    for spec in input_specs:
        if any(isinstance(p, _StridedShard) for p in spec.placements):
            return None
        if spec.tensor_meta is not None and any(
            isinstance(s, torch.SymInt) for s in spec.tensor_meta.shape
        ):
            return None

    prepared_strategy = _PreparedSingleDimStrategy(
        single_dim_strategy, op_schema, output_tensor_meta, num_inputs=num_inputs
    )

    initial_placements = tuple(spec.placements for spec in input_specs)
    first_result: OpStrategy | None = None

    # Fast path: if initial placements already match a strategy, skip search
    fast_result = prepared_strategy.try_propagate(mesh, initial_placements, input_specs)
    if fast_result is not None:
        fast_result._pq_transitions = []  # type: ignore[attr-defined]
        if _collect_all_matches is not None:
            _collect_all_matches.add(initial_placements)
            first_result = fast_result
        else:
            return fast_result

    # Pre-compute mesh topology and per-input comm bytes for cost computation.
    # comm_bytes_gb reflects the local shard size given current placements;
    # it's tracked per PQ entry and updated as placements change.
    mesh_topo = MeshTopoInfo.build_from_mesh(mesh)
    initial_comm_bytes_gb: list[float] = []
    for spec in input_specs:
        if spec.tensor_meta is None:
            raise AssertionError
        total_bytes = spec.tensor_meta.dtype.itemsize * math.prod(
            spec.tensor_meta.shape
        )
        # TODO: is_shard() misses _StridedShard, use spec.num_shards instead.
        # Not fixing yet: the overestimate biases Dijkstra toward redistributing
        # away from _StridedShard, which is the safer default until _StridedShard
        # is fully validated.
        num_shards = 1
        for i, p in enumerate(spec.placements):
            if p.is_shard():
                num_shards *= mesh_topo.mesh_dim_devices[i]
        initial_comm_bytes_gb.append(total_bytes / num_shards / (1024**3))

    pq: list[_PQEntry] = []
    visited: set[tuple[tuple[Placement, ...], ...]] = set()
    next_counter = count()

    initial_per_input_costs = (0.0,) * num_inputs
    initial_per_input_comm_bytes = tuple(initial_comm_bytes_gb)
    heapq.heappush(
        pq,
        _PQEntry(
            0.0,
            next(next_counter),
            initial_placements,
            [],
            initial_per_input_costs,
            initial_per_input_comm_bytes,
        ),
    )

    def _push_neighbor(
        input_idx: int,
        mesh_dim: int,
        new_placement: Placement,
        source: _PQEntry,
    ) -> None:
        new_input_placements = [list(ps) for ps in source.placements]
        old_placement = new_input_placements[input_idx][mesh_dim]
        new_input_placements[input_idx][mesh_dim] = new_placement
        candidate_placements = tuple(tuple(ps) for ps in new_input_placements)
        if candidate_placements in visited:
            return
        # Check that the NET transition (original -> proposed) is feasible.
        # Individual hops may each be valid (e.g. S->R then R->P) while the
        # net redistribution (S->P) is unsupported by the runtime planner.
        original_p = initial_placements[input_idx][mesh_dim]
        net_cost, _ = _compute_placement_transition_cost(
            original_p,
            new_placement,
            mesh_topo,
            mesh_dim,
            initial_comm_bytes_gb[input_idx],
        )
        if net_cost == float("inf"):
            return
        step_cost, new_comm_bytes = _compute_placement_transition_cost(
            old_placement,
            new_placement,
            mesh_topo,
            mesh_dim,
            source.per_input_comm_bytes_gb[input_idx],
        )
        if step_cost == float("inf"):
            return
        changed_cost = source.per_input_costs[input_idx] + step_cost
        new_per_input_costs = (
            source.per_input_costs[:input_idx]
            + (changed_cost,)
            + source.per_input_costs[input_idx + 1 :]
        )
        new_per_input_comm_bytes = (
            source.per_input_comm_bytes_gb[:input_idx]
            + (new_comm_bytes,)
            + source.per_input_comm_bytes_gb[input_idx + 1 :]
        )
        new_cost = sum(new_per_input_costs)
        new_transitions = source.transitions + [
            (input_idx, mesh_dim, old_placement, new_placement)
        ]
        heapq.heappush(
            pq,
            _PQEntry(
                new_cost,
                next(next_counter),
                candidate_placements,
                new_transitions,
                new_per_input_costs,
                new_per_input_comm_bytes,
            ),
        )

    while pq:
        candidate = heapq.heappop(pq)

        if candidate.placements in visited:
            continue
        visited.add(candidate.placements)

        match_result = prepared_strategy.try_propagate(
            mesh, candidate.placements, input_specs
        )
        if match_result is not None:
            # Use pre-computed per-input costs from the PQ search instead of
            # recomputing via generate_redistribute_costs -> _gen_transform_infos.
            match_spec = match_result.strategies[0]
            if match_spec.input_specs is None:
                raise AssertionError
            op_spec = OpSpec(
                output_specs=match_spec.output_specs,
                input_specs=list(match_spec.input_specs),
                redistribute_cost=[[cost] for cost in candidate.per_input_costs],
            )

            exhaustive = len(prepared_strategy.expanded_strategies) ** mesh.ndim
            logger.debug(
                "returning cost=%f %s, visited=%d, exhaustive=%d, transitions=%s",
                candidate.cost,
                op_spec,
                len(visited),
                exhaustive,
                candidate.transitions,
            )
            result = OpStrategy([op_spec])
            result._pq_transitions = candidate.transitions  # type: ignore[attr-defined]
            if _collect_all_matches is not None:
                _collect_all_matches.add(candidate.placements)
                if first_result is None:
                    first_result = result
            else:
                return result

        # Generate neighbor states
        for mesh_dim in range(mesh.ndim):
            for input_idx in range(len(candidate.placements)):
                current_p = candidate.placements[input_idx][mesh_dim]
                for neighbor_p in _get_neighbor_placements(
                    prepared_strategy.allowed_sharding_per_input[input_idx],
                    prepared_strategy.allowed_partial_per_input[input_idx],
                    current_p,
                    candidate.placements[input_idx],
                    mesh_dim,
                ):
                    _push_neighbor(input_idx, mesh_dim, neighbor_p, candidate)

    if _collect_all_matches is not None and first_result is not None:
        return first_result

    logger.warning(
        "Dijkstra search exhausted without finding a valid strategy for "
        "%s on %s (explored %d combinations); falling back to full expansion",
        op_schema,
        mesh,
        len(visited),
    )
    return None