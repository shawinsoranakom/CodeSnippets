def tokens(doc):
  """Given a Document, produces character or word tokens.

  Tokens can be either characters, or word-level tokens (unigrams and/or
  bigrams).

  Args:
    doc: Document to produce tokens from.

  Yields:
    token

  Raises:
    ValueError: if all FLAGS.{output_unigrams, output_bigrams, output_char}
      are False.
  """
  if not (FLAGS.output_unigrams or FLAGS.output_bigrams or FLAGS.output_char):
    raise ValueError(
        'At least one of {FLAGS.output_unigrams, FLAGS.output_bigrams, '
        'FLAGS.output_char} must be true')

  content = doc.content.strip()
  if FLAGS.lowercase:
    content = content.lower()

  if FLAGS.output_char:
    for char in content:
      yield char

  else:
    tokens_ = data_utils.split_by_punct(content)
    for i, token in enumerate(tokens_):
      if FLAGS.output_unigrams:
        yield token

      if FLAGS.output_bigrams:
        previous_token = (tokens_[i - 1] if i > 0 else data_utils.EOS_TOKEN)
        bigram = '_'.join([previous_token, token])
        yield bigram
        if (i + 1) == len(tokens_):
          bigram = '_'.join([token, data_utils.EOS_TOKEN])
          yield bigram