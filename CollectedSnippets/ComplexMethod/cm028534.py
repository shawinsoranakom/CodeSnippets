def spatial_resize_and_concat(inputs):
  """Concatenates multiple different sized tensors channel-wise.

  Args:
    inputs: A list of `Tensors` of size `[batch*time, channels, height, width]`.

  Returns:
    The output `Tensor` after concatenation.
  """
  data_format = tf_keras.backend.image_data_format()
  assert data_format == 'channels_last'

  # Do nothing if only 1 input
  if len(inputs) == 1:
    return inputs[0]
  if data_format != 'channels_last':
    return inputs

  # get smallest spatial size and largest channels
  sm_size = [1000, 1000]
  for inp in inputs:
    # assume batch X height x width x channels
    sm_size[0] = min(sm_size[0], inp.shape[1])
    sm_size[1] = min(sm_size[1], inp.shape[2])

  for i in range(len(inputs)):
    if inputs[i].shape[1] != sm_size[0] or inputs[i].shape[2] != sm_size[1]:
      ratio = (inputs[i].shape[1] + 1) // sm_size[0]
      inputs[i] = tf_keras.layers.MaxPool2D([ratio, ratio],
                                            ratio,
                                            padding='same')(
                                                inputs[i])

  return tf.concat(inputs, 3)