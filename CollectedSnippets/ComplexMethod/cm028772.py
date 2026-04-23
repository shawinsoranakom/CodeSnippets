def _convert_tokens_to_instances(
    tokens: np.array,
    sentence_ids: np.array,
    per_host_batch_size: int,
    seq_length: int,
    reuse_length: int,
    bi_data: bool,
    tokenizer: tokenization.FullSentencePieceTokenizer,
    num_cores_per_host: int = 0,
    logging_frequency: int = 500) -> List[TrainingInstance]:
  """Converts tokens and sentence IDs into individual training instances.

  The format of data in the XLNet pretraining task is very similar to the
  BERT pretraining task. Two segments A and B are randomly sampled, and the
  contatenation of A and B into a single sequence is used to perform
  language modeling.

  To create an XLNet Pretraining instance from a single long sequence, S:
  - Create a segment of length `reuse_length`. This first segment represents
    past tokens. During modeling, this segment is used to cache obtained
    content representations for the segment recurrence mechanism.
  - Similar to BERT, create a segment of length `seq_length` - `reuse_length`
    composed of A and B segments.
    For XLNet, the order is "A", "SEP", "B", "SEP", "CLS".

  Args:
    tokens: All tokens concatenated into a single list.
    sentence_ids: All sentence IDs concatenated into a single list.
    per_host_batch_size: The target batch size per host.
    seq_length: The max sequence length.
    reuse_length: The number of tokens to use from the previous segment.
    bi_data: Whether or not to use bidirectional data.
    tokenizer: The SentencePiece tokenizer that has the attribute `sp_model`.
    num_cores_per_host: The number of cores per host. This is required if
      `bi_data` = `True`.
    logging_frequency: The frequency at which to log status updates.

  Returns:
    A list of `TrainingInstance` objects.
  """
  instances = []

  per_core_batch_size = (per_host_batch_size // num_cores_per_host
                         if bi_data else None)

  if bi_data:
    logging.info("Bi-directional data enabled.")
    assert per_host_batch_size % (2 * num_cores_per_host) == 0
    forward_tokens, forward_sentence_ids = _reshape_to_batch_dimensions(
        tokens=tokens,
        sentence_ids=sentence_ids,
        per_host_batch_size=per_host_batch_size // 2)
    forward_data_shape = (num_cores_per_host, 1, per_core_batch_size // 2, -1)

    forward_tokens = forward_tokens.reshape(forward_data_shape)
    forward_sentence_ids = forward_sentence_ids.reshape(forward_data_shape)

    backwards_tokens = forward_tokens[:, :, :, ::-1]
    backwards_sentence_ids = forward_sentence_ids[:, :, :, ::-1]

    tokens = np.concatenate([forward_tokens, backwards_tokens], 1).reshape(
        per_host_batch_size, -1)
    sentence_ids = np.concatenate(
        [forward_sentence_ids, backwards_sentence_ids]).reshape(
            per_host_batch_size, -1)
  else:
    logging.info("Bi-directional data disabled.")
    tokens, sentence_ids = _reshape_to_batch_dimensions(
        tokens=tokens,
        sentence_ids=sentence_ids,
        per_host_batch_size=per_host_batch_size)

  logging.info("Tokens shape: %s", tokens.shape)

  data_length = tokens.shape[1]
  sep = np.array([special_symbols["<sep>"]], dtype=np.int64)
  cls = np.array([special_symbols["<cls>"]], dtype=np.int64)
  # 2 sep, 1 cls
  num_special_tokens = 3

  data_index = 0
  batch_number = 0
  step_size = reuse_length if reuse_length else seq_length
  num_batches = math.ceil(data_length / step_size)

  while data_index + seq_length <= data_length:
    if batch_number % logging_frequency == 0:
      logging.info("Processing batch %d of %d", batch_number, num_batches)

    for batch_index in range(per_host_batch_size):
      previous_segment_tokens = tokens[
          batch_index, data_index: data_index + reuse_length]

      results = _create_a_and_b_segments(
          tokens=tokens[batch_index],
          sentence_ids=sentence_ids[batch_index],
          begin_index=data_index + reuse_length,
          total_length=seq_length - reuse_length - num_special_tokens)

      if results is None:
        logging.info("Stopping at data index: %d", data_index)
        break
      a_data, b_data, label = results

      data = np.concatenate(
          [previous_segment_tokens, a_data, sep, b_data, sep, cls])
      a_length = a_data.shape[0]
      b_length = b_data.shape[0]
      segment_ids = ([0] * (reuse_length + a_length) + [0]
                     + [1] * b_length + [1] + [2])
      boundary_indices = _get_boundary_indices(tokenizer=tokenizer,
                                               data=data)
      assert len(data) == seq_length
      assert len(segment_ids) == seq_length
      assert len(boundary_indices) > 0  # pylint: disable=g-explicit-length-test

      instances.append(TrainingInstance(
          data=data,
          segment_ids=segment_ids,
          boundary_indices=boundary_indices,
          label=label))
    batch_number += 1
    data_index += step_size
  return instances