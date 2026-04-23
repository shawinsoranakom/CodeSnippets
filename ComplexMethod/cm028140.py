def __call__(self, inputs, state, scope=None):
    """Long short-term memory cell (LSTM) with bottlenecking.

    Includes logic for quantization-aware training. Note that all concats and
    activations use fixed ranges unless stated otherwise.

    Args:
      inputs: Input tensor at the current timestep.
      state: Tuple of tensors, the state at the previous timestep.
      scope: Optional scope.

    Returns:
      A tuple where the first element is the LSTM output and the second is
      a LSTMStateTuple of the state at the current timestep.
    """
    scope = scope or 'conv_lstm_cell'
    with tf.variable_scope(scope, reuse=tf.AUTO_REUSE):
      c, h = state

      # Set nodes to be under raw_inputs/ name scope for tfmini export.
      with tf.name_scope(None):
        c = tf.identity(c, name='raw_inputs/init_lstm_c')
        # When pre_bottleneck is enabled, input h handle is in rnn_decoder.py
        if not self._pre_bottleneck:
          h = tf.identity(h, name='raw_inputs/init_lstm_h')

      # unflatten state if necessary
      if self._flatten_state:
        c = tf.reshape(c, [-1] + self.output_size)
        h = tf.reshape(h, [-1] + self.output_size)

      c_list = tf.split(c, self._groups, axis=3)
      if self._pre_bottleneck:
        inputs_list = tf.split(inputs, self._groups, axis=3)
      else:
        h_list = tf.split(h, self._groups, axis=3)
      out_bottleneck = []
      out_c = []
      out_h = []
      # summary of input passed into cell
      if self._viz_gates:
        slim.summaries.add_histogram_summary(inputs, 'cell_input')

      for k in range(self._groups):
        if self._pre_bottleneck:
          bottleneck = inputs_list[k]
        else:
          if self._conv_op_overrides:
            bottleneck_fn = self._conv_op_overrides[0]
          else:
            bottleneck_fn = functools.partial(
                lstm_utils.quantizable_separable_conv2d,
                kernel_size=self._filter_size,
                activation_fn=self._activation)
          if self._use_batch_norm:
            b_x = bottleneck_fn(
                inputs=inputs,
                num_outputs=self._num_units // self._groups,
                is_quantized=self._is_quantized,
                depth_multiplier=1,
                normalizer_fn=None,
                scope='bottleneck_%d_x' % k)
            b_h = bottleneck_fn(
                inputs=h_list[k],
                num_outputs=self._num_units // self._groups,
                is_quantized=self._is_quantized,
                depth_multiplier=1,
                normalizer_fn=None,
                scope='bottleneck_%d_h' % k)
            b_x = slim.batch_norm(
                b_x,
                scale=True,
                is_training=self._is_training,
                scope='BatchNorm_%d_X' % k)
            b_h = slim.batch_norm(
                b_h,
                scale=True,
                is_training=self._is_training,
                scope='BatchNorm_%d_H' % k)
            bottleneck = b_x + b_h
          else:
            # All concats use fixed quantization ranges to prevent rescaling
            # at inference. Both |inputs| and |h_list| are tensors resulting
            # from Relu6 operations so we fix the ranges to [0, 6].
            bottleneck_concat = lstm_utils.quantizable_concat(
                [inputs, h_list[k]],
                axis=3,
                is_training=False,
                is_quantized=self._is_quantized,
                scope='bottleneck_%d/quantized_concat' % k)
            bottleneck = bottleneck_fn(
                inputs=bottleneck_concat,
                num_outputs=self._num_units // self._groups,
                is_quantized=self._is_quantized,
                depth_multiplier=1,
                normalizer_fn=None,
                scope='bottleneck_%d' % k)

        if self._conv_op_overrides:
          conv_fn = self._conv_op_overrides[1]
        else:
          conv_fn = functools.partial(
              lstm_utils.quantizable_separable_conv2d,
              kernel_size=self._filter_size,
              activation_fn=None)
        concat = conv_fn(
            inputs=bottleneck,
            num_outputs=4 * self._num_units // self._groups,
            is_quantized=self._is_quantized,
            depth_multiplier=1,
            normalizer_fn=None,
            scope='concat_conv_%d' % k)

        # Since there is no activation in the previous separable conv, we
        # quantize here. A starting range of [-6, 6] is used because the
        # tensors are input to a Sigmoid function that saturates at these
        # ranges.
        concat = lstm_utils.quantize_op(
            concat,
            is_training=self._is_training,
            default_min=-6,
            default_max=6,
            is_quantized=self._is_quantized,
            scope='gates_%d/act_quant' % k)

        # i = input_gate, j = new_input, f = forget_gate, o = output_gate
        i, j, f, o = tf.split(concat, 4, 3)

        f_add = f + self._forget_bias
        f_add = lstm_utils.quantize_op(
            f_add,
            is_training=self._is_training,
            default_min=-6,
            default_max=6,
            is_quantized=self._is_quantized,
            scope='forget_gate_%d/add_quant' % k)
        f_act = tf.sigmoid(f_add)

        a = c_list[k] * f_act
        a = lstm_utils.quantize_op(
            a,
            is_training=self._is_training,
            is_quantized=self._is_quantized,
            scope='forget_gate_%d/mul_quant' % k)

        i_act = tf.sigmoid(i)

        j_act = self._activation(j)
        # The quantization range is fixed for the relu6 to ensure that zero
        # is exactly representable.
        j_act = lstm_utils.fixed_quantize_op(
            j_act,
            fixed_min=0.0,
            fixed_max=6.0,
            is_quantized=self._is_quantized,
            scope='new_input_%d/act_quant' % k)

        b = i_act * j_act
        b = lstm_utils.quantize_op(
            b,
            is_training=self._is_training,
            is_quantized=self._is_quantized,
            scope='input_gate_%d/mul_quant' % k)

        new_c = a + b
        # The quantization range is fixed to [0, 6] due to an optimization in
        # TFLite. The order of operations is as fllows:
        #     Add -> FakeQuant -> Relu6 -> FakeQuant -> Concat.
        # The fakequant ranges to the concat must be fixed to ensure all inputs
        # to the concat have the same range, removing the need for rescaling.
        # The quantization ranges input to the relu6 are propagated to its
        # output. Any mismatch between these two ranges will cause an error.
        new_c = lstm_utils.fixed_quantize_op(
            new_c,
            fixed_min=0.0,
            fixed_max=6.0,
            is_quantized=self._is_quantized,
            scope='new_c_%d/add_quant' % k)

        if not self._is_quantized:
          if self._scale_state:
            normalizer = tf.maximum(1.0,
                                    tf.reduce_max(new_c, axis=(1, 2, 3)) / 6)
            new_c /= tf.reshape(normalizer, [tf.shape(new_c)[0], 1, 1, 1])
          elif self._clip_state:
            new_c = tf.clip_by_value(new_c, -6, 6)

        new_c_act = self._activation(new_c)
        # The quantization range is fixed for the relu6 to ensure that zero
        # is exactly representable.
        new_c_act = lstm_utils.fixed_quantize_op(
            new_c_act,
            fixed_min=0.0,
            fixed_max=6.0,
            is_quantized=self._is_quantized,
            scope='new_c_%d/act_quant' % k)

        o_act = tf.sigmoid(o)

        new_h = new_c_act * o_act
        # The quantization range is fixed since it is input to a concat.
        # A range of [0, 6] is used since |new_h| is a product of ranges [0, 6]
        # and [0, 1].
        new_h_act = lstm_utils.fixed_quantize_op(
            new_h,
            fixed_min=0.0,
            fixed_max=6.0,
            is_quantized=self._is_quantized,
            scope='new_h_%d/act_quant' % k)

        out_bottleneck.append(bottleneck)
        out_c.append(new_c_act)
        out_h.append(new_h_act)

      # Since all inputs to the below concats are already quantized, we can use
      # a regular concat operation.
      new_c = tf.concat(out_c, axis=3)
      new_h = tf.concat(out_h, axis=3)

      # |bottleneck| is input to a concat with |new_h|. We must use
      # quantizable_concat() with a fixed range that matches |new_h|.
      bottleneck = lstm_utils.quantizable_concat(
          out_bottleneck,
          axis=3,
          is_training=False,
          is_quantized=self._is_quantized,
          scope='out_bottleneck/quantized_concat')

      # summary of cell output and new state
      if self._viz_gates:
        slim.summaries.add_histogram_summary(new_h, 'cell_output')
        slim.summaries.add_histogram_summary(new_c, 'cell_state')

      output = new_h
      if self._output_bottleneck:
        output = lstm_utils.quantizable_concat(
            [new_h, bottleneck],
            axis=3,
            is_training=False,
            is_quantized=self._is_quantized,
            scope='new_output/quantized_concat')

      # reflatten state to store it
      if self._flatten_state:
        new_c = tf.reshape(new_c, [-1, self._param_count], name='lstm_c')
        new_h = tf.reshape(new_h, [-1, self._param_count], name='lstm_h')

      # Set nodes to be under raw_outputs/ name scope for tfmini export.
      with tf.name_scope(None):
        new_c = tf.identity(new_c, name='raw_outputs/lstm_c')
        new_h = tf.identity(new_h, name='raw_outputs/lstm_h')
      states_and_output = contrib_rnn.LSTMStateTuple(new_c, new_h)

      return output, states_and_output