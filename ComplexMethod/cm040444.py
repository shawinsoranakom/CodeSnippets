def _vectorize_update_dim_sizes(dim_sizes, shape, core_dims, is_input=True):
    num_core_dims = len(core_dims)
    if is_input:
        if len(shape) < num_core_dims:
            raise ValueError(
                f"input with shape {shape} does not "
                "have enough dimensions for all core "
                f"dimensions {core_dims}"
            )
    else:
        if len(shape) != num_core_dims:
            raise ValueError(
                f"output shape {shape} does not "
                f"match core dimensions {core_dims}"
            )

    core_shape = shape[-num_core_dims:] if core_dims else ()
    for dim, size in zip(core_dims, core_shape):
        if dim not in dim_sizes:
            dim_sizes[dim] = size
        elif size != dim_sizes[dim]:
            raise ValueError(
                f"inconsistent size for core dimension {dim}: "
                f"{size} vs {dim_sizes[dim]}"
            )