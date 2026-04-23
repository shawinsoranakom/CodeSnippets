def map_shape_dtype_structure(fn, shape, dtype):
    """Variant of tree.map_structure that operates on shape tuples."""
    if is_shape_tuple(shape):
        return fn(tuple(shape), dtype)
    if isinstance(shape, list):
        return [
            map_shape_dtype_structure(fn, s, d) for s, d in zip(shape, dtype)
        ]
    if isinstance(shape, tuple):
        return tuple(
            map_shape_dtype_structure(fn, s, d) for s, d in zip(shape, dtype)
        )
    if isinstance(shape, dict):
        return {
            k: map_shape_dtype_structure(fn, v, dtype[k])
            for k, v in shape.items()
        }
    else:
        raise ValueError(
            f"Cannot map function to unknown objects {shape} and {dtype}"
        )