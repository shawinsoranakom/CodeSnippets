def _build_network(
      self,
      input_specs: tf_keras.layers.InputSpec,
      state_specs: Optional[Mapping[str, tf_keras.layers.InputSpec]] = None,
  ) -> Tuple[TensorMap, Union[TensorMap, Tuple[TensorMap, TensorMap]]]:
    """Builds the model network.

    Args:
      input_specs: the model input spec to use.
      state_specs: a dict mapping a state name to the corresponding state spec.
        State names should match with the `state` input/output dict.

    Returns:
      Inputs and outputs as a tuple. Inputs are expected to be a dict with
      base input and states. Outputs are expected to be a dict of endpoints
      and (optional) output states.
    """
    state_specs = state_specs if state_specs is not None else {}

    image_input = tf_keras.Input(shape=input_specs.shape[1:], name='inputs')

    states = {
        name: tf_keras.Input(shape=spec.shape[1:], dtype=spec.dtype, name=name)
        for name, spec in state_specs.items()
    }

    inputs = {**states, 'image': image_input}
    endpoints = {}

    x = image_input

    num_layers = sum(
        len(block.expand_filters)
        for block in self._block_specs
        if isinstance(block, MovinetBlockSpec))
    stochastic_depth_idx = 1
    for block_idx, block in enumerate(self._block_specs):
      if isinstance(block, StemSpec):
        layer_obj = movinet_layers.Stem(
            block.filters,
            block.kernel_size,
            block.strides,
            conv_type=self._conv_type,
            causal=self._causal,
            activation=self._activation,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer,
            batch_norm_layer=self._norm,
            batch_norm_momentum=self._norm_momentum,
            batch_norm_epsilon=self._norm_epsilon,
            use_sync_bn=self._use_sync_bn,
            state_prefix='state_stem',
            name='stem')
        x, states = layer_obj(x, states=states)
        endpoints['stem'] = x
      elif isinstance(block, MovinetBlockSpec):
        if not (len(block.expand_filters) == len(block.kernel_sizes) ==
                len(block.strides)):
          raise ValueError(
              'Lengths of block parameters differ: {}, {}, {}'.format(
                  len(block.expand_filters),
                  len(block.kernel_sizes),
                  len(block.strides)))
        params = list(zip(block.expand_filters,
                          block.kernel_sizes,
                          block.strides))
        for layer_idx, layer in enumerate(params):
          stochastic_depth_drop_rate = (
              self._stochastic_depth_drop_rate * stochastic_depth_idx /
              num_layers)
          expand_filters, kernel_size, strides = layer
          name = f'block{block_idx-1}_layer{layer_idx}'
          layer_obj = movinet_layers.MovinetBlock(
              block.base_filters,
              expand_filters,
              kernel_size=kernel_size,
              strides=strides,
              causal=self._causal,
              activation=self._activation,
              gating_activation=self._gating_activation,
              stochastic_depth_drop_rate=stochastic_depth_drop_rate,
              conv_type=self._conv_type,
              se_type=self._se_type,
              use_positional_encoding=
              self._use_positional_encoding and self._causal,
              kernel_initializer=self._kernel_initializer,
              kernel_regularizer=self._kernel_regularizer,
              batch_norm_layer=self._norm,
              batch_norm_momentum=self._norm_momentum,
              batch_norm_epsilon=self._norm_epsilon,
              use_sync_bn=self._use_sync_bn,
              state_prefix=f'state_{name}',
              name=name)
          x, states = layer_obj(x, states=states)

          endpoints[name] = x
          stochastic_depth_idx += 1
      elif isinstance(block, HeadSpec):
        layer_obj = movinet_layers.Head(
            project_filters=block.project_filters,
            conv_type=self._conv_type,
            activation=self._activation,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer,
            batch_norm_layer=self._norm,
            batch_norm_momentum=self._norm_momentum,
            batch_norm_epsilon=self._norm_epsilon,
            use_sync_bn=self._use_sync_bn,
            average_pooling_type=self._average_pooling_type,
            state_prefix='state_head',
            name='head')
        x, states = layer_obj(x, states=states)
        endpoints['head'] = x
      else:
        raise ValueError('Unknown block type {}'.format(block))

    outputs = (endpoints, states) if self._output_states else endpoints

    return inputs, outputs