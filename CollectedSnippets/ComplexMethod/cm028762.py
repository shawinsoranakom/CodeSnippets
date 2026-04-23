def _tokenize_example(example, max_length, tokenizer, text_preprocessing=None):
  """Tokenizes words and breaks long example into short ones."""
  # Needs additional [CLS] and [SEP] tokens.
  max_length = max_length - 2
  new_examples = []
  new_example = InputExample(sentence_id=example.sentence_id, sub_sentence_id=0)
  if any([x < 0 for x in example.label_ids]):
    raise ValueError("Unexpected negative label_id: %s" % example.label_ids)

  for i, word in enumerate(example.words):
    if text_preprocessing:
      word = text_preprocessing(word)
    subwords = tokenizer.tokenize(word)
    if (not subwords or len(subwords) > max_length) and word:
      subwords = [_UNK_TOKEN]

    if len(subwords) + len(new_example.words) > max_length:
      # Start a new example.
      new_examples.append(new_example)
      last_sub_sentence_id = new_example.sub_sentence_id
      new_example = InputExample(
          sentence_id=example.sentence_id,
          sub_sentence_id=last_sub_sentence_id + 1)

    for j, subword in enumerate(subwords):
      # Use the real label for the first subword, and pad label for
      # the remainings.
      subword_label = example.label_ids[i] if j == 0 else _PADDING_LABEL_ID
      new_example.add_word_and_label_id(subword, subword_label)

  if new_example.words:
    new_examples.append(new_example)

  return new_examples