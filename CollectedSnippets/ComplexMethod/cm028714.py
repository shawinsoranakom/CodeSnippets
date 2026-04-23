def bert_pack_inputs(inputs: Union[tf.RaggedTensor, List[tf.RaggedTensor]],
                       seq_length: Union[int, tf.Tensor],
                       start_of_sequence_id: Union[int, tf.Tensor],
                       end_of_segment_id: Union[int, tf.Tensor],
                       padding_id: Union[int, tf.Tensor],
                       truncator="round_robin"):
    """Freestanding equivalent of the BertPackInputs layer."""
    _check_if_tf_text_installed()
    # Sanitize inputs.
    if not isinstance(inputs, (list, tuple)):
      inputs = [inputs]
    if not inputs:
      raise ValueError("At least one input is required for packing")
    input_ranks = [rt.shape.rank for rt in inputs]
    if None in input_ranks or len(set(input_ranks)) > 1:
      raise ValueError("All inputs for packing must have the same known rank, "
                       "found ranks " + ",".join(input_ranks))
    # Flatten inputs to [batch_size, (tokens)].
    if input_ranks[0] > 2:
      inputs = [rt.merge_dims(1, -1) for rt in inputs]
    # In case inputs weren't truncated (as they should have been),
    # fall back to some ad-hoc truncation.
    num_special_tokens = len(inputs) + 1
    if truncator == "round_robin":
      trimmed_segments = text.RoundRobinTrimmer(seq_length -
                                                num_special_tokens).trim(inputs)
    elif truncator == "waterfall":
      trimmed_segments = text.WaterfallTrimmer(
          seq_length - num_special_tokens).trim(inputs)
    else:
      raise ValueError("Unsupported truncator: %s" % truncator)
    # Combine segments.
    segments_combined, segment_ids = text.combine_segments(
        trimmed_segments,
        start_of_sequence_id=start_of_sequence_id,
        end_of_segment_id=end_of_segment_id)
    # Pad to dense Tensors.
    input_word_ids, _ = text.pad_model_inputs(segments_combined, seq_length,
                                              pad_value=padding_id)
    input_type_ids, input_mask = text.pad_model_inputs(segment_ids, seq_length,
                                                       pad_value=0)
    # Work around broken shape inference.
    output_shape = tf.stack([
        inputs[0].nrows(out_type=tf.int32),  # batch_size
        tf.cast(seq_length, dtype=tf.int32)])
    def _reshape(t):
      return tf.reshape(t, output_shape)
    # Assemble nest of input tensors as expected by BERT TransformerEncoder.
    return dict(input_word_ids=_reshape(input_word_ids),
                input_mask=_reshape(input_mask),
                input_type_ids=_reshape(input_type_ids))