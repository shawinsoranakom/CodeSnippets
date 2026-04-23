def _get_initial_state_shapes(
      self,
      block_specs: Sequence[BlockSpec],
      input_shape: Union[Sequence[int], tf.Tensor],
      use_positional_encoding: bool = False) -> Dict[str, Sequence[int]]:
    """Generates names and shapes for all input states.

    Args:
      block_specs: sequence of specs used for creating a model.
      input_shape: the expected 5D shape of the image input.
      use_positional_encoding: whether the model will use positional encoding.

    Returns:
      A dict mapping state names to state shapes.
    """
    def divide_resolution(shape, num_downsamples):
      """Downsamples the dimension to calculate strided convolution shape."""
      if shape is None:
        return None
      if isinstance(shape, tf.Tensor):
        # Avoid using div and ceil to support tf lite
        shape = tf.cast(shape, tf.float32)
        resolution_divisor = 2 ** num_downsamples
        resolution_multiplier = 0.5 ** num_downsamples
        shape = ((shape + resolution_divisor - 1) * resolution_multiplier)
        return tf.cast(shape, tf.int32)
      else:
        resolution_divisor = 2 ** num_downsamples
        return math.ceil(shape / resolution_divisor)

    states = {}
    num_downsamples = 0

    for block_idx, block in enumerate(block_specs):
      if isinstance(block, StemSpec):
        if block.kernel_size[0] > 1:
          states['state_stem_stream_buffer'] = (
              input_shape[0],
              input_shape[1],
              divide_resolution(input_shape[2], num_downsamples),
              divide_resolution(input_shape[3], num_downsamples),
              block.filters,
          )
        num_downsamples += 1
      elif isinstance(block, MovinetBlockSpec):
        block_idx -= 1
        params = list(zip(
            block.expand_filters,
            block.kernel_sizes,
            block.strides))
        for layer_idx, layer in enumerate(params):
          expand_filters, kernel_size, strides = layer

          # If we use a 2D kernel, we apply spatial downsampling
          # before the buffer.
          if (tuple(strides[1:3]) != (1, 1) and
              self._conv_type in ['2plus1d', '3d_2plus1d']):
            num_downsamples += 1

          prefix = f'state_block{block_idx}_layer{layer_idx}'

          if kernel_size[0] > 1:
            states[f'{prefix}_stream_buffer'] = (
                input_shape[0],
                kernel_size[0] - 1,
                divide_resolution(input_shape[2], num_downsamples),
                divide_resolution(input_shape[3], num_downsamples),
                expand_filters,
            )

          if '3d' in self._se_type:
            states[f'{prefix}_pool_buffer'] = (
                input_shape[0], 1, 1, 1, expand_filters,
            )
            states[f'{prefix}_pool_frame_count'] = (1,)

          if use_positional_encoding:
            name = f'{prefix}_pos_enc_frame_count'
            states[name] = (1,)

          if strides[1] != strides[2]:
            raise ValueError('Strides must match in the spatial dimensions, '
                             'got {}'.format(strides))

          # If we use a 3D kernel, we apply spatial downsampling
          # after the buffer.
          if (tuple(strides[1:3]) != (1, 1) and
              self._conv_type not in ['2plus1d', '3d_2plus1d']):
            num_downsamples += 1
      elif isinstance(block, HeadSpec):
        states['state_head_pool_buffer'] = (
            input_shape[0], 1, 1, 1, block.project_filters,
        )
        states['state_head_pool_frame_count'] = (1,)

    return states