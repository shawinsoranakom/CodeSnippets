def _compute_local_shape_and_global_offset(
    global_shape: ShapeType,
    mesh_shape: ShapeType,
    my_coordinate: list[int] | Callable[[int], RankType] | None,
    placements: Sequence[Placement],
    skip_offset: bool = False,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """
    Suppose you have a full tensor with size global_shape, and you have sharded
    it according to placements for mesh_shape.  This function returns, for a
    specific coordinate my_coordinate in the device mesh:

        - The size of your local shard WITHOUT padding (i.e., if you have
          an uneven split, your size might be smaller than the other entries
          in your dim), and

        - Where the data for your shard begins, in the full tensor.

    This function is fairly simple if your tensor is evenly sharded; the complication
    is around uneven splits.  There is also some complication for handling StridedShard,
    which changes the order you should apply sharding.

    Args:
        global_shape (ShapeType): The global shape of the tensor.
        mesh_shape (ShapeType): The shape of the device mesh.
        my_coordinate (Optional[list[int]]): The coordinate of the current rank in the device mesh.
        placements (Sequence[Placement]): The placements of the DTensor.
        skip_offset (bool): If True, skip computing the global offsets and return an empty
            tuple for global_offset. This can improve performance when only the local shape
            is needed. Defaults to False.

    Returns:
        tuple: A tuple containing:
            - local_shape (tuple[int, ...]): The shape of the local shard on the current rank.
            - global_offset (tuple[int, ...]): The offsets for each dimension identifying where
              this shard begins in the global tensor. If skip_offset is True, this will be an
              empty tuple.
    """

    if isinstance(my_coordinate, (list, tuple)):
        _coord: list | tuple = my_coordinate

        def coordinate_lookup(dim: int) -> RankType:
            return _coord[dim]
    else:
        if my_coordinate is None:
            raise AssertionError
        coordinate_lookup = my_coordinate

    local_shape = list(global_shape)
    # Perform shard from left to right. For example,
    #   global tensor: [0, 1, 2, 3, 4, 5, 6, 7]
    #   placements: S(0), SS(0, split_factor=2)
    #   mesh_shape: (2, 2)
    # After S(0), shard_dim_to_global_offsets are
    #   {0: [0, 1, 2, 3]} on my_coordinate [0, 0] [0, 1]
    #   {0: [4, 5, 6, 7]} on my_coordinate [1, 0] [1, 1]
    # After SS(0, split_factor=2), shard_dim_to_global_offsets are
    #   {0: [0, 2]} on my_coordinate [0, 0]
    #   {0: [1, 3]} on my_coordinate [0, 1]
    #   {0: [4, 6]} on my_coordinate [1, 0]
    #   {0: [5, 7]} on my_coordinate [1, 1]
    shard_dim_to_global_offsets = {}
    for mesh_dim, placement in enumerate(placements):
        if not isinstance(placement, (Shard, _StridedShard)):
            continue
        shard_dim = placement.dim
        zero_global_offset = global_shape[shard_dim]
        if shard_dim >= len(local_shape):
            raise AssertionError(
                f"Sharding dim {shard_dim} greater than tensor ndim {len(local_shape)}"
            )
        previous_offsets = shard_dim_to_global_offsets.get(shard_dim)
        shard_size, shard_offsets = _get_shard_size_and_offsets(
            local_shape[shard_dim],
            mesh_shape[mesh_dim],
            coordinate_lookup(mesh_dim),
            placement,
            previous_offsets,
            zero_global_offset,
            skip_offset,
        )
        local_shape[shard_dim] = shard_size
        shard_dim_to_global_offsets[shard_dim] = shard_offsets
    if skip_offset:
        return tuple(local_shape), ()
    global_offset = [0] * len(global_shape)
    for shard_dim, global_offsets in shard_dim_to_global_offsets.items():
        global_offset[shard_dim] = _get_first_offset(global_offsets)
    return tuple(local_shape), tuple(global_offset)