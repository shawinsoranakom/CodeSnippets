def _compute_positional_encoding(
    attention_type,
    position_encoding_layer,
    hidden_size,
    batch_size,
    total_length,
    seq_length,
    clamp_length,
    bi_data,
    dtype=tf.float32):
  """Computes the relative position encoding.

  Args:
    attention_type: str, the attention type. Can be "uni" (directional) or
      "bi" (directional).
    position_encoding_layer: An instance of `RelativePositionEncoding`.
    hidden_size: int, the hidden size.
    batch_size: int, the batch size.
    total_length: int, the sequence length added to the memory length.
    seq_length: int, the length of each sequence.
    clamp_length: int, clamp all relative distances larger than clamp_length. -1
      means no clamping.
    bi_data: bool, whether to use bidirectional input pipeline. Usually set to
      True during pretraining and False during finetuning.
    dtype: the dtype of the encoding.

  Returns:
    A Tensor, representing the position encoding.

  """
  freq_seq = tf.range(0, hidden_size, 2.0)
  if dtype is not None and dtype != tf.float32:
    freq_seq = tf.cast(freq_seq, dtype=dtype)

  if attention_type == "bi":
    beg, end = total_length, -seq_length
  elif attention_type == "uni":
    beg, end = total_length, -1
  else:
    raise ValueError("Unknown `attention_type` {}.".format(attention_type))

  if bi_data:
    forward_position_sequence = tf.range(beg, end, -1.0)
    backward_position_sequence = tf.range(-beg, -end, 1.0)

    if dtype is not None and dtype != tf.float32:
      forward_position_sequence = tf.cast(forward_position_sequence,
                                          dtype=dtype)
      backward_position_sequence = tf.cast(backward_position_sequence,
                                           dtype=dtype)

    if clamp_length > 0:
      forward_position_sequence = tf.clip_by_value(
          forward_position_sequence,
          -clamp_length,
          clamp_length)
      backward_position_sequence = tf.clip_by_value(
          backward_position_sequence,
          -clamp_length,
          clamp_length)

    if batch_size is not None:
      forward_positional_encoding = position_encoding_layer(
          forward_position_sequence, batch_size // 2)
      backward_positional_encoding = position_encoding_layer(
          backward_position_sequence, batch_size // 2)
    else:
      forward_positional_encoding = position_encoding_layer(
          forward_position_sequence, None)
      backward_positional_encoding = position_encoding_layer(
          backward_position_sequence, None)

    relative_position_encoding = tf.concat(
        [forward_positional_encoding, backward_positional_encoding], axis=0)
  else:
    forward_position_sequence = tf.range(beg, end, -1.0)
    if dtype is not None and dtype != tf.float32:
      forward_position_sequence = tf.cast(
          forward_position_sequence, dtype=dtype)
    if clamp_length > 0:
      forward_position_sequence = tf.clip_by_value(
          forward_position_sequence,
          -clamp_length,
          clamp_length)

    relative_position_encoding = position_encoding_layer(
        forward_position_sequence, batch_size)
  return relative_position_encoding