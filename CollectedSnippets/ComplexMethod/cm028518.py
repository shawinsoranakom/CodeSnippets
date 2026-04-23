def call(  # pytype: disable=annotation-type-mismatch
      self, inputs: tf.Tensor, mask: Optional[Any] = None, training: bool = None
  ) -> Mapping[str, tf.Tensor]:
    logging.info(
        'MaxViT inputs: shape %s, dtype %s.', inputs.shape, inputs.dtype
    )
    output = self._stem(inputs, training=training)
    logging.info(
        'Stage 0 (stem) output: shape %s, dtype %s.', output.shape, output.dtype
    )

    endpoints = {}
    add_pos_enc = self._add_pos_enc
    for idx, stage_blocks in enumerate(self._blocks):
      # Add position encoding
      # Note: the position encoding is usually added to the input of the first
      # transformer block. For MaxViT, it is the first block of stage 3.
      if (isinstance(add_pos_enc, (tuple, list)) and add_pos_enc[idx]) or (
          isinstance(add_pos_enc, bool) and add_pos_enc
      ):
        logging.info('Add position encoding at stage %d.', idx + 1)
        output = self._add_absolute_position_encoding(output)

      # Blocks forward
      for block in stage_blocks:
        output = block(output, training=training)

      if self._block_type[idx] == 'tfm':
        height, width = ops.get_shape_from_length(
            output.shape[1], self.height, self.width
        )
        output = tf.reshape(output, [-1, height, width, output.shape[-1]])

      endpoints[str(idx + 2)] = output
      logging.info(
          'Stage %d output: feature level %s shape %s, dtype %s.',
          idx + 1,
          idx + 2,
          output.shape,
          output.dtype,
      )

    self._output_specs = {
        idx: endpoint.get_shape() for idx, endpoint in endpoints.items()
    }

    if self._representation_size and self._representation_size > 0:
      # Backbone's output is [batch_size, height, weight, channel_size].
      output = tf_keras.layers.GlobalAveragePooling2D()(output)
      # Maybe add a layer_norm after global average pooling.
      if self._add_gap_layer_norm:
        output = self._final_layer_norm(output)
      endpoints['pre_logits'] = tf.nn.tanh(self._dense(output))

    return endpoints