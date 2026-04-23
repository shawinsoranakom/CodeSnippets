def try_create_flattened(
        infos: list[_TransformInfo],
    ) -> tuple[_FlattenedTransformInfo | None, str | None]:
        """
        Try to create a flattened transform from 2+ same-type transforms.

        Returns (result, failure_reason) where:
        - result is the FlattenedTransformInfo if successful, None otherwise
        - failure_reason is None if successful, or one of:
          - "too_few_transforms": Less than 2 transforms provided
          - "no_flattened_mesh": No flattened mesh exists for the required dimensions
          - "uneven_tensor_shape": For reduce_scatter, tensor dim not evenly divisible
        """
        if len(infos) < 2:
            return None, "too_few_transforms"

        # All transforms must have mergeable src_dst_placements
        # (e.g., can't merge Partial->Shard(0) with Partial->Shard(1))
        first_placements = infos[0].src_dst_placements
        comm_type = infos[0]._comm_type_key()
        if not all(
            are_placements_mergeable(info.src_dst_placements, first_placements)
            for info in infos
        ):
            raise AssertionError(
                "All transforms must have mergeable src_dst_placements"
            )
        mesh_dims = tuple(info.mesh_dim for info in infos)
        sorted_mesh_dims = tuple(sorted(mesh_dims))

        # For reduce_scatter and all_gather, order matters for correctness.
        # Flattened meshes only exist for ascending dim order.
        if comm_type == "reduce_scatter":
            # For reduce_scatter: the transform order determines the operation sequence.
            # If transforms are in order (1, 0) but flattened mesh is (0, 1), we can't flatten.
            if mesh_dims != sorted_mesh_dims:
                return None, "non_ascending_mesh_dims"
        elif comm_type == "all_gather":
            # For all_gather: transforms come from planner in innermost-to-outermost order
            # (descending mesh dims for ascending shard order). If transforms are not in
            # descending order, the shard order isn't ascending and we can't flatten.
            if mesh_dims != sorted_mesh_dims[::-1]:
                return None, "non_ascending_mesh_dims"
        # Use sorted dims for mesh lookup (required by DeviceMesh API)
        flattened_mesh = _get_flattened_mesh_by_layout(device_mesh, sorted_mesh_dims)
        if flattened_mesh is None:
            return None, "no_flattened_mesh"

        # For nested sharding, each transform has a different logical_shape.
        # We need the outermost transform's logical_shape, which represents the
        # tensor shape before any of the transforms in this group are applied.
        # The outermost transform has the largest logical_shape on the affected
        # tensor dimension (least divided by prior shards).
        src, dst = first_placements
        if comm_type == "all_gather":
            # S->R (all_gather): affected dim is the source shard dim
            affected_dim = cast(Shard, src).dim
            outermost_info = max(infos, key=lambda x: x.logical_shape[affected_dim])
        elif comm_type == "reduce_scatter":
            affected_dim = cast(Shard, dst).dim
            outermost_info = max(infos, key=lambda x: x.logical_shape[affected_dim])
            tensor_dim_size = outermost_info.logical_shape[affected_dim]
            effective_shard_mesh_size = math.prod(
                device_mesh.size(info.mesh_dim) for info in infos
            )
            # For reduce_scatter (Partial -> Shard), we cannot flatten if the tensor
            # dimension is not evenly divisible by the flattened mesh size.
            # The effective size is the product of mesh sizes for dims being transformed
            # (not all dims with matching placement - intervening shards are already
            # accounted for in logical_shape).
            if tensor_dim_size % effective_shard_mesh_size != 0:
                return None, "uneven_tensor_shape"
        elif comm_type == "all_reduce":
            # no shape change, any info works
            outermost_info = infos[0]
        else:
            raise NotImplementedError(
                f"Unsupported comm type for try_create_flattened: {comm_type}"
            )

        # For mixed sum/avg partials: use sum for the collective, compute avg scale
        avg_scale = None
        merged_src = src
        if src.is_partial():
            scale = math.prod(
                device_mesh.size(info.mesh_dim)
                for info in infos
                if cast(Partial, info.src_dst_placements[0]).reduce_op == "avg"
            )
            if scale > 1:
                avg_scale = scale
                merged_src = Partial("sum")

        merged_placements = (merged_src, dst)

        return (
            _FlattenedTransformInfo(
                mesh_dim=0,
                src_dst_placements=merged_placements,
                logical_shape=outermost_info.logical_shape,
                mesh=flattened_mesh,
                original_mesh_dims=sorted_mesh_dims,
                avg_scale=avg_scale,
            ),
            None,
        )