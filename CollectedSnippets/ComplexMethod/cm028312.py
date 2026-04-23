def make_prediction_net(num_out_channels, kernel_sizes=(3), num_filters=(256),
                        bias_fill=None, use_depthwise=False, name=None,
                        unit_height_conv=True):
  """Creates a network to predict the given number of output channels.

  This function is intended to make the prediction heads for the CenterNet
  meta architecture.

  Args:
    num_out_channels: Number of output channels.
    kernel_sizes: A list representing the sizes of the conv kernel in the
      intermediate layer. Note that the length of the list indicates the number
      of intermediate conv layers and it must be the same as the length of the
      num_filters.
    num_filters: A list representing the number of filters in the intermediate
      conv layer. Note that the length of the list indicates the number of
      intermediate conv layers.
    bias_fill: If not None, is used to initialize the bias in the final conv
      layer.
    use_depthwise: If true, use SeparableConv2D to construct the Sequential
      layers instead of Conv2D.
    name: Optional name for the prediction net.
    unit_height_conv: If True, Conv2Ds have asymmetric kernels with height=1.

  Returns:
    net: A keras module which when called on an input tensor of size
      [batch_size, height, width, num_in_channels] returns an output
      of size [batch_size, height, width, num_out_channels]
  """
  if isinstance(kernel_sizes, int) and isinstance(num_filters, int):
    kernel_sizes = [kernel_sizes]
    num_filters = [num_filters]
  assert len(kernel_sizes) == len(num_filters)
  if use_depthwise:
    conv_fn = tf.keras.layers.SeparableConv2D
  else:
    conv_fn = tf.keras.layers.Conv2D

  # We name the convolution operations explicitly because Keras, by default,
  # uses different names during training and evaluation. By setting the names
  # here, we avoid unexpected pipeline breakage in TF1.
  out_conv = tf.keras.layers.Conv2D(
      num_out_channels,
      kernel_size=1,
      name='conv1' if tf_version.is_tf1() else None)

  if bias_fill is not None:
    out_conv.bias_initializer = tf.keras.initializers.constant(bias_fill)

  layers = []
  for idx, (kernel_size,
            num_filter) in enumerate(zip(kernel_sizes, num_filters)):
    layers.append(
        conv_fn(
            num_filter,
            kernel_size=[1, kernel_size] if unit_height_conv else kernel_size,
            padding='same',
            name='conv2_%d' % idx if tf_version.is_tf1() else None))
    layers.append(tf.keras.layers.ReLU())
  layers.append(out_conv)
  net = tf.keras.Sequential(layers, name=name)
  return net