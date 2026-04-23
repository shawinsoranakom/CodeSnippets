def _compute_attention_mask(
    input_mask,
    permutation_mask,
    attention_type,
    seq_length,
    memory_length,
    batch_size,
    dtype=tf.float32):
  """Combines all input attention masks for XLNet.

  In XLNet modeling, `0` represents tokens that can be attended, and `1`
  represents tokens that cannot be attended.

  For XLNet pre-training and fine tuning, there are a few masks used:
  - Causal attention mask: If the attention type is unidirectional, then all
    tokens after the current position cannot be attended to.
  - Input mask: when generating data, padding is added to a max sequence length
    to make all sequences the same length. This masks out real tokens (`0`) from
    padding tokens (`1`).
  - Permutation mask: during XLNet pretraining, the input sequence is factorized
    into a factorization sequence `z`. During partial prediction, `z` is split
    at a cutting point `c` (an index of the factorization sequence) and
    prediction is only applied to all tokens after `c`. Therefore, tokens at
    factorization positions `i` > `c` can be attended to and tokens at
    factorization positions `i` <= `c` cannot be attended to.

  This function broadcasts and combines all attention masks to produce the
  query attention mask and the content attention mask.

  Args:
    input_mask: Tensor, the input mask related to padding. Input shape:
      `(B, S)`.
    permutation_mask: Tensor, the permutation mask used in partial prediction.
      Input shape: `(B, S, S)`.
    attention_type: str, the attention type. Can be "uni" (directional) or
      "bi" (directional).
    seq_length: int, the length of each sequence.
    memory_length: int the length of memory blocks.
    batch_size: int, the batch size.
    dtype: The dtype of the masks.

  Returns:
    attention_mask, content_attention_mask: The position and context-based
      attention masks and content attention masks, respectively.

  """
  attention_mask = None
  # `1` values mean do not attend to this position.
  if attention_type == "uni":
    causal_attention_mask = _create_causal_attention_mask(
        seq_length=seq_length,
        memory_length=memory_length,
        dtype=dtype)
    causal_attention_mask = causal_attention_mask[None, None, :, :]
    # `causal_attention_mask`: [1, 1, S, S + M]

  # input_mask: [B, S]
  # permutation_mask: [B, S, S]
  if input_mask is not None and permutation_mask is not None:
    data_mask = _combine_masks(input_mask[:, None, :], permutation_mask, dtype)
  elif input_mask is not None and permutation_mask is None:
    data_mask = input_mask[:, None, :]
  elif input_mask is None and permutation_mask is not None:
    data_mask = permutation_mask
  else:
    data_mask = None

  # data_mask: [B, S, S] or [B, 1, S]

  if data_mask is not None:
    # All positions within state can be attended to.
    state_mask = tf.ones([batch_size, tf.shape(data_mask)[1], memory_length],
                         dtype=dtype)
    # state_mask: [B, 1, M] or [B, S, M]
    data_mask = tf.concat([state_mask, data_mask], 2)
    # data_mask: [B, 1, S + M] or [B, S, S + M]

    if attention_type == "uni":
      attention_mask = _combine_masks(causal_attention_mask,
                                      data_mask[:, None, :, :],
                                      dtype=dtype)
    else:
      attention_mask = data_mask[:, None, :, :]

  if attention_mask is not None:
    # Construct the content attention mask.
    # This ensures that the mask allows the model to attend to positions in
    # content positions (e.g. the content diagonal).
    non_target_mask = tf.concat(
        [tf.zeros([seq_length, memory_length], dtype=dtype),
         tf.eye(seq_length, dtype=dtype)], axis=-1)
    content_attention_mask = _combine_masks(
        attention_mask, non_target_mask, how="or", dtype=dtype)
  else:
    content_attention_mask = None

  return attention_mask, content_attention_mask