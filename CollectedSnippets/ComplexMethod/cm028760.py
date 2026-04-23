def _bert_preprocess(self, record: Mapping[str, tf.Tensor]):
    """Parses raw tensors into a dict of tensors to be consumed by the model."""
    if self._use_next_sentence_label:
      input_text = record[self._params.text_field_names[0]]
      # Split sentences
      sentence_breaker = tf_text.RegexSplitter()
      sentences = sentence_breaker.split(input_text)

      # Extract next-sentence-prediction labels and segments
      next_or_random_segment, is_next = (
          segment_extractor.get_next_sentence_labels(sentences))
      # merge dims to change shape from [num_docs, (num_segments)] to
      # [total_num_segments]
      is_next = is_next.merge_dims(-2, -1)

      # construct segments with shape [(num_sentence)]
      segments = [
          sentences.merge_dims(-2, -1),
          next_or_random_segment.merge_dims(-2, -1)
      ]
    else:
      segments = [record[name] for name in self._params.text_field_names]

    segments_combined, segment_ids = self._tokenize(segments)

    # Dynamic masking
    item_selector = tf_text.RandomItemSelector(
        self._max_predictions_per_seq,
        selection_rate=self._masking_rate,
        unselectable_ids=[self._cls_token, self._sep_token],
        shuffle_fn=(tf.identity if self._params.deterministic else None))
    values_chooser = tf_text.MaskValuesChooser(
        vocab_size=self._vocab_size, mask_token=self._mask_token)
    masked_input_ids, masked_lm_positions, masked_lm_ids = (
        tf_text.mask_language_model(
            segments_combined,
            item_selector=item_selector,
            mask_values_chooser=values_chooser,
        ))

    # Pad out to fixed shape and get input mask.
    seq_lengths = {
        "input_word_ids": self._seq_length,
        "input_type_ids": self._seq_length,
        "masked_lm_positions": self._max_predictions_per_seq,
        "masked_lm_ids": self._max_predictions_per_seq,
    }
    model_inputs = {
        "input_word_ids": masked_input_ids,
        "input_type_ids": segment_ids,
        "masked_lm_positions": masked_lm_positions,
        "masked_lm_ids": masked_lm_ids,
    }
    padded_inputs_and_mask = tf.nest.map_structure(tf_text.pad_model_inputs,
                                                   model_inputs, seq_lengths)
    model_inputs = {
        k: padded_inputs_and_mask[k][0] for k in padded_inputs_and_mask
    }
    model_inputs["masked_lm_weights"] = tf.cast(
        padded_inputs_and_mask["masked_lm_ids"][1], tf.float32)
    model_inputs["input_mask"] = padded_inputs_and_mask["input_word_ids"][1]

    if self._use_next_sentence_label:
      model_inputs["next_sentence_labels"] = is_next

    for name in model_inputs:
      t = model_inputs[name]
      if t.dtype == tf.int64:
        t = tf.cast(t, tf.int32)
      model_inputs[name] = t

    return model_inputs