def convert_single_example(example_index, example, label_list, max_seq_length,
                           tokenize_fn, use_bert_format):
  """Converts a single `InputExample` into a single `InputFeatures`."""

  if isinstance(example, PaddingInputExample):
    return InputFeatures(
        input_ids=[0] * max_seq_length,
        input_mask=[1] * max_seq_length,
        segment_ids=[0] * max_seq_length,
        label_id=0,
        is_real_example=False)

  if label_list is not None:
    label_map = {}
    for (i, label) in enumerate(label_list):
      label_map[label] = i

  tokens_a = tokenize_fn(example.text_a)
  tokens_b = None
  if example.text_b:
    tokens_b = tokenize_fn(example.text_b)

  if tokens_b:
    # Modifies `tokens_a` and `tokens_b` in place so that the total
    # length is less than the specified length.
    # Account for two [SEP] & one [CLS] with "- 3"
    _truncate_seq_pair(tokens_a, tokens_b, max_seq_length - 3)
  else:
    # Account for one [SEP] & one [CLS] with "- 2"
    if len(tokens_a) > max_seq_length - 2:
      tokens_a = tokens_a[:max_seq_length - 2]

  tokens = []
  segment_ids = []
  for token in tokens_a:
    tokens.append(token)
    segment_ids.append(SEG_ID_A)
  tokens.append(data_utils.SEP_ID)
  segment_ids.append(SEG_ID_A)

  if tokens_b:
    for token in tokens_b:
      tokens.append(token)
      segment_ids.append(SEG_ID_B)
    tokens.append(data_utils.SEP_ID)
    segment_ids.append(SEG_ID_B)

  if use_bert_format:
    tokens.insert(0, data_utils.CLS_ID)
    segment_ids.insert(0, data_utils.SEG_ID_CLS)
  else:
    tokens.append(data_utils.CLS_ID)
    segment_ids.append(data_utils.SEG_ID_CLS)

  input_ids = tokens

  # The mask has 0 for real tokens and 1 for padding tokens. Only real
  # tokens are attended to.
  input_mask = [0] * len(input_ids)

  # Zero-pad up to the sequence length.
  if len(input_ids) < max_seq_length:
    delta_len = max_seq_length - len(input_ids)
    if use_bert_format:
      input_ids = input_ids + [0] * delta_len
      input_mask = input_mask + [1] * delta_len
      segment_ids = segment_ids + [data_utils.SEG_ID_PAD] * delta_len
    else:
      input_ids = [0] * delta_len + input_ids
      input_mask = [1] * delta_len + input_mask
      segment_ids = [data_utils.SEG_ID_PAD] * delta_len + segment_ids

  assert len(input_ids) == max_seq_length
  assert len(input_mask) == max_seq_length
  assert len(segment_ids) == max_seq_length

  if label_list is not None:
    label_id = label_map[example.label]
  else:
    label_id = example.label
  if example_index < 5:
    logging.info("*** Example ***")
    logging.info("guid: %s", (example.guid))
    logging.info("input_ids: %s", " ".join([str(x) for x in input_ids]))
    logging.info("input_mask: %s", " ".join([str(x) for x in input_mask]))
    logging.info("segment_ids: %s", " ".join([str(x) for x in segment_ids]))
    logging.info("label: %s (id = %d)", example.label, label_id)

  feature = InputFeatures(
      input_ids=input_ids,
      input_mask=input_mask,
      segment_ids=segment_ids,
      label_id=label_id)
  return feature