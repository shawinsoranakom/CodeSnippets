def _calc_shard_info(
    mesh_coordinate: Sequence[IntLikeType], spec: DTensorSpec
) -> tuple[list[IntLikeType], list[IntLikeType]]:
    mesh = spec.mesh
    # note: dim_map does not allow double sharding which is the FSDP(fully_shard)+TP
    # case. Replace the custom logic with dim_map once we support it.
    dim_map: list[int | list[int]] = [-1] * spec.ndim
    for i, placement in enumerate(spec.placements):
        if isinstance(placement, Shard | _StridedShard):
            shard_dim = placement.dim
            if dim_map[shard_dim] == -1:
                dim_map[shard_dim] = [i]
            else:
                mesh_dim_list = dim_map[shard_dim]
                if not isinstance(mesh_dim_list, list):
                    raise AssertionError
                mesh_dim_list.append(i)

    # Compute shard coordinate:
    # The coordinate on each tensor dim is a tuple (idx, range)
    # If a DTensor is partitioned on its dim i into n shards, and the current rank
    # holds the j-th, then its shard coordinate will be (idx=j, range=n) on dim i
    mesh_size = mesh.shape
    shard_idx_by_dim = []
    total_num_shards_by_dim: list[
        IntLikeType
    ] = []  # total number of shards on each tensor dim
    for mesh_dim in dim_map:
        shard_idx: IntLikeType = 0
        total_num_shards: IntLikeType = 1
        # the tensor dim is sharded on more than 1 mesh dim
        if isinstance(mesh_dim, list):
            rank_coord = [mesh_coordinate[d] for d in mesh_dim]
            num_shards = [mesh_size[d] for d in mesh_dim]
            # compute the shard idx and total number of shards
            for idx, size in zip(rank_coord, num_shards):
                shard_idx = shard_idx * size + idx
                total_num_shards *= size

        shard_idx_by_dim.append(shard_idx)
        total_num_shards_by_dim.append(total_num_shards)
    return shard_idx_by_dim, total_num_shards_by_dim