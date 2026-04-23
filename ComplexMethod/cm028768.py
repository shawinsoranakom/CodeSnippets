def _parse(self, record: Mapping[str, tf.Tensor]):
    """Parses raw tensors into a dict of tensors to be consumed by the model."""
    x = {}

    inputs = record['input_word_ids']
    x['input_type_ids'] = record['input_type_ids']

    if self._sample_strategy in ['whole_word', 'word_span']:
      boundary = tf.sparse.to_dense(record['boundary_indices'])
    else:
      boundary = None

    input_mask = self._online_sample_mask(inputs=inputs, boundary=boundary)

    if self._reuse_length > 0:
      if self._permutation_size > self._reuse_length:
        logging.warning(
            '`permutation_size` is greater than `reuse_length` (%d > %d).'
            'This may introduce data leakage.', self._permutation_size,
            self._reuse_length)

      # Enable the memory mechanism.
      # Permute the reuse and non-reuse segments separately.
      non_reuse_len = self._seq_length - self._reuse_length
      if not (self._reuse_length % self._permutation_size == 0 and
              non_reuse_len % self._permutation_size == 0):
        raise ValueError('`reuse_length` and `seq_length` should both be '
                         'a multiple of `permutation_size`.')

      # Creates permutation mask and target mask for the first reuse_len tokens.
      # The tokens in this part are reused from the last sequence.
      perm_mask_0, target_mask_0, tokens_0, masked_0 = self._get_factorization(
          inputs=inputs[:self._reuse_length],
          input_mask=input_mask[:self._reuse_length])

      # Creates permutation mask and target mask for the rest of tokens in
      # current example, which are concatenation of two new segments.
      perm_mask_1, target_mask_1, tokens_1, masked_1 = self._get_factorization(
          inputs[self._reuse_length:], input_mask[self._reuse_length:])

      perm_mask_0 = tf.concat([
          perm_mask_0,
          tf.zeros([self._reuse_length, non_reuse_len], dtype=tf.int32)
      ],
                              axis=1)
      perm_mask_1 = tf.concat([
          tf.ones([non_reuse_len, self._reuse_length], dtype=tf.int32),
          perm_mask_1
      ],
                              axis=1)
      perm_mask = tf.concat([perm_mask_0, perm_mask_1], axis=0)
      target_mask = tf.concat([target_mask_0, target_mask_1], axis=0)
      tokens = tf.concat([tokens_0, tokens_1], axis=0)
      masked_tokens = tf.concat([masked_0, masked_1], axis=0)
    else:
      # Disable the memory mechanism.
      if self._seq_length % self._permutation_size != 0:
        raise ValueError('`seq_length` should be a multiple of '
                         '`permutation_size`.')
      # Permute the entire sequence together
      perm_mask, target_mask, tokens, masked_tokens = self._get_factorization(
          inputs=inputs, input_mask=input_mask)
    x['permutation_mask'] = tf.reshape(perm_mask,
                                       [self._seq_length, self._seq_length])
    x['input_word_ids'] = tokens
    x['masked_tokens'] = masked_tokens

    target = tokens
    if self._max_predictions_per_seq is not None:
      indices = tf.range(self._seq_length, dtype=tf.int32)
      bool_target_mask = tf.cast(target_mask, tf.bool)
      indices = tf.boolean_mask(indices, bool_target_mask)

      # account for extra padding due to CLS/SEP.
      actual_num_predict = tf.shape(indices)[0]
      pad_len = self._max_predictions_per_seq - actual_num_predict

      target_mapping = tf.one_hot(indices, self._seq_length, dtype=tf.int32)
      paddings = tf.zeros([pad_len, self._seq_length],
                          dtype=target_mapping.dtype)
      target_mapping = tf.concat([target_mapping, paddings], axis=0)
      x['target_mapping'] = tf.reshape(
          target_mapping, [self._max_predictions_per_seq, self._seq_length])

      target = tf.boolean_mask(target, bool_target_mask)
      paddings = tf.zeros([pad_len], dtype=target.dtype)
      target = tf.concat([target, paddings], axis=0)
      x['target'] = tf.reshape(target, [self._max_predictions_per_seq])

      target_mask = tf.concat([
          tf.ones([actual_num_predict], dtype=tf.int32),
          tf.zeros([pad_len], dtype=tf.int32)
      ],
                              axis=0)
      x['target_mask'] = tf.reshape(target_mask,
                                    [self._max_predictions_per_seq])
    else:
      x['target'] = tf.reshape(target, [self._seq_length])
      x['target_mask'] = tf.reshape(target_mask, [self._seq_length])
    return x