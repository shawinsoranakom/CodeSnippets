def _any_str_or_dim_in_dynamic_shapes(
    dynamic_shapes: dict[str, Any] | tuple[Any, ...] | list[Any],
) -> bool:
    """Check if there is any string or Dim in the dynamic_shapes."""
    flat_dynamic_shapes, _ = _flatten_dynamic_shapes_to_axes(dynamic_shapes)
    # This indicates the dynamic_shapes includes something we don't support in axes, and it's flattened
    # to itself. Otherwise, flat_dynamic_shapes should be a list of dict/list/tuple (or None).
    if any(
        not isinstance(axes, (dict, list, tuple)) and axes is not None
        for axes in flat_dynamic_shapes
    ):
        return False
    # both str and Dim can provide custom names
    for axes in flat_dynamic_shapes:
        if isinstance(axes, dict):
            for dim in axes.values():
                if isinstance(dim, (str, Dim)):
                    return True
        elif isinstance(axes, (list, tuple)):
            for dim in axes:
                if isinstance(dim, (str, Dim)):
                    return True
    return False