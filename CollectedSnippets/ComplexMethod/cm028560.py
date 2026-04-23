def call(self, inputs):
    if isinstance(inputs, dict):
      word_embeddings = inputs.get('input_word_embeddings', None)
      type_ids = inputs.get('input_type_ids', None)
      if 'input_word_ids' in inputs.keys():
        word_ids = inputs.get('input_word_ids')
        mask = inputs.get('input_mask')
      elif 'left_word_ids' in inputs.keys():
        word_ids = inputs.get('left_word_ids')
        mask = inputs.get('left_mask')
      elif 'right_word_ids' in inputs.keys():
        word_ids = inputs.get('right_word_ids')
        mask = inputs.get('right_mask')
      dense_inputs = inputs.get('dense_inputs', None)
      dense_mask = inputs.get('dense_mask', None)
      dense_type_ids = inputs.get('dense_type_ids', None)
    elif isinstance(inputs, list):
      ## Dual Encoder Tasks
      word_ids, mask = inputs
      word_embeddings = None
      type_ids = None
      dense_inputs, dense_mask, dense_type_ids = None, None, None
    else:
      raise ValueError('Unexpected inputs type to %s.' % self.__class__)

    if type_ids is None:
      type_ids = tf.zeros_like(mask)

    if word_embeddings is None:
      word_embeddings = self._embedding_layer(word_ids)

    if dense_inputs is not None:
      mask = tf.concat([mask, dense_mask], axis=1)

    embeddings = self._get_embeddings(
        word_ids, type_ids, word_embeddings, dense_inputs, dense_type_ids
    )
    embeddings = self._embedding_norm_layer(embeddings)
    embeddings = self._embedding_dropout(embeddings)

    if self._embedding_projection is not None:
      embeddings = self._embedding_projection(embeddings)

    attention_mask = self._attention_mask_layer(embeddings, mask)

    encoder_outputs = []
    x = embeddings
    for layer in self._transformer_layers:
      x = layer([x, attention_mask])
      encoder_outputs.append(x)

    last_encoder_output = encoder_outputs[-1]
    first_token_tensor = last_encoder_output[:, 0, :]
    pooled_output = self._pooler_layer(first_token_tensor)

    output = dict(
        sequence_output=encoder_outputs[-1],
        pooled_output=pooled_output,
        encoder_outputs=encoder_outputs,
    )

    return output