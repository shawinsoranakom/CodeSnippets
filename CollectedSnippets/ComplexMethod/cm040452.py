def standardize_shape(shape):
    if not isinstance(shape, tuple):
        if shape is None:
            raise ValueError("Undefined shapes are not supported.")
        if not hasattr(shape, "__iter__"):
            raise ValueError(f"Cannot convert '{shape}' to a shape.")
        if config.backend() == "tensorflow":
            if isinstance(shape, tf.TensorShape):
                # `tf.TensorShape` may contain `Dimension` objects.
                # We need to convert the items in it to either int or `None`
                shape = shape.as_list()

    if config.backend() == "jax":
        # Replace `_DimExpr` (dimension expression) with None
        from jax import export as jax_export

        shape = tuple(
            None if jax_export.is_symbolic_dim(d) else d for d in shape
        )

    if config.backend() == "torch":
        # Replace symbolic dimensions with None to preserve dynamic shapes
        # during torch.export tracing
        import torch

        shape = tuple(None if isinstance(d, torch.SymInt) else d for d in shape)

    # Handle dimensions that are not ints and not None, verify they're >= 0.
    standardized_shape = []
    for d in shape:
        if d is None:
            standardized_shape.append(d)
            continue

        # Reject these even if they can be cast to int successfully.
        if isinstance(d, (str, float)):
            raise ValueError(
                f"Cannot convert '{shape}' to a shape. "
                f"Found invalid dimension '{d}' of type '{type(d)}'. "
            )

        try:
            # Cast numpy scalars, tf constant tensors, etc.
            d = int(d)
        except Exception as e:
            raise ValueError(
                f"Cannot convert '{shape}' to a shape. "
                f"Found invalid dimension '{d}' of type '{type(d)}'. "
            ) from e
        if d < 0:
            raise ValueError(
                f"Cannot convert '{shape}' to a shape. "
                "Negative dimensions are not allowed."
            )
        standardized_shape.append(d)

    # This also turns subclasses of `tuple` (e.g. `torch.Size`) to plain tuple.
    return tuple(standardized_shape)