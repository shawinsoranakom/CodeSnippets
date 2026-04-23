def _get_neighbor_placements(
    allowed_sharding: set[Shard | _StridedShard],
    allowed_partial: set[Placement],
    current: Placement,
    input_placements: tuple[Placement, ...],
    mesh_dim: int,
) -> list[Placement]:
    """Return valid one-shot placement transitions for one input on one mesh dim.

    DTensor placements are applied left-to-right, so a tensor dim sharded on
    multiple mesh dims has a specific nesting order. A one-shot collective on
    mesh_dim M can only produce the correct data layout if no mesh dim to the
    RIGHT of M already shards the same tensor dim. For example, going from
    (R, S(0)) to (S(0), S(0)) via local chunk on mesh dim 0 produces a
    strided-shard layout, not the correct left-to-right (S(0), S(0)) layout.

    Transition rules:
    - Replicate -> Shard(d): free local chunk, valid if d not sharded to the right
    - Replicate -> Partial: local view, always valid
    - Shard(d) -> Replicate: allgather, valid if d not sharded to the right
    - Shard(d1) -> Shard(d2): all-to-all, valid if neither d1 nor d2 sharded right
    - Partial -> Replicate: allreduce, always valid
    - Partial -> Shard(d): reduce-scatter, valid if d not sharded to the right
    """
    # Note: circular import
    from torch.distributed.tensor.placement_types import Partial

    # Tensor dims sharded by mesh dims to the right of this one.
    right_shard_dims: set[int] = set()
    for i in range(mesh_dim + 1, len(input_placements)):
        p = input_placements[i]
        if _is_sharding(p):
            right_shard_dims.add(p.dim)

    neighbors: list[Placement] = []

    if isinstance(current, Replicate):
        neighbors.extend(s for s in allowed_sharding if s.dim not in right_shard_dims)
        neighbors.extend(allowed_partial)

    elif _is_sharding(current):
        cur_dim_ok = current.dim not in right_shard_dims
        if cur_dim_ok:
            neighbors.append(Replicate())
        for s in allowed_sharding:
            if s != current and cur_dim_ok and s.dim not in right_shard_dims:
                neighbors.append(s)

    elif isinstance(current, Partial):
        neighbors.append(Replicate())
        neighbors.extend(s for s in allowed_sharding if s.dim not in right_shard_dims)

    return neighbors