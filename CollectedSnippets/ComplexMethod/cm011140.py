def _validate_mesh(
    mesh: "DeviceMesh",
    dp_mesh_dims: "DataParallelMeshDims | None" = None,
) -> None:
    """
    Validate that the mesh can be used with fully_shard.

    When ``dp_mesh_dims`` is provided, validates that the named dims
    exist in the mesh and at least one of shard/replicate is set.
    Otherwise raises ValueError if the mesh is not 1D or 2D.
    """
    if dp_mesh_dims is not None:
        if dp_mesh_dims.shard is None and dp_mesh_dims.replicate is None:
            raise ValueError(
                "At least one of shard or replicate must be set in dp_mesh_dims"
            )
        if mesh.mesh_dim_names is None:
            raise ValueError(
                "mesh must have mesh_dim_names when dp_mesh_dims is provided"
            )
        names_to_check: list[str] = list(dp_mesh_dims.shard_names)
        names_to_check.extend(dp_mesh_dims.replicate_names)
        for name in names_to_check:
            if name not in mesh.mesh_dim_names:
                raise ValueError(
                    f"Mesh dim name '{name}' not found in mesh.mesh_dim_names "
                    f"{mesh.mesh_dim_names}"
                )
        return
    if mesh.ndim not in (1, 2):
        raise ValueError(f"fully_shard expects a 1D or 2D DeviceMesh but got {mesh}")
    if mesh.ndim == 2 and mesh.mesh_dim_names is None:
        raise AssertionError(
            "Please init the 2D mesh for HSDP with mesh_dim_names specified"
        )