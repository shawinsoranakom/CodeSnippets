def _pad_to_multiple(tensor: tf.Tensor,
                     factor: Union[int, tf.Tensor],
                     axis: int,
                     mode: Optional[Text] = 'CONSTANT',
                     constant_values=0,
                     name: Optional[Text] = None) -> tf.Tensor:
  """Pads `tensor` on a given `axis` to be a multiple of `factor`.

  Padding will be concatenated to the end of the axis only, not the beginning.
  If the length along `axis` is already a multiple of `factor`, this is
  effectively a no-op.

  Args:
    tensor: A Tensor with rank >= 1 to pad.
    factor: Positive integer factor to pad for. If a Tensor, must be a scalar
      int.
    axis: A valid axis in `tensor` to pad.
    mode: The padding mode to use according to `tf.pad`. Defaults to 'CONSTANT'.
    constant_values: For 'CONSTANT' mode, the scalar pad value to use within
      `tf.pad`. Defaults to 0. Must be same type as `tensor`.
    name: A name for the operation (optional).

  Returns:
    The padded Tensor result.
  """
  with tf.name_scope(name or 'pad_to_multiple'):
    tensor = tf.convert_to_tensor(tensor)

    if isinstance(factor, int) and factor < 1:
      raise ValueError('`factor` must be positive.')
    rank = tensor.shape.rank
    if rank is None:
      raise ValueError('Static rank of `tensor` must be known.')
    if axis < 0:
      axis += rank
    if axis < 0 or axis >= rank:
      raise ValueError('`axis` out of bounds for `tensor` rank.')

    axis_len = tf_utils.get_shape_list(tensor)[axis]
    pad_len = -axis_len % factor
    paddings = pad_len * tf.one_hot([-1, axis], rank, axis=0, dtype=tf.int32)
    return tf.pad(
        tensor=tensor,
        paddings=paddings,
        mode=mode,
        constant_values=constant_values)