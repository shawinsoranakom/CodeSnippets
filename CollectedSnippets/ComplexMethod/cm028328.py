def per_pixel_conditional_conv(input_tensor, parameters, channels, depth):
  """Use parameters perform per-pixel convolutions with the given depth [1].

  [1]: https://arxiv.org/abs/2003.05664

  Args:
    input_tensor: float tensor of shape [num_instances, height,
      width, input_channels]
    parameters: A [num_instances, num_params] float tensor. If num_params
      is incomparible with the given channels and depth, a ValueError will
      be raised.
    channels: int, the number of channels in the convolution.
    depth: int, the number of layers of convolutions to perform.

  Returns:
    output: A [num_instances, height, width] tensor with the conditional
      conv applied according to each instance's parameters.
  """

  input_channels = input_tensor.get_shape().as_list()[3]
  num_params = parameters.get_shape().as_list()[1]

  input_convs = 1 if depth > 1 else 0
  intermediate_convs = depth - 2 if depth >= 2 else 0
  expected_weights = ((input_channels * channels * input_convs) +
                      (channels * channels * intermediate_convs) +
                      channels)  # final conv
  expected_biases = (channels * (depth - 1)) + 1

  if depth == 1:
    if input_channels != channels:
      raise ValueError(
          'When depth=1, input_channels({}) should be equal to'.format(
              input_channels) + ' channels({})'.format(channels))

  if num_params != (expected_weights + expected_biases):
    raise ValueError('Expected {} parameters at depth {}, but got {}'.format(
        expected_weights + expected_biases, depth, num_params))

  start = 0
  output = input_tensor
  for i in range(depth):

    is_last_layer = i == (depth - 1)
    if is_last_layer:
      channels = 1

    num_params_single_conv = channels * input_channels + channels
    params = parameters[:, start:start + num_params_single_conv]

    start += num_params_single_conv
    output = _per_pixel_single_conv(output, params, channels)

    if not is_last_layer:
      output = tf.nn.relu(output)

    input_channels = channels

  return output