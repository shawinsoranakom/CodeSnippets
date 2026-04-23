def patched_dim_method(wrapper: WrappedOperator, *args: Any, **kwargs: Any) -> Any:
    """
    This is the core method that handles dimension-aware operations.
    """
    if not args:
        raise ValueError("Expected at least one argument (self)")

    # Get dimension argument
    dim_arg = kwargs.get(wrapper.dim_name)
    if dim_arg is None and wrapper.dim_offset < len(args):
        # Try to get dim from positional args (accounting for self at index 0)
        dim_idx = wrapper.dim_offset + 1
        if dim_idx < len(args):
            dim_arg = args[dim_idx]

    # If no dimension argument provided, fall back to standard functorch handling
    if dim_arg is None:
        info = TensorInfo.create(args[0], ensure_batched=True, ensure_present=False)
        if not info:
            return wrapper.orig(*args, **kwargs)

        with EnableAllLayers(info.levels) as guard:
            if info.batchedtensor is None:
                raise AssertionError("Expected batchedtensor to be non-None")
            guard.inplace_update_layers(info.batchedtensor, info.levels)
            new_args = list(args)
            new_args[0] = handle_from_tensor(info.batchedtensor)
            result = wrapper.orig(*new_args, **kwargs)
            return guard.from_batched(result, info.has_device)

    # Handle dimension-aware operation
    info = TensorInfo.create(args[0])
    if not info:
        return wrapper.orig(*args, **kwargs)

    # Check for keepdim parameter
    keepdim = False
    if wrapper.reduce:
        keepdim_arg = kwargs.get("keepdim")
        if keepdim_arg is None and wrapper.keepdim_offset < len(args):
            keepdim_idx = wrapper.keepdim_offset + 1
            if keepdim_idx < len(args):
                keepdim_arg = args[keepdim_idx]
        if keepdim_arg is not None:
            keepdim = bool(keepdim_arg)

    # Wrap dimensions
    ndim = info.ndim()
    dims = _wrap_dims(dim_arg, ndim, keepdim)

    # Convert dimensions to indices and validate
    dim_indices: list[int] = []
    seen = [False] * len(info.levels)

    for d in dims:
        midx = None
        for i, level in enumerate(info.levels):
            if level == d:
                midx = i
                break

        if midx is None:
            # Try to match by position/name more flexibly
            for i, level in enumerate(info.levels):
                if hasattr(level, "matches") and level.matches(d):
                    midx = i
                    break

            if midx is None:
                level_strs = [str(level) for level in info.levels]
                raise ValueError(
                    f"Tensor with dimensions {level_strs} does not contain {d}"
                )

        seen[midx] = True
        dim_indices.append(midx)

    # Determine new levels after reduction
    new_levels = []
    if wrapper.reduce and not keepdim:
        for i, level in enumerate(info.levels):
            if not seen[i]:
                new_levels.append(level)
    else:
        new_levels = info.levels[:]

    # Create dimension indices for the original function
    if len(dim_indices) == 1:
        py_indices: Any = dim_indices[0]
    else:
        py_indices = tuple(dim_indices)

    # Update arguments
    new_args = list(args)
    new_kwargs = kwargs.copy()
    if info.tensor is None:
        raise AssertionError("Expected tensor to be non-None")
    new_args[0] = handle_from_tensor(info.tensor)

    # Update dimension argument
    if wrapper.dim_name in new_kwargs:
        new_kwargs[wrapper.dim_name] = py_indices
    else:
        dim_idx = wrapper.dim_offset + 1
        if dim_idx < len(new_args):
            new_args = list(new_args)
            new_args[dim_idx] = py_indices

    # Call original function
    result = wrapper.orig(*new_args, **new_kwargs)

    # Wrap results
    def wrap_result(obj: Any) -> Any:
        if isinstance(obj, torch.Tensor):
            from . import Tensor

            return Tensor.from_positional(obj, new_levels, info.has_device)
        return obj

    return tree_map(wrap_result, result)