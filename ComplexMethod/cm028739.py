def _decode(self, record: tf.Tensor):
    """Decodes a serialized tf.Example."""
    name_to_features = {
        'input_mask': tf.io.VarLenFeature(tf.int64),
        'masked_lm_positions': tf.io.VarLenFeature(tf.int64),
        'masked_lm_ids': tf.io.VarLenFeature(tf.int64),
        'masked_lm_weights': tf.io.VarLenFeature(tf.float32),
    }
    if self._params.use_v2_feature_names:
      input_ids_key = 'input_word_ids'
      segment_key = 'input_type_ids'
      name_to_features.update({
          input_ids_key: tf.io.VarLenFeature(tf.int64),
          segment_key: tf.io.VarLenFeature(tf.int64),
      })
    else:
      input_ids_key = 'input_ids'
      segment_key = 'segment_ids'
      name_to_features.update({
          input_ids_key: tf.io.VarLenFeature(tf.int64),
          segment_key: tf.io.VarLenFeature(tf.int64),
      })
    if self._use_next_sentence_label:
      name_to_features['next_sentence_labels'] = tf.io.FixedLenFeature([1],
                                                                       tf.int64)
    dynamic_keys = [input_ids_key, 'input_mask', segment_key]
    if self._use_position_id:
      name_to_features['position_ids'] = tf.io.VarLenFeature(tf.int64)
      dynamic_keys.append('position_ids')

    example = tf.io.parse_single_example(record, name_to_features)
    for key in dynamic_keys + self._mask_keys:
      example[key] = tf.sparse.to_dense(example[key])

    # Truncate padded data after the first non pad in the
    # sequence length dimension.
    # Pad before the first non pad from the back should not be removed.
    mask = tf.math.greater(
        tf.math.cumsum(example[input_ids_key], reverse=True), 0)
    for key in dynamic_keys:
      example[key] = tf.boolean_mask(example[key], mask)

    # masked_lm_ids should be 0 padded.
    # Change mask features to -1 padding so that we can differentiate
    # padding from data or from bucketizing.
    mask = tf.math.not_equal(example['masked_lm_ids'], 0)
    example['masked_lm_ids'] = tf.where(
        mask, example['masked_lm_ids'],
        -tf.ones(tf.shape(example['masked_lm_ids']), dtype=example[key].dtype))

    # tf.Example only supports tf.int64, but the TPU only supports tf.int32.
    # So cast all int64 to int32.
    # tf.data service uses dataset graph fingerprint to distinguish input
    # pipeline jobs, thus we sort the keys here to make sure they are generated
    # in a deterministic order each time the dataset function is traced.
    for name in sorted(list(example.keys())):
      t = example[name]
      if t.dtype == tf.int64:
        t = tf.cast(t, tf.int32)
      example[name] = t

    return example