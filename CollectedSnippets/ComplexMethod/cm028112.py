def pix2pix_generator(net,
                      num_outputs,
                      blocks=None,
                      upsample_method='nn_upsample_conv',
                      is_training=False):  # pylint: disable=unused-argument
  """Defines the network architecture.

  Args:
    net: A `Tensor` of size [batch, height, width, channels]. Note that the
      generator currently requires square inputs (e.g. height=width).
    num_outputs: The number of (per-pixel) outputs.
    blocks: A list of generator blocks or `None` to use the default generator
      definition.
    upsample_method: The method of upsampling images, one of 'nn_upsample_conv'
      or 'conv2d_transpose'
    is_training: Whether or not we're in training or testing mode.

  Returns:
    A `Tensor` representing the model output and a dictionary of model end
      points.

  Raises:
    ValueError: if the input heights do not match their widths.
  """
  end_points = {}

  blocks = blocks or _default_generator_blocks()

  input_size = net.get_shape().as_list()

  input_size[3] = num_outputs

  upsample_fn = functools.partial(upsample, method=upsample_method)

  encoder_activations = []

  ###########
  # Encoder #
  ###########
  with tf.variable_scope('encoder'):
    with slim.arg_scope([slim.conv2d],
                        kernel_size=[4, 4],
                        stride=2,
                        activation_fn=tf.nn.leaky_relu):

      for block_id, block in enumerate(blocks):
        # No normalizer for the first encoder layers as per 'Image-to-Image',
        # Section 5.1.1
        if block_id == 0:
          # First layer doesn't use normalizer_fn
          net = slim.conv2d(net, block.num_filters, normalizer_fn=None)
        elif block_id < len(blocks) - 1:
          net = slim.conv2d(net, block.num_filters)
        else:
          # Last layer doesn't use activation_fn nor normalizer_fn
          net = slim.conv2d(
              net, block.num_filters, activation_fn=None, normalizer_fn=None)

        encoder_activations.append(net)
        end_points['encoder%d' % block_id] = net

  ###########
  # Decoder #
  ###########
  reversed_blocks = list(blocks)
  reversed_blocks.reverse()

  with tf.variable_scope('decoder'):
    # Dropout is used at both train and test time as per 'Image-to-Image',
    # Section 2.1 (last paragraph).
    with slim.arg_scope([slim.dropout], is_training=True):

      for block_id, block in enumerate(reversed_blocks):
        if block_id > 0:
          net = tf.concat([net, encoder_activations[-block_id - 1]], axis=3)

        # The Relu comes BEFORE the upsample op:
        net = tf.nn.relu(net)
        net = upsample_fn(net, block.num_filters, [2, 2])
        if block.decoder_keep_prob > 0:
          net = slim.dropout(net, keep_prob=block.decoder_keep_prob)
        end_points['decoder%d' % block_id] = net

  with tf.variable_scope('output'):
    # Explicitly set the normalizer_fn to None to override any default value
    # that may come from an arg_scope, such as pix2pix_arg_scope.
    logits = slim.conv2d(
        net, num_outputs, [4, 4], activation_fn=None, normalizer_fn=None)
    logits = tf.reshape(logits, input_size)

    end_points['logits'] = logits
    end_points['predictions'] = tf.tanh(logits)

  return logits, end_points