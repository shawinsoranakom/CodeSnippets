def is_tensor_shardable(
    shape: Sequence[int],
    spec: DTensorSpec,
    allow_unbacked_sharding: bool | None = None,
) -> bool:
    """
    Check if the shape is shardable according to the spec.

    This function handles both `Shard` and `_StridedShard` placements:
    - For `Shard`: checks if the tensor dimension size >= number of shards
    - For `_StridedShard`: additionally checks if the dimension is shardable after
      splitting with the placement's `split_factor`

    allow_unbacked_sharding: determines the fallback value if unbacked shapes are involved,
    and the queried shape properties are not statically known.

    e.g. when asking if u0 is shardable on num_shards, and u0 has generic bounds [0, inf],
    the behavior of allow_unbacked_sharding is:

        None: will data-dependent error
        True: assumes shardability; we return True, allowing zero-size shards at runtime when u0 < num_shards.
        False: returns False, and lower-bounding u0, e.g. torch._check(u0 >= num_shards), is needed to enable sharding.
    """
    from torch.fx.experimental.symbolic_shapes import guard_or_false, guard_or_true

    if allow_unbacked_sharding not in [None, True, False]:
        raise AssertionError
    guard_fn = {
        None: bool,
        True: guard_or_false,
        False: guard_or_true,
    }[allow_unbacked_sharding]

    # number of shards in each tensor dimension
    num_shards = [1] * len(shape)
    for i, placement in enumerate(spec.placements):
        if _is_shard_like(placement):
            shard_dim = placement.dim
            if shard_dim >= len(shape):
                return False
            num_shards[shard_dim] *= spec.mesh.size(i)
            if isinstance(placement, _StridedShard):
                # make sure tensor dim `shard_dim` is shardable after splitting
                # with split_factor
                if guard_fn(
                    shape[shard_dim] < num_shards[shard_dim] * placement.split_factor
                ):
                    return False
            else:
                if guard_fn(shape[shard_dim] < num_shards[shard_dim]):
                    return False

    return True