def _flatten_dims(tensor: tf.Tensor,
                  first_dim: Optional[int] = 0,
                  last_dim: Optional[int] = -1,
                  name: Optional[Text] = None) -> tf.Tensor:
  """Flattens the given span of dimensions in `tensor`.

  Args:
    tensor: [..., first_dim_size, ...middle_dims..., last_dim_size, ...] shaped
      Tensor.
    first_dim: The first dimension to flatten (inclusive). Must be a valid index
      for the rank of `tensor`. Default is 0.
    last_dim: The last dimension to flatten (inclusive). Must be a valid index
      for the rank of `tensor`. Default is -1.
    name: A name for the operation (optional).

  Returns:
    Tensor of shape [..., flattened_dim_size, ...] where
    flattened_dim_size = first_dim_size * ...middle_dims... * last_dim_size.
  """
  with tf.name_scope(name or 'flatten_dims'):
    tensor = tf.convert_to_tensor(tensor)

    rank = tensor.shape.rank
    if rank is None:
      raise ValueError('Static rank of `tensor` must be known.')
    if first_dim < 0:  # pytype: disable=unsupported-operands
      first_dim += rank
    if first_dim < 0 or first_dim >= rank:  # pytype: disable=unsupported-operands
      raise ValueError('`first_dim` out of bounds for `tensor` rank.')
    if last_dim < 0:  # pytype: disable=unsupported-operands
      last_dim += rank
    if last_dim < 0 or last_dim >= rank:  # pytype: disable=unsupported-operands
      raise ValueError('`last_dim` out of bounds for `tensor` rank.')
    if first_dim > last_dim:  # pytype: disable=unsupported-operands
      raise ValueError('`first_dim` must not be larger than `last_dim`.')

    # Try to calculate static flattened dim size if all input sizes to flatten
    # are statically known. Otherwise, just use -1.
    flat_dims_shape = tensor.shape[first_dim:(last_dim + 1)].as_list()
    flattened_dim_size = 1
    for size in flat_dims_shape:
      if size is None:
        flattened_dim_size = -1
        break
      flattened_dim_size *= size

    old_shape = tf.shape(tensor)
    output_shape = tf.concat([
        old_shape[:first_dim], [flattened_dim_size], old_shape[(last_dim + 1):]
    ], 0)
    return tf.reshape(tensor, output_shape)