def call(self, inputs, output_range: Optional[tf.Tensor] = None):
    # inputs are [word_ids, mask, type_ids]
    word_embeddings = None
    if isinstance(inputs, (list, tuple)):
      logging.warning('List inputs to  %s are discouraged.', self.__class__)
      if len(inputs) == 3:
        word_ids, mask, type_ids = inputs
        dense_inputs = None
        dense_mask = None
        dense_type_ids = None
      elif len(inputs) == 6:
        word_ids, mask, type_ids, dense_inputs, dense_mask, dense_type_ids = (
            inputs
        )
      else:
        raise ValueError(
            'Unexpected inputs to %s with length at %d.'
            % (self.__class__, len(inputs))
        )
    elif isinstance(inputs, dict):
      word_ids = inputs.get('input_word_ids')
      mask = inputs.get('input_mask')
      type_ids = inputs.get('input_type_ids')
      word_embeddings = inputs.get('input_word_embeddings', None)

      dense_inputs = inputs.get('dense_inputs', None)
      dense_mask = inputs.get('dense_mask', None)
      dense_type_ids = inputs.get('dense_type_ids', None)
    else:
      raise ValueError('Unexpected inputs type to %s.' % self.__class__)

    if word_embeddings is None:
      word_embeddings = self._embedding_layer(word_ids)

    if dense_inputs is not None:
      # Allow concatenation of the dense embeddings at sequence end if requested
      # and `unpool_length`` is set as zero
      if self._append_dense_inputs:
        if self._unpool_length != 0:
          raise ValueError(
              'unpool_length is not supported by append_dense_inputs now.'
          )
        word_embeddings = tf.concat([word_embeddings, dense_inputs], axis=1)
        type_ids = tf.concat([type_ids, dense_type_ids], axis=1)
        mask = tf.concat([mask, dense_mask], axis=1)
      else:
        # Concat the dense embeddings at sequence begin so unpool_len can
        # control embedding not being pooled.
        word_embeddings = tf.concat([dense_inputs, word_embeddings], axis=1)
        type_ids = tf.concat([dense_type_ids, type_ids], axis=1)
        mask = tf.concat([dense_mask, mask], axis=1)
    # absolute position embeddings
    position_embeddings = self._position_embedding_layer(word_embeddings)
    type_embeddings = self._type_embedding_layer(type_ids)

    embeddings = tf_keras.layers.add(
        [word_embeddings, position_embeddings, type_embeddings])
    embeddings = self._embedding_norm_layer(embeddings)
    embeddings = self._embedding_dropout(embeddings)

    if self._embedding_projection is not None:
      embeddings = self._embedding_projection(embeddings)

    attention_mask = self._attention_mask_layer(embeddings, mask)

    encoder_outputs = []
    x = embeddings
    # TODO(b/195972228): attention_mask can be co-generated with pooling.
    if self._pool_type in (_MAX, _AVG):
      attention_mask = _pool_and_concat(
          attention_mask,
          unpool_length=self._unpool_length,
          strides=self._pool_strides[0],
          axes=[1])

      for i, layer in enumerate(self._transformer_layers):
        transformer_output_range = None
        if i == self._num_layers - 1:
          transformer_output_range = output_range

        # Bypass no pooling cases.
        if self._pool_strides[i] == 1:
          x = layer(
              [x, x, attention_mask], output_range=transformer_output_range
          )
        else:
          # Pools layer for compressing the query length.
          pooled_inputs = self._att_input_pool_layers[i](
              x[:, self._unpool_length:, :])
          query_inputs = tf.concat(
              values=(tf.cast(
                  x[:, :self._unpool_length, :],
                  dtype=pooled_inputs.dtype), pooled_inputs),
              axis=1)
          x = layer([query_inputs, x, attention_mask],
                    output_range=transformer_output_range)
        # Pools the corresponding attention_mask.
        if i < len(self._transformer_layers) - 1:
          attention_mask = _pool_and_concat(
              attention_mask,
              unpool_length=self._unpool_length,
              strides=[self._pool_strides[i + 1], self._pool_strides[i]],
              axes=[1, 2])
        encoder_outputs.append(x)
    elif self._pool_type == _TRUNCATED_AVG:
      # Compute the attention masks and pooling transforms.
      # Note we do not compute this in __init__ due to inference converter issue
      # b/215659399.
      pooling_transforms = _create_truncated_avg_transforms(
          self._max_sequence_length, self._pool_strides)
      attention_masks = _create_truncated_avg_masks(mask, self._pool_strides,
                                                    pooling_transforms)
      for i, layer in enumerate(self._transformer_layers):
        attention_mask = attention_masks[i]
        transformer_output_range = None
        if i == self._num_layers - 1:
          transformer_output_range = output_range
        # Bypass no pooling cases.
        if self._pool_strides[i] == 1:
          x = layer([x, x, attention_mask],
                    output_range=transformer_output_range)
        else:
          pooled_inputs = tf.einsum(
              'BFD,FT->BTD',
              tf.cast(x[:, self._unpool_length:, :], _get_policy_dtype()
                     ),  # extra casting for faster mixed computation.
              pooling_transforms[i])
          query_inputs = tf.concat(
              values=(tf.cast(
                  x[:, :self._unpool_length, :],
                  dtype=pooled_inputs.dtype), pooled_inputs),
              axis=1)
          x = layer([query_inputs, x, attention_mask],
                    output_range=transformer_output_range)
        encoder_outputs.append(x)

    last_encoder_output = encoder_outputs[-1]
    first_token_tensor = last_encoder_output[:, 0, :]
    pooled_output = self._pooler_layer(first_token_tensor)

    return dict(
        word_embeddings=word_embeddings,
        embedding_output=embeddings,
        sequence_output=encoder_outputs[-1],
        pooled_output=pooled_output,
        encoder_outputs=encoder_outputs)