def call(self, inputs):
    word_embeddings = None
    if isinstance(inputs, dict):
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
      mask = tf.concat([mask, dense_mask], axis=1)

    embeddings = self._get_embeddings(word_ids, type_ids, word_embeddings,
                                      dense_inputs, dense_type_ids)
    embeddings = self._embedding_norm_layer(embeddings)
    embeddings = self._embedding_dropout(embeddings)

    if self._embedding_projection is not None:
      embeddings = self._embedding_projection(embeddings)

    attention_mask = self._attention_mask_layer(embeddings, mask)

    encoder_outputs = []
    attention_outputs = []
    x = embeddings
    for i, layer in enumerate(self._transformer_layers):
      transformer_output_range = None
      if i == self._num_layers - 1:
        transformer_output_range = self._output_range
      x = layer([x, attention_mask], output_range=transformer_output_range)
      if self._config['return_attention_scores']:
        x, attention_scores = x
        attention_outputs.append(attention_scores)
      encoder_outputs.append(x)

    last_encoder_output = encoder_outputs[-1]
    first_token_tensor = last_encoder_output[:, 0, :]
    pooled_output = self._pooler_layer(first_token_tensor)

    output = dict(
        sequence_output=encoder_outputs[-1],
        pooled_output=pooled_output,
        encoder_outputs=encoder_outputs)
    if self._config['return_attention_scores']:
      output['attention_scores'] = attention_outputs

    if self._config['return_word_embeddings']:
      output['word_embeddings'] = embeddings

    return output