def call(self, inputs, output_range: Optional[tf.Tensor] = None):
    if isinstance(inputs, dict):
      word_ids = inputs.get('input_word_ids')
      mask = inputs.get('input_mask')
      type_ids = inputs.get('input_type_ids')

      dense_inputs = inputs.get('dense_inputs', None)
      dense_mask = inputs.get('dense_mask', None)
      dense_type_ids = inputs.get('dense_type_ids', None)
    else:
      raise ValueError('Unexpected inputs type to %s.' % self.__class__)

    word_embeddings = self._embedding_layer(word_ids)

    if dense_inputs is not None:
      # Concat the dense embeddings at sequence end.
      word_embeddings = tf.concat([word_embeddings, dense_inputs], axis=1)
      type_ids = tf.concat([type_ids, dense_type_ids], axis=1)
      mask = tf.concat([mask, dense_mask], axis=1)

    # absolute position embeddings.
    position_embeddings = self._position_embedding_layer(word_embeddings)
    type_embeddings = self._type_embedding_layer(type_ids)

    embeddings = word_embeddings + position_embeddings + type_embeddings
    embeddings = self._embedding_norm_layer(embeddings)
    embeddings = self._embedding_dropout(embeddings)

    if self._embedding_projection is not None:
      embeddings = self._embedding_projection(embeddings)

    attention_mask = self._attention_mask_layer(embeddings, mask)

    encoder_outputs = []
    x = embeddings

    # Get token routing.
    token_importance = self._token_importance_embed(word_ids)
    selected, not_selected = self._token_separator(token_importance)

    # For a 12-layer BERT:
    #   1. All tokens fist go though 5 transformer layers, then
    #   2. Only important tokens go through 1 transformer layer with cross
    #      attention to unimportant tokens, then
    #   3. Only important tokens go through 5 transformer layers without cross
    #      attention.
    #   4. Finally, all tokens go through the last layer.

    # Step 1.
    for i, layer in enumerate(self._transformer_layers[:self._num_layers // 2 -
                                                       1]):
      x = layer([x, attention_mask],
                output_range=output_range if i == self._num_layers -
                1 else None)
      encoder_outputs.append(x)

    # Step 2.
    # First, separate important and non-important tokens.
    x_selected = tf.gather(x, selected, batch_dims=1, axis=1)
    mask_selected = tf.gather(mask, selected, batch_dims=1, axis=1)
    attention_mask_token_drop = self._attention_mask_layer(
        x_selected, mask_selected)

    x_not_selected = tf.gather(x, not_selected, batch_dims=1, axis=1)
    mask_not_selected = tf.gather(mask, not_selected, batch_dims=1, axis=1)
    attention_mask_token_pass = self._attention_mask_layer(
        x_selected, tf.concat([mask_selected, mask_not_selected], axis=1))
    x_all = tf.concat([x_selected, x_not_selected], axis=1)

    # Then, call transformer layer with cross attention.
    x_selected = self._transformer_layers[self._num_layers // 2 - 1](
        [x_selected, x_all, attention_mask_token_pass],
        output_range=output_range if self._num_layers // 2 -
        1 == self._num_layers - 1 else None)
    encoder_outputs.append(x_selected)

    # Step 3.
    for i, layer in enumerate(self._transformer_layers[self._num_layers //
                                                       2:-1]):
      x_selected = layer([x_selected, attention_mask_token_drop],
                         output_range=output_range if i == self._num_layers - 1
                         else None)
      encoder_outputs.append(x_selected)

    # Step 4.
    # First, merge important and non-important tokens.
    x_not_selected = tf.cast(x_not_selected, dtype=x_selected.dtype)
    x = tf.concat([x_selected, x_not_selected], axis=1)
    indices = tf.concat([selected, not_selected], axis=1)
    reverse_indices = tf.argsort(indices)
    x = tf.gather(x, reverse_indices, batch_dims=1, axis=1)

    # Then, call transformer layer with all tokens.
    x = self._transformer_layers[-1]([x, attention_mask],
                                     output_range=output_range)
    encoder_outputs.append(x)

    last_encoder_output = encoder_outputs[-1]
    first_token_tensor = last_encoder_output[:, 0, :]
    pooled_output = self._pooler_layer(first_token_tensor)

    return dict(
        sequence_output=encoder_outputs[-1],
        pooled_output=pooled_output,
        encoder_outputs=encoder_outputs)