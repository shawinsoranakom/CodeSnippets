def pre_bottleneck(self, inputs, state, input_index):
    """Apply pre-bottleneck projection to inputs.

    Pre-bottleneck operation maps features of different channels into the same
    dimension. The purpose of this op is to share the features from both large
    and small models in the same LSTM cell.

    Args:
      inputs: 4D Tensor with shape [batch_size x width x height x input_size].
      state: 4D Tensor with shape [batch_size x width x height x state_size].
      input_index: integer index indicating which base features the inputs
        correspoding to.

    Returns:
      inputs: pre-bottlenecked inputs.
    Raises:
      ValueError: If pre_bottleneck is not set or inputs is not rank 4.
    """
    # Sometimes state is a tuple, in which case it cannot be modified, e.g.
    # during training, tf.contrib.training.SequenceQueueingStateSaver
    # returns the state as a tuple. This should not be an issue since we
    # only need to modify state[1] during export, when state should be a
    # list.
    if not self._pre_bottleneck:
      raise ValueError('Only applied when pre_bottleneck is set to true.')
    if len(inputs.shape) != 4:
      raise ValueError('Expect a rank 4 feature tensor.')
    if not self._flatten_state and len(state.shape) != 4:
      raise ValueError('Expect rank 4 state tensor.')
    if self._flatten_state and len(state.shape) != 2:
      raise ValueError('Expect rank 2 state tensor when flatten_state is set.')

    with tf.name_scope(None):
      state = tf.identity(
          state, name='raw_inputs/init_lstm_h_%d' % (input_index + 1))
    if self._flatten_state:
      batch_size = inputs.shape[0]
      height = inputs.shape[1]
      width = inputs.shape[2]
      state = tf.reshape(state, [batch_size, height, width, -1])
    with tf.variable_scope('conv_lstm_cell', reuse=tf.AUTO_REUSE):
      state_split = tf.split(state, self._groups, axis=3)
      with tf.variable_scope('bottleneck_%d' % input_index):
        bottleneck_out = []
        for k in range(self._groups):
          with tf.variable_scope('group_%d' % k):
            bottleneck_out.append(
                lstm_utils.quantizable_separable_conv2d(
                    lstm_utils.quantizable_concat(
                        [inputs, state_split[k]],
                        axis=3,
                        is_training=self._is_training,
                        is_quantized=self._is_quantized,
                        scope='quantized_concat'),
                    self.output_size[-1] / self._groups,
                    self._filter_size,
                    is_quantized=self._is_quantized,
                    depth_multiplier=1,
                    activation_fn=tf.nn.relu6,
                    normalizer_fn=None,
                    scope='project'))
        inputs = lstm_utils.quantizable_concat(
            bottleneck_out,
            axis=3,
            is_training=self._is_training,
            is_quantized=self._is_quantized,
            scope='bottleneck_out/quantized_concat')
      # For exporting inference graph, we only mark the first timestep.
      with tf.name_scope(None):
        inputs = tf.identity(
            inputs, name='raw_outputs/base_endpoint_%d' % (input_index + 1))
    return inputs