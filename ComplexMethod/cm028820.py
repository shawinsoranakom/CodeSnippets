def shard_tensors(
    axis: int, block_size: int, tensors: 'Sequence[tf.Tensor]'
) -> Union[List[Sequence[tf.Tensor]], 'Iterable[Sequence[tf.Tensor]]']:
  """Consistently splits multiple tensors sharding-style.

  Args:
    axis: axis to be used to split tensors
    block_size: block size to split tensors.
    tensors: list of tensors.

  Returns:
    List of shards, each shard has exactly one peace of each input tesnor.

  Raises:
    ValueError: if input tensors has different size of sharded dimension.
  """
  if not all(tensor.shape.is_fully_defined() for tensor in tensors):
    return [tensors]
  for validate_axis in range(axis + 1):
    consistent_length: int = tensors[0].shape[validate_axis]
    for tensor in tensors:
      if tensor.shape[validate_axis] != consistent_length:
        raise ValueError('Inconsistent shapes in shard_tensors: first is '
                         f'{tensors[0].shape} and other is {tensor.shape}')
  batch_size: int = tensors[0].shape[axis]
  if block_size >= batch_size:
    return [tensors]
  else:
    blocks = batch_size // block_size
    remainder = batch_size % block_size
    if remainder:
      tensor_parts = []
      for tensor in tensors:
        shape: tf.TensorShape = tensor.shape
        body: tf.Tensor = tf.slice(tensor, [0] * len(shape), [
            size if i != axis else blocks * block_size
            for i, size in enumerate(shape)
        ])
        tail: tf.Tensor = tf.slice(tensor, [
            0 if i != axis else (blocks * block_size)
            for i, _ in enumerate(shape)
        ], [
            size if i != axis else (size - blocks * block_size)
            for i, size in enumerate(shape)
        ])
        tensor_parts.append(tf.split(body, blocks, axis) + [tail])
      return zip(*tensor_parts)
    else:
      return zip(*[tf.split(tensor, blocks, axis) for tensor in tensors])