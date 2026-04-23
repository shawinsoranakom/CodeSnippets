def test_single_dim_transition_reachability(self):
        """Verify single-dim transition rules form a connected graph.

        For mm on a 2D mesh, collect all placements that appear per input
        position, build a directed graph from transition rules, and BFS from
        each placement to assert all others are reachable.
        """
        from collections import deque

        mesh = DeviceMesh("cpu", mesh=torch.arange(4).reshape(2, 2))
        M, K, N = 64, 32, 64
        left_meta, right_meta = _get_mm_metas(M, K, N)
        output_meta = self._get_mm_output_meta(M, K, N)

        ref_left_spec, ref_right_spec = _get_mm_specs(
            mesh,
            left_meta,
            right_meta,
            left_placements=(Replicate(), Replicate()),
            right_placements=(Replicate(), Replicate()),
        )
        wrapped_schema = OpSchema(
            op=torch.ops.aten.mm.default,
            args_schema=(
                OpStrategy([OpSpec(ref_left_spec)]),
                OpStrategy([OpSpec(ref_right_spec)]),
            ),
            kwargs_schema={},
        )
        expanded_fn = _expand_single_dim_strategy_to_mesh(
            mesh,
            wrapped_schema,
            _SingleDimStrategyInfo(mm_single_dim_strategy),
            output_meta,
        )
        ref_strategy = expanded_fn(
            torch.ops.aten.mm.default,
            wrapped_schema.args_meta,
            wrapped_schema.kwargs_meta,
        )

        # Collect all placements per input position per mesh dim
        for input_idx in range(2):
            for mesh_dim in range(mesh.ndim):
                all_placements: set[Placement] = set()
                for s in ref_strategy.strategies:
                    all_placements.add(s.input_specs[input_idx].placements[mesh_dim])

                # Build directed graph from transition rules
                def is_sharding(p: Placement) -> bool:
                    return isinstance(p, Shard)

                edges: dict[Placement, set[Placement]] = {
                    p: set() for p in all_placements
                }
                for src in all_placements:
                    for dst in all_placements:
                        if src == dst:
                            continue
                        # R -> S, R -> P (free)
                        if isinstance(src, Replicate) and (
                            is_sharding(dst) or isinstance(dst, Partial)
                        ):
                            edges[src].add(dst)
                        # S -> R (allgather), S -> S' (all-to-all)
                        if is_sharding(src) and (
                            isinstance(dst, Replicate) or is_sharding(dst)
                        ):
                            edges[src].add(dst)
                        # P -> R (allreduce), P -> S (reduce-scatter)
                        if isinstance(src, Partial) and (
                            isinstance(dst, Replicate) or is_sharding(dst)
                        ):
                            edges[src].add(dst)

                # BFS from each placement, assert all others reachable
                for start in all_placements:
                    visited: set[Placement] = set()
                    q = deque([start])
                    while q:
                        node = q.popleft()
                        if node in visited:
                            continue
                        visited.add(node)
                        q.extend(edges.get(node, set()))
                    self.assertEqual(
                        visited,
                        all_placements,
                        f"input_idx={input_idx}, mesh_dim={mesh_dim}: "
                        f"from {start}, unreachable: {all_placements - visited}",
                    )