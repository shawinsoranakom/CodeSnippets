def pad_to_multiple(tensor, multiple):
  """Returns the tensor zero padded to the specified multiple.

  Appends 0s to the end of the first and second dimension (height and width) of
  the tensor until both dimensions are a multiple of the input argument
  'multiple'. E.g. given an input tensor of shape [1, 3, 5, 1] and an input
  multiple of 4, PadToMultiple will append 0s so that the resulting tensor will
  be of shape [1, 4, 8, 1].

  Args:
    tensor: rank 4 float32 tensor, where
            tensor -> [batch_size, height, width, channels].
    multiple: the multiple to pad to.

  Returns:
    padded_tensor: the tensor zero padded to the specified multiple.
  """
  if multiple == 1:
    return tensor

  tensor_shape = tensor.get_shape()
  batch_size = static_shape.get_batch_size(tensor_shape)
  tensor_height = static_shape.get_height(tensor_shape)
  tensor_width = static_shape.get_width(tensor_shape)
  tensor_depth = static_shape.get_depth(tensor_shape)

  if batch_size is None:
    batch_size = tf.shape(tensor)[0]

  if tensor_height is None:
    tensor_height = tf.shape(tensor)[1]
    padded_tensor_height = tf.cast(
        tf.ceil(
            tf.cast(tensor_height, dtype=tf.float32) /
            tf.cast(multiple, dtype=tf.float32)),
        dtype=tf.int32) * multiple
  else:
    padded_tensor_height = int(
        math.ceil(float(tensor_height) / multiple) * multiple)

  if tensor_width is None:
    tensor_width = tf.shape(tensor)[2]
    padded_tensor_width = tf.cast(
        tf.ceil(
            tf.cast(tensor_width, dtype=tf.float32) /
            tf.cast(multiple, dtype=tf.float32)),
        dtype=tf.int32) * multiple
  else:
    padded_tensor_width = int(
        math.ceil(float(tensor_width) / multiple) * multiple)

  if tensor_depth is None:
    tensor_depth = tf.shape(tensor)[3]

  # Use tf.concat instead of tf.pad to preserve static shape
  if padded_tensor_height != tensor_height:
    height_pad = tf.zeros([
        batch_size, padded_tensor_height - tensor_height, tensor_width,
        tensor_depth
    ], dtype=tensor.dtype)
    tensor = tf.concat([tensor, height_pad], 1)
  if padded_tensor_width != tensor_width:
    width_pad = tf.zeros([
        batch_size, padded_tensor_height, padded_tensor_width - tensor_width,
        tensor_depth
    ], dtype=tensor.dtype)
    tensor = tf.concat([tensor, width_pad], 2)

  return tensor