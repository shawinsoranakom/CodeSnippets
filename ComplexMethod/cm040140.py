def make_tf_tensor_spec(x, dynamic_batch=False):
    """Create a TensorSpec from various input types.

    Args:
        x: Input to convert (tf.TensorSpec, KerasTensor, or backend tensor).
        dynamic_batch: If True, set the batch dimension to None.

    Returns:
        A tf.TensorSpec instance.
    """
    if isinstance(x, tf.TensorSpec):
        tensor_spec = x
        # Adjust batch dimension if needed
        if dynamic_batch and len(tensor_spec.shape) > 0:
            shape = tuple(
                None if i == 0 else s for i, s in enumerate(tensor_spec.shape)
            )
            tensor_spec = tf.TensorSpec(
                shape, dtype=tensor_spec.dtype, name=tensor_spec.name
            )
    else:
        input_spec = make_input_spec(x)
        shape = input_spec.shape
        # Adjust batch dimension if needed and shape is not None
        if dynamic_batch and shape is not None and len(shape) > 0:
            shape = tuple(None if i == 0 else s for i, s in enumerate(shape))
        tensor_spec = tf.TensorSpec(
            shape, dtype=input_spec.dtype, name=input_spec.name
        )
    return tensor_spec