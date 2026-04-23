def distribute_tensor(tensor, layout):
    """Distribute the tensor based on the layout.

    Note that this function can be used both in eager context, or within a
    jitted function.

    Args:
        tensor: `jax.Array` that need to be distributed.
        layout: `TensorLayout` for the created variable, or a
            JAX-supported layout instance (e.g. `jax.sharding.Sharding`).

    Returns:
        Distributed value.
    """
    # Avoid circular imports.
    from keras.src.distribution import TensorLayout

    if isinstance(layout, TensorLayout):
        layout = layout.backend_layout

    if jax_utils.is_in_jax_tracing_scope(tensor):
        return jax.lax.with_sharding_constraint(tensor, layout)

    # Skip relayout if unnecessary.
    if isinstance(tensor, jax.Array):
        if isinstance(
            layout, jax.sharding.Sharding
        ) and tensor.sharding.is_equivalent_to(layout, ndim=len(tensor.shape)):
            return tensor
        # JAX explicit "layout" support.
        elif hasattr(layout, "layout"):
            current_layout = getattr(tensor, "layout", None)
            if current_layout == layout:
                return tensor
        # JAX explicit "format" support.
        elif hasattr(layout, "format"):
            current_layout = getattr(tensor, "format", None)
            if current_layout == layout:
                return tensor

    return jax.device_put(tensor, layout)