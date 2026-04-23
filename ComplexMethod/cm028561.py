def call(self, inputs):
    word_embeddings = None

    if isinstance(inputs, dict):
      if 'input_word_ids' in inputs.keys():
        word_ids = inputs.get('input_word_ids')
        mask = inputs.get('input_mask')
        type_ids = inputs.get('input_type_ids', None)
        word_embeddings = inputs.get('input_word_embeddings', None)
      elif 'left_word_ids' in inputs.keys():
        word_ids = inputs.get('left_word_ids')
        mask = inputs.get('left_mask')
      elif 'right_word_ids' in inputs.keys():
        word_ids = inputs.get('right_word_ids')
        mask = inputs.get('right_mask')
      dense_inputs = inputs.get('dense_inputs', None)
      dense_mask = inputs.get('dense_mask', None)
    elif isinstance(inputs, list):
      ## Dual Encoder Tasks
      word_ids, mask = inputs
      type_ids = None
      dense_inputs, dense_mask = None, None
    else:
      raise ValueError('Unexpected inputs type to %s.' % self.__class__)

    if type_ids is None:
      type_ids = tf.zeros_like(mask)

    if word_embeddings is None:
      word_embeddings = self._embedding_layer(word_ids)

    if dense_inputs is not None:
      mask = tf.concat([mask, dense_mask], axis=1)

    embeddings = self._embedding_norm_layer(word_embeddings)
    embeddings = self._embedding_dropout(embeddings)

    encoder_outputs = []
    x = embeddings

    for l in range(self._num_layers):
      if x.shape[0] is None:
        pass
      else:
        x = self._transformer_layers[l]([x, mask])
      encoder_outputs.append(x)

    last_encoder_output = encoder_outputs[-1]
    avg_token_tensor = tf.math.reduce_mean(last_encoder_output, axis=1)
    pooled_output = self._pooler_layer(avg_token_tensor)

    output = dict(
        sequence_output=encoder_outputs[-1],
        pooled_output=pooled_output,
        encoder_outputs=encoder_outputs,
    )

    return output