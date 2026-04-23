def _create_a_and_b_segments(
    tokens: np.array,
    sentence_ids: np.array,
    begin_index: int,
    total_length: int,
    no_cut_probability: float = 0.5):
  """Splits segments A and B from a single instance of tokens and sentence ids.

  Args:
    tokens: The 1D input token ids. This represents an individual entry within a
      batch.
    sentence_ids: The 1D input sentence ids. This represents an individual entry
      within a batch. This should be the same length as `tokens`.
    begin_index: The reference beginning index to split data.
    total_length: The target combined length of segments A and B.
    no_cut_probability: The probability of not cutting a segment despite
      a cut possibly existing.

  Returns:
    A tuple consisting of A data, B data, and label.

  """
  data_length = tokens.shape[0]
  if begin_index + total_length >= data_length:
    logging.info("[_create_segments]: begin_index %d + total_length %d >= "
                 "data_length %d", begin_index, total_length, data_length)
    return None

  end_index = begin_index + 1
  cut_indices = []

  # Identify all indices where sentence IDs change from one to the next.
  while end_index < data_length:
    if sentence_ids[end_index] != sentence_ids[end_index - 1]:
      if end_index - begin_index >= total_length:
        break
      cut_indices.append(end_index)
    end_index += 1

  a_begin = begin_index

  if not cut_indices or random.random() < no_cut_probability:
    # Segments A and B are contained within the same sentence.
    label = 0
    if not cut_indices:
      a_end = end_index
    else:
      a_end = random.choice(cut_indices)
    b_length = max(1, total_length - (a_end - a_begin))
    b_begin = random.randint(0, data_length - 1 - b_length)
    b_end = b_begin + b_length

    while b_begin > 0 and sentence_ids[b_begin - 1] == sentence_ids[b_begin]:
      b_begin -= 1
    while (b_end < data_length - 1 and
           sentence_ids[b_end - 1] == sentence_ids[b_end]):
      b_end += 1
  else:
    # Segments A and B are different sentences.
    label = 1
    a_end = random.choice(cut_indices)
    b_begin = a_end
    b_end = end_index

  while a_end - a_begin + b_end - b_begin > total_length:
    if a_end - a_begin > b_end - b_begin:
      # Delete only the right side for the LM objective.
      a_end -= 1
    else:
      b_end -= 1
  if a_end >= data_length or b_end >= data_length:
    logging.info("[_create_segments]: a_end %d or b_end %d >= data_length %d",
                 a_end, b_end, data_length)
    return None

  a_data = tokens[a_begin: a_end]
  b_data = tokens[b_begin: b_end]
  return a_data, b_data, label