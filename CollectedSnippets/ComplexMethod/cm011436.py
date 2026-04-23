def _optimize_transform_infos(
    transform_infos: list[_TransformInfo],
    device_mesh: DeviceMesh,
    src_placements: tuple[Placement, ...],
    dst_placements: tuple[Placement, ...],
) -> list[_TransformInfo | _FlattenedTransformInfo]:
    """
    Optimize transform infos by merging consecutive same-type collectives into
    a single flattened operation when a matching flattened DeviceMesh exists.

    Merging requirements:
    - Operations must be consecutive in the transform list (no reordering).
      Notably, redistributing from P, P, P -> R, S, R is not optimized here and cannot be optimized due to
      optimization needing to fuse non-contiguous reductions, leaving this pattern vulnerable to numerics issues and
      suboptimal perf
    - Operations must have the same comm type (e.g., all allgather or all reduce_scatter)
    - Operations must have identical src_dst_placements (e.g., can't merge
      Partial->Shard(0) with Partial->Shard(1))
    - A flattened mesh covering the relevant dimensions must exist
    - For reduce_scatter, tensor dim must be evenly divisible by flattened mesh size

    For nested sharding, the merged operation uses the logical_shape from the
    outermost mesh dimension (smallest mesh_dim index) which represents the
    global tensor shape needed for correct padding/unpadding.

    TODO:
    - all_to_all operations are excluded from merging, but it may be possible to merge them in some cases.

    """
    if len(transform_infos) < 2:
        return transform_infos

    if _DISABLE_REDISTRIBUTE_TRANSFORM_OPTIMIZATION:
        return transform_infos

    # Comm types that are safe to merge (all_to_all excluded for now)
    MERGEABLE_COMM_TYPES = frozenset({"all_gather", "all_reduce", "reduce_scatter"})

    def is_mergeable(key: str | None) -> bool:
        """Check if a comm type key represents a mergeable operation."""
        return key in MERGEABLE_COMM_TYPES

    def are_placements_mergeable(
        p1: tuple[Placement, Placement], p2: tuple[Placement, Placement]
    ) -> bool:
        """
        Check if two src_dst_placements can be merged.

        Allows merging of Partial("sum") and Partial("avg") since they can be
        combined: perform sum reduction, then scale by avg mesh dims afterward.
        """
        if p1 == p2:
            return True

        src1, dst1 = p1
        src2, dst2 = p2

        # Destinations must match exactly
        if dst1 != dst2:
            return False

        # Both sources must be partial
        if not (src1.is_partial() and src2.is_partial()):
            return False

        # Only sum and avg can be merged (both use sum reduction, avg just scales)
        partial1 = cast(Partial, src1)
        partial2 = cast(Partial, src2)
        mergeable_reduce_ops = {"sum", "avg"}
        return (
            partial1.reduce_op in mergeable_reduce_ops
            and partial2.reduce_op in mergeable_reduce_ops
        )

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

    # Merge consecutive same-type operations (without reordering)
    result: list[_TransformInfo | _FlattenedTransformInfo] = []
    i = 0

    while i < len(transform_infos):
        info = transform_infos[i]
        current_key = info._comm_type_key()

        # Only try to merge if this is a mergeable comm type
        if not is_mergeable(current_key):
            result.append(info)
            i += 1
            continue

        # Collect consecutive transforms with mergeable src_dst_placements
        # (not just same comm type - e.g., Partial->Shard(0) vs Partial->Shard(1) can't merge)
        # Note: sum/avg partials can be merged since they use the same reduction
        current_placements = info.src_dst_placements
        group: list[_TransformInfo] = [info]
        j = i + 1
        while (
            j < len(transform_infos)
            and is_mergeable(transform_infos[j]._comm_type_key())
            and are_placements_mergeable(
                transform_infos[j].src_dst_placements, current_placements
            )
        ):
            group.append(transform_infos[j])
            j += 1

        # Try to flatten the group
        flattened, failure_reason = try_create_flattened(group)
        if flattened is not None:
            result.append(flattened)
        else:
            # Can't flatten - add individually and warn once if applicable
            result.extend(group)
            # Warn for reasons that indicate a real optimization opportunity was missed
            if failure_reason in (
                "no_flattened_mesh",
                "uneven_tensor_shape",
                "non_ascending_mesh_dims",
            ):
                mesh_dims = tuple(sorted(g.mesh_dim for g in group))
                _warn_flatten_optimization_not_possible(
                    device_mesh,
                    mesh_dims,
                    src_placements,
                    dst_placements,
                    len(group),
                    current_key,  # type: ignore[arg-type]
                    failure_reason,
                )

        i = j
    logger.debug(
        "_optimize_transform_infos original: %s, optimized: %s", transform_infos, result
    )

    return result