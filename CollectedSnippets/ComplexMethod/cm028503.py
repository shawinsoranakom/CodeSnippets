def _get_noise_shape(
    x: tf.Tensor, noise_shape: Union[Sequence[int], tf.TensorShape]
) -> Union[tf.Tensor, tf.TensorShape, Sequence[int]]:
  """Computes the shape of the binary mask for dropout."""
  # If noise_shape is none return immediately.
  if noise_shape is None:
    return tf.shape(x)

  try:
    # Best effort to figure out the intended shape.
    # If not possible, let the op to handle it.
    # In eager mode exception will show up.
    noise_shape_ = _as_shape(noise_shape)
  except (TypeError, ValueError):
    return noise_shape

  if x.shape.dims is not None and len(x.shape.dims) == len(noise_shape_.dims):
    new_dims = []
    for i, dim in enumerate(x.shape.dims):
      if noise_shape_.dims[i].value is None and dim.value is not None:
        new_dims.append(dim.value)
      else:
        new_dims.append(noise_shape_.dims[i].value)
    return tf.TensorShape(new_dims)

  return noise_shape