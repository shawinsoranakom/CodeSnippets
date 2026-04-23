def featurize_example(self, ex_index, example, label_list, max_seq_length,
                        tokenizer):
    """Here we concate sentence1, sentence2, word together with [SEP] tokens."""
    del label_list
    tokens_a = tokenizer.tokenize(example.text_a)
    tokens_b = tokenizer.tokenize(example.text_b)
    tokens_word = tokenizer.tokenize(example.word)

    # Modifies `tokens_a` and `tokens_b` in place so that the total
    # length is less than the specified length.
    # Account for [CLS], [SEP], [SEP], [SEP] with "- 4"
    # Here we only pop out the first two sentence tokens.
    _truncate_seq_pair(tokens_a, tokens_b,
                       max_seq_length - 4 - len(tokens_word))

    seg_id_a = 0
    seg_id_b = 1
    seg_id_c = 2
    seg_id_cls = 0
    seg_id_pad = 0

    tokens = []
    segment_ids = []
    tokens.append("[CLS]")
    segment_ids.append(seg_id_cls)
    for token in tokens_a:
      tokens.append(token)
      segment_ids.append(seg_id_a)
    tokens.append("[SEP]")
    segment_ids.append(seg_id_a)

    for token in tokens_b:
      tokens.append(token)
      segment_ids.append(seg_id_b)

    tokens.append("[SEP]")
    segment_ids.append(seg_id_b)

    for token in tokens_word:
      tokens.append(token)
      segment_ids.append(seg_id_c)

    tokens.append("[SEP]")
    segment_ids.append(seg_id_c)

    input_ids = tokenizer.convert_tokens_to_ids(tokens)

    # The mask has 1 for real tokens and 0 for padding tokens. Only real
    # tokens are attended to.
    input_mask = [1] * len(input_ids)

    # Zero-pad up to the sequence length.
    while len(input_ids) < max_seq_length:
      input_ids.append(0)
      input_mask.append(0)
      segment_ids.append(seg_id_pad)

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    label_id = example.label
    if ex_index < 5:
      logging.info("*** Example ***")
      logging.info("guid: %s", (example.guid))
      logging.info("tokens: %s",
                   " ".join([tokenization.printable_text(x) for x in tokens]))
      logging.info("input_ids: %s", " ".join([str(x) for x in input_ids]))
      logging.info("input_mask: %s", " ".join([str(x) for x in input_mask]))
      logging.info("segment_ids: %s", " ".join([str(x) for x in segment_ids]))
      logging.info("label: %s (id = %s)", example.label, str(label_id))
      logging.info("weight: %s", example.weight)
      logging.info("example_id: %s", example.example_id)

    feature = InputFeatures(
        input_ids=input_ids,
        input_mask=input_mask,
        segment_ids=segment_ids,
        label_id=label_id,
        is_real_example=True,
        weight=example.weight,
        example_id=example.example_id)

    return feature