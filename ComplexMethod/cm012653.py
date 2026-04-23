def construct_range_trees(
        self,
        pid_cache: dict[str, str] | None,
        inside_reduction: bool,
        is_reduction: bool,
        numels: dict[str, sympy.Expr],
        no_x_dim: bool,
    ) -> list[IterationRangesRoot]:
        active_prefixes = OrderedSet(
            prefix for prefix in all_prefixes if prefix in numels
        )
        no_r_dim = not inside_reduction or not is_reduction

        def filtered_index_map(seq, mask) -> dict[Any, int]:
            return {
                val: idx for idx, val in enumerate(val for val in seq if val in mask)
            }

        grid_dims = ["x", "y", "z"]
        pointwise_tensor_dims = list(reversed(grid_dims))
        reduction_dims = ["r0_", "r1_"]
        if no_x_dim:
            tensor_dims = reduction_dims
        elif no_r_dim:
            tensor_dims = pointwise_tensor_dims
        else:
            tensor_dims = pointwise_tensor_dims + reduction_dims

        # Filter out unused tensor dims.
        # Convert to dicts for O(1) index lookup.
        tensor_dim_map = filtered_index_map(tensor_dims, active_prefixes)
        grid_dim_map = filtered_index_map(grid_dims, all_prefixes)

        range_trees = []
        for i, prefix in enumerate(active_prefixes):
            is_reduction = prefix_is_reduction(prefix)
            tensor_dim = tensor_dim_map.get(prefix)
            grid_dim = grid_dim_map.get(prefix)
            index = i if grid_dim is None else grid_dim
            range_trees.append(
                IterationRangesRoot(
                    f"{prefix}index",
                    numels[prefix],
                    prefix,
                    index,
                    self,  # type: ignore[arg-type]
                    pid_cache=pid_cache,
                    is_loop=is_reduction and not self.persistent_reduction,
                    tensor_dim=tensor_dim,
                    grid_dim=grid_dim,
                    has_zdim="z" in numels,
                )
            )
        return range_trees