def _maybe_convert_StridedShard_to_shard_order(
        placements: tuple[Placement, ...], mesh: DeviceMesh
    ) -> ShardOrder | None:
        """
        Try to convert _StridedShard placements to ShardOrder.

        This is the inverse of `_convert_shard_order_to_StridedShard`. It reconstructs the shard
        order by examining the split_factor of each _StridedShard and determining its position
        in the execution order. If the _StridedShard configuration cannot be represented as a
        valid ShardOrder (i.e., there's no shard order that produces the observed split_factors),
        this function returns None.

        Args:
            placements: Tuple of Placement objects that may contain _StridedShard.
            mesh: DeviceMesh containing the size information for each mesh dimension.

        Returns:
            ShardOrder if conversion is possible, None otherwise. For placements without
            _StridedShard, returns the default shard order.

          Algorithm:
              1. If no _StridedShard in placements, return default shard order
              2. Create an empty list for each tensor dimension to represent mesh dim ordering
              3. Iterate through placements in reverse order (right to left):
                 - For each Shard/_StridedShard on a tensor dimension:
                   - Extract its split_factor (1 for Shard, split_factor for _StridedShard)
                   - Find the position in mesh_dims_order where accumulated_sf equals split_factor
                   - accumulated_sf is the product of mesh sizes of mesh dimensions that appear
                     earlier in mesh_dims_order (lower indices)
                   - Insert mesh_dim at the found position
              4. If no valid position found for any split_factor, return None (unable to convert)
              5. Construct ShardOrderEntry for each tensor dimension from mesh_dims_order

        Example:
            >>> # xdoctest: +SKIP("Requires DeviceMesh")
            >>> # mesh = DeviceMesh([4, 3, 2])  # sizes: mesh[0]=4, mesh[1]=3, mesh[2]=2
            >>> # placements = (_StridedShard(0, sf=2), _StridedShard(0, sf=2), Shard(0))
            >>> # Process tensor_dim=0 from right to left:
            >>> #   - mesh_dim=2: Shard(0) with sf=1
            >>> #     Try position 0: accumulated_sf=1, matches! Insert at position 0
            >>> #     Current mesh_dims_order order: [2]
            >>> #   - mesh_dim=1: _StridedShard(0, sf=2) with sf=2
            >>> #     Try position 0: accumulated_sf=1, no match
            >>> #     Try position 1: accumulated_sf=1*mesh.size(2)=2, matches! Insert at position 1
            >>> #     Current mesh_dims_order order: [2, 1]
            >>> #   - mesh_dim=0: _StridedShard(0, sf=2) with sf=2
            >>> #     Try position 0: accumulated_sf=1, no match
            >>> #     Try position 1: accumulated_sf=1*mesh.size(2)=2, matches! Insert at position 1
            >>> #     Final mesh_dims_order order: [2, 0, 1]
            >>> # Result: ShardOrder((ShardOrderEntry(tensor_dim=0, mesh_dims=(2, 0, 1)),))
            >>> # This means: first shard on mesh_dim=2, then mesh_dim=0, then mesh_dim=1

        Note:
            This function validates that _StridedShard can be represented as a ShardOrder.
            Not all _StridedShard configurations are valid - the split_factor must match
            the product of mesh sizes in some execution order.
        """
        if not any(isinstance(p, _StridedShard) for p in placements):
            return DTensorSpec.compute_default_shard_order(placements)
        max_tensor_dim = max([i.dim for i in placements if _is_shard_like(i)]) + 1
        shard_order = []

        tensor_dim_to_mesh_dims_order: list[list[int]] = [
            [] for i in range(max_tensor_dim)
        ]
        for mesh_dim in reversed(range(len(placements))):
            cur_placement = placements[mesh_dim]
            if _is_shard_like(cur_placement):
                tensor_dim = cur_placement.dim
                mesh_dims_order = tensor_dim_to_mesh_dims_order[tensor_dim]
                cur_sf = 1
                if isinstance(cur_placement, _StridedShard):
                    cur_sf = cur_placement.split_factor
                accumulated_sf = 1
                find_order = False
                for i in range(len(mesh_dims_order) + 1):
                    if accumulated_sf == cur_sf:
                        mesh_dims_order.insert(i, mesh_dim)
                        find_order = True
                        break
                    if i < len(mesh_dims_order):
                        accumulated_sf *= mesh.size(mesh_dims_order[i])
                if not find_order:
                    # _StridedShard is not convertible to ShardOrder
                    return None
            else:
                if not isinstance(cur_placement, Replicate | Partial | _MaskPartial):
                    raise ValueError(
                        f"Unsupported placement type {type(cur_placement)} encountered in "
                        f"{placements}; expected Replicate, Partial, or _MaskPartial."
                    )
        for tensor_dim in range(max_tensor_dim):
            if len(tensor_dim_to_mesh_dims_order[tensor_dim]) > 0:
                shard_order.append(
                    ShardOrderEntry(
                        tensor_dim=tensor_dim,
                        mesh_dims=tuple(tensor_dim_to_mesh_dims_order[tensor_dim]),
                    )
                )
        return tuple(shard_order)