def _partition_val(val: Any, spec: DTensorSpec) -> Any:
    """
    util function to convert a full tensor val to its local component
    """
    if isinstance(val, torch.Tensor):
        local_shard = val
        if val.ndim == 0:
            # If it's already a scalar tensor, it is already local, we don't
            # need to do anything
            return local_shard

        for idx, placement in enumerate(spec.placements):
            # NOTE: is_shard() does not match _StridedShard; see _is_shard_like().
            if placement.is_shard():
                placement = cast(Shard, placement)
                num_chunks = spec.mesh.size(mesh_dim=idx)
                my_coord = spec.mesh.get_coordinate()
                if my_coord is None:
                    raise AssertionError("current rank not in mesh!")
                my_coord_on_mesh_dim = my_coord[idx]
                local_shard = placement._select_split_tensor(
                    local_shard,
                    num_chunks,
                    my_coord_on_mesh_dim,
                    with_padding=False,
                    contiguous=True,
                    clone=False,
                )
        return local_shard
    elif isinstance(val, (list, tuple)):
        return val.__class__(_partition_val(v, spec) for v in val)
    else:
        raise RuntimeError(f"val type {type(val)} not supported")