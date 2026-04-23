def create_mock_transformer_xl_data(
    batch_size,
    num_heads,
    head_size,
    hidden_size,
    seq_length,
    memory_length=0,
    num_predictions=2,
    two_stream=False,
    num_layers=1,
    include_biases=True,
    include_state=False,
    include_mask=False,
    include_segment=False):
  """Creates mock testing data.

  Args:
    batch_size: `int`, the batch size.
    num_heads: `int`, number of attention heads.
    head_size: `int`, the size of each attention head.
    hidden_size: `int`, the layer's hidden size.
    seq_length: `int`, Sequence length of the input.
    memory_length: optional `int`, the length of the state. Defaults to 0.
    num_predictions: `int`, the number of predictions used in two stream
      attention.
    two_stream: `bool`, whether or not to generate two stream data.
    num_layers: `int`, the number of Transformer XL blocks.
    include_biases: optional `bool`, whether or not to include attention biases.
    include_state: optional `bool`, whether or not to include state data.
    include_mask: optional `bool`, whether or not to include mask data.
    include_segment: optional `bool`, whether or not to include segment data.

  Returns:
    A dictionary with `str` as keys and `Tensor` as values.
  """
  encoding_shape = (batch_size, seq_length * 2, hidden_size)

  data = dict(
      relative_position_encoding=tf.random.normal(shape=encoding_shape),
      content_stream=tf.random.normal(
          shape=(batch_size, seq_length, hidden_size)))

  if include_biases:
    attention_bias_shape = (num_heads, head_size)
    data.update(dict(
        content_attention_bias=tf.random.normal(shape=attention_bias_shape),
        segment_attention_bias=tf.random.normal(shape=attention_bias_shape),
        positional_attention_bias=tf.random.normal(shape=attention_bias_shape)))

  if two_stream:
    data.update(dict(
        query_stream=tf.random.normal(
            shape=(batch_size, num_predictions, hidden_size)),
        target_mapping=tf.random.normal(
            shape=(batch_size, num_predictions, seq_length))))

  if include_state:
    total_seq_length = seq_length + memory_length
    if num_layers > 1:
      state_shape = (num_layers, batch_size, memory_length, hidden_size)
    else:
      state_shape = (batch_size, memory_length, hidden_size)
    data.update(dict(
        state=tf.random.normal(shape=state_shape)))
  else:
    total_seq_length = seq_length

  if include_mask:
    mask_shape = (batch_size, num_heads, seq_length, total_seq_length)
    mask_data = np.random.randint(2, size=mask_shape).astype("float32")
    data["content_attention_mask"] = mask_data
    if two_stream:
      data["query_attention_mask"] = mask_data

  if include_segment:
    # A transformer XL block takes an individual segment "encoding" from the
    # entirety of the Transformer XL segment "embedding".
    if num_layers > 1:
      segment_encoding_shape = (num_layers, 2, num_heads, head_size)
      segment_encoding_name = "segment_embedding"
    else:
      segment_encoding_shape = (2, num_heads, head_size)
      segment_encoding_name = "segment_encoding"

    segment_matrix = np.random.randint(
        2, size=(batch_size, seq_length, total_seq_length))
    data["segment_matrix"] = tf.math.equal(segment_matrix, 1)
    data[segment_encoding_name] = tf.random.normal(shape=segment_encoding_shape)

  return data