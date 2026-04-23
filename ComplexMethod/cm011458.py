def visualize_sharding(dtensor, header="", use_rich: bool = False):
    """
    Visualizes sharding in the terminal for :class:`DTensor` that are 1D or 2D.

    .. note:: This requires the ``tabulate`` package, or ``rich`` and ``matplotlib``.
              No sharding info will be printed for empty tensors
    """
    if dtensor.numel() == 0:  # Do not print empty dtensors.
        return

    if len(dtensor.shape) >= 3:
        raise RuntimeError("visualize sharding supports only 1D or 2D DTensor")

    if dtensor.device_mesh.get_coordinate() is None:  # current rank is not in the mesh
        return

    # Only display the visualization once for each DTensor, on the rank whose
    # coordinate is 0 on all dimensions. For example, if the mesh is a full mesh,
    # we will only print on rank 0.
    local_rank_zero_on_all_dim = all(
        dtensor.device_mesh.get_local_rank(mesh_dim=dim) == 0
        for dim in range(dtensor.device_mesh.ndim)
    )
    if not local_rank_zero_on_all_dim:
        return

    device_coords = {
        int(device_index.item()): list(coord)
        for coord, device_index in np.ndenumerate(
            np.array(dtensor.device_mesh.mesh.tolist())
        )
    }

    device_shard_shape_and_offsets = {
        device_index: _compute_local_shape_and_global_offset(
            dtensor.shape,
            dtensor.device_mesh.shape,
            lambda i: device_coords[device_index][i],
            dtensor.placements,
        )
        for device_index in device_coords
    }

    # Extend shards in a 1D tensor to 2D
    device_shard_shape_and_offsets = {
        device_index: (
            shape if len(shape) == 2 else (shape[0], 1),
            offset if len(offset) == 2 else (offset[0], 0),
        )
        for device_index, (shape, offset) in device_shard_shape_and_offsets.items()
    }

    shards = [
        (
            (offset[0], offset[0] + shape[0] - 1),
            (offset[1], offset[1] + shape[1] - 1),
            device_index,
        )
        for device_index, (shape, offset) in device_shard_shape_and_offsets.items()
    ]

    if (
        importlib.util.find_spec("rich")
        and importlib.util.find_spec("matplotlib")
        and use_rich
    ):
        _create_rich_table(
            dtensor.shape, shards, device_kind=dtensor.device_mesh.device_type
        )
    elif importlib.util.find_spec("tabulate"):
        print(_create_table(shards, device_kind=dtensor.device_mesh.device_type))
    else:
        raise ValueError("`visualize_sharding` requires either `rich` or `tabulate`.")