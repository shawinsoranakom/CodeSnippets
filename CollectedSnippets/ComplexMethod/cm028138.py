def __call__(self, inputs, state, scope=None):
    """Long short-term memory cell (LSTM) with bottlenecking.

    Args:
      inputs: Input tensor at the current timestep.
      state: Tuple of tensors, the state and output at the previous timestep.
      scope: Optional scope.

    Returns:
      A tuple where the first element is the LSTM output and the second is
      a LSTMStateTuple of the state at the current timestep.
    """
    scope = scope or 'conv_lstm_cell'
    with tf.variable_scope(scope, reuse=tf.AUTO_REUSE):
      c, h = state

      # unflatten state if necessary
      if self._flatten_state:
        c = tf.reshape(c, [-1] + self.output_size)
        h = tf.reshape(h, [-1] + self.output_size)

      # summary of input passed into cell
      if self._viz_gates:
        slim.summaries.add_histogram_summary(inputs, 'cell_input')
      if self._pre_bottleneck:
        bottleneck = inputs
      else:
        bottleneck = slim.separable_conv2d(
            tf.concat([inputs, h], 3),
            self._num_units,
            self._filter_size,
            depth_multiplier=1,
            activation_fn=self._activation,
            normalizer_fn=None,
            scope='bottleneck')

        if self._viz_gates:
          slim.summaries.add_histogram_summary(bottleneck, 'bottleneck')

      concat = slim.separable_conv2d(
          bottleneck,
          4 * self._num_units,
          self._filter_size,
          depth_multiplier=1,
          activation_fn=None,
          normalizer_fn=None,
          scope='gates')

      i, j, f, o = tf.split(concat, 4, 3)

      new_c = (
          c * tf.sigmoid(f + self._forget_bias) +
          tf.sigmoid(i) * self._activation(j))
      if self._clip_state:
        new_c = tf.clip_by_value(new_c, -6, 6)
      new_h = self._activation(new_c) * tf.sigmoid(o)
      # summary of cell output and new state
      if self._viz_gates:
        slim.summaries.add_histogram_summary(new_h, 'cell_output')
        slim.summaries.add_histogram_summary(new_c, 'cell_state')

      output = new_h
      if self._output_bottleneck:
        output = tf.concat([new_h, bottleneck], axis=3)

      # reflatten state to store it
      if self._flatten_state:
        new_c = tf.reshape(new_c, [-1, self._param_count])
        new_h = tf.reshape(new_h, [-1, self._param_count])

      return output, contrib_rnn.LSTMStateTuple(new_c, new_h)