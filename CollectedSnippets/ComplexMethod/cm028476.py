def parser(record):
    """Function used to parse tfrecord."""

    record_spec = {
        "input": tf.io.FixedLenFeature([seq_len], tf.int64),
        "seg_id": tf.io.FixedLenFeature([seq_len], tf.int64),
        "label": tf.io.FixedLenFeature([1], tf.int64),
    }

    if online_masking_config.sample_strategy in ["whole_word", "word_span"]:
      logging.info("Add `boundary` spec for %s",
                   online_masking_config.sample_strategy)
      record_spec["boundary"] = tf.io.VarLenFeature(tf.int64)

    # retrieve serialized example
    example = tf.io.parse_single_example(
        serialized=record, features=record_spec)

    inputs = example.pop("input")
    if online_masking_config.sample_strategy in ["whole_word", "word_span"]:
      boundary = tf.sparse.to_dense(example.pop("boundary"))
    else:
      boundary = None
    is_masked, _ = _online_sample_masks(
        inputs, seq_len, num_predict, online_masking_config, boundary=boundary)

    if reuse_len > 0:
      ##### Use memory
      # permutate the reuse and non-reuse parts separately
      non_reuse_len = seq_len - reuse_len
      assert reuse_len % perm_size == 0 and non_reuse_len % perm_size == 0

      # Creates permutation mask and target mask for the first reuse_len tokens.
      # The tokens in this part are reused from the last sequence.
      perm_mask_0, target_mask_0, input_k_0, input_q_0 = _local_perm(
          inputs[:reuse_len], is_masked[:reuse_len], perm_size, reuse_len,
          leak_ratio)

      # Creates permutation mask and target mask for the rest of tokens in
      # current example, which are concatentation of two new segments.
      perm_mask_1, target_mask_1, input_k_1, input_q_1 = _local_perm(
          inputs[reuse_len:], is_masked[reuse_len:], perm_size, non_reuse_len,
          leak_ratio)

      perm_mask_0 = tf.concat(
          [perm_mask_0, tf.ones([reuse_len, non_reuse_len])], axis=1)
      perm_mask_1 = tf.concat(
          [tf.zeros([non_reuse_len, reuse_len]), perm_mask_1], axis=1)
      perm_mask = tf.concat([perm_mask_0, perm_mask_1], axis=0)
      target_mask = tf.concat([target_mask_0, target_mask_1], axis=0)
      input_k = tf.concat([input_k_0, input_k_1], axis=0)
      input_q = tf.concat([input_q_0, input_q_1], axis=0)
    else:
      ##### Do not use memory
      assert seq_len % perm_size == 0
      # permutate the entire sequence together
      perm_mask, target_mask, input_k, input_q = _local_perm(
          inputs, is_masked, perm_size, seq_len, leak_ratio)

    # reshape back to fixed shape
    example["perm_mask"] = tf.reshape(perm_mask, [seq_len, seq_len])
    example["input_ids"] = tf.reshape(input_k, [seq_len])
    example["input_q"] = tf.reshape(input_q, [seq_len])

    # Directly use raw inputs as the target
    target = inputs

    if num_predict is not None:
      indices = tf.range(seq_len, dtype=tf.int64)
      bool_target_mask = tf.cast(target_mask, tf.bool)
      indices = tf.boolean_mask(indices, bool_target_mask)

      ##### extra padding due to CLS/SEP introduced after prepro
      actual_num_predict = tf.shape(indices)[0]
      pad_len = num_predict - actual_num_predict

      ##### target_mapping
      target_mapping = tf.one_hot(indices, seq_len, dtype=tf.float32)
      paddings = tf.zeros([pad_len, seq_len], dtype=target_mapping.dtype)
      target_mapping = tf.concat([target_mapping, paddings], axis=0)
      example["target_mapping"] = tf.reshape(target_mapping,
                                             [num_predict, seq_len])

      ##### target
      target = tf.boolean_mask(target, bool_target_mask)
      paddings = tf.zeros([pad_len], dtype=target.dtype)
      target = tf.concat([target, paddings], axis=0)
      example["target"] = tf.reshape(target, [num_predict])

      ##### target mask
      target_mask = tf.concat([
          tf.ones([actual_num_predict], dtype=tf.float32),
          tf.zeros([pad_len], dtype=tf.float32)
      ],
                              axis=0)
      example["target_mask"] = tf.reshape(target_mask, [num_predict])
    else:
      example["target"] = tf.reshape(target, [seq_len])
      example["target_mask"] = tf.reshape(target_mask, [seq_len])

    for key in list(example.keys()):
      val = example[key]
      if tf_keras.backend.is_sparse(val):
        val = tf.sparse.to_dense(val)
      if val.dtype == tf.int64:
        val = tf.cast(val, tf.int32)

      example[key] = val

    for k, v in example.items():
      logging.info("%s: %s", k, v)

    return example