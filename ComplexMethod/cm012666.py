def get_nd_tilings(
        cls,
        node_schedule,
        pointwise_numel,
        reduction_numel,
    ) -> list[immutable_dict[str, sympy.Expr]]:
        """
        Creates N-dimensional tiling candidates, attempting to simplify loads/stores
        by tiling the kernel into higher dimensions.

        Returns a list of tilings ranked by dimensionality.
        """

        def collapse_dims(
            dims: Sequence[sympy.Expr], fallback_numel: sympy.Expr
        ) -> tuple[sympy.Expr, ...]:
            """
            Collapse dimensions to the maximum allowed number of tiles.
            """
            if not dims:
                return (fallback_numel,)
            max_tiles = get_max_tiles(2)
            if V.graph.sizevars.statically_known_equals(
                pointwise_numel, 1
            ) and V.graph.sizevars.statically_known_gt(reduction_numel, 1):
                # We only have at most two dimensions to tile over when emitting a
                # reduction-only kernel.
                max_tiles = min(max_tiles, 2)
            num_leading_dims = max(0, len(dims) - max_tiles)
            first_trailing_dim = num_leading_dims + 1
            collapsed_leading_dim = sympy_product(dims[:first_trailing_dim])
            return (collapsed_leading_dim,) + tuple(dims[first_trailing_dim:])

        def tile_var_ranges(
            var_ranges, ranges_to_tile, total_numel
        ) -> tuple[sympy.Expr, ...]:
            # Pattern match the subexpression pertaining to each index variable.
            tiling = []
            for var, numel in var_ranges:
                index = BlockPatternMatcher.get_subexpr_involving_symbol(dep.index, var)

                # Heuristic to bound the maximum dimensionality of the block.
                num_dims = max(
                    2,
                    index.count(FloorDiv) + index.count(ModularIndexing),
                    len(ranges_to_tile),
                )

                # Attempt to pattern match the index expr.
                # Failed matches default to the full range.
                match_result = BlockPatternMatcher.match_mod_div_block_expr(
                    index, var, numel, num_dims
                )
                dims = match_result[0] if match_result is not None else [numel]
                tiling.extend(dims)

            # Prune dimensions of size 1.
            tiling = [
                dim
                for dim in tiling
                if not V.graph.sizevars.statically_known_equals(dim, sympy.S.One)
            ]

            return collapse_dims(tiling, total_numel)

        is_pointwise = reduction_numel == 1
        tilings = OrderedSet[immutable_dict[str, sympy.Expr]]()
        for node in EnableReduction.filter(node_schedule):
            if not isinstance(node, scheduler.SchedulerNode):
                continue

            # If this is a reduction schedule, skip nodes which are missing their
            # reduction ranges.
            node_ranges = node.get_ranges()
            if not is_pointwise and len(node_ranges[1]) == 0:
                continue

            # Use the node ranges as the default tiling candidate.
            default_pointwise_tiling = collapse_dims(node_ranges[0], pointwise_numel)
            default_reduction_tiling = collapse_dims(node_ranges[1], reduction_numel)
            node_tilings = [(default_pointwise_tiling, default_reduction_tiling)]

            # Search the indexing expressions for more candidates.
            # If we see modular indexing, try to subdivide ranges into their implied
            # block shape.
            memory_deps = [
                dep
                for dep in node.read_writes.reads_and_writes()
                if isinstance(dep, MemoryDep) and len(dep.ranges) > 0
            ]
            for dep in memory_deps:
                # Attempt to partition variable ranges into pointwise and reduction groups.
                # To achieve this, merge the leading ranges until we reach the pointwise numel.
                all_var_ranges = [*dep.ranges.items()]
                pointwise_vars_numel = sympy.S.One
                sizevars = V.graph.sizevars
                pointwise_end_idx = 0
                for idx, (_var, numel) in enumerate(all_var_ranges):
                    pointwise_vars_numel *= numel
                    pointwise_end_idx = idx
                    if sizevars.statically_known_geq(
                        pointwise_vars_numel, pointwise_numel
                    ):
                        break

                # Reject the split if it does not match the total pointwise numel.
                if not sizevars.statically_known_equals(
                    pointwise_vars_numel, pointwise_numel
                ):
                    continue

                # Partition var ranges into pointwise and reduction splits, tiling them
                # separately.
                reduction_start_idx = pointwise_end_idx + 1
                pointwise_var_ranges = all_var_ranges[:reduction_start_idx]
                reduction_var_ranges = (
                    None if is_pointwise else all_var_ranges[reduction_start_idx:]
                )
                pointwise_tiling = tile_var_ranges(
                    pointwise_var_ranges, node_ranges[0], pointwise_numel
                )
                reduction_tiling = (
                    (sympy.S.One,)
                    if is_pointwise
                    else tile_var_ranges(
                        reduction_var_ranges, node_ranges[1], reduction_numel
                    )
                )

                if len(pointwise_tiling) and len(reduction_tiling) > 0:
                    node_tilings.append((pointwise_tiling, reduction_tiling))

            # Each memory dependency contributes one pointwise and reduction tiling. We
            # take the Cartesian product of these, yielding all possible joint tilings.
            for pointwise_tiling, reduction_tiling in itertools.product(
                *zip(*node_tilings)
            ):
                tilings.add(cls.create_tiling(pointwise_tiling, reduction_tiling))

        # Rank tilings by the number of dimensions. E.g., prefer 2D to 1D.
        # Since this is a stable sort, ties are broken by schedule order.
        ranked_tilings = sorted(
            tilings,
            key=len,
            reverse=True,
        )

        return ranked_tilings