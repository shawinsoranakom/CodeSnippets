def create_training_instances(
    input_files,
    tokenizer,
    processor_text_fn,
    max_seq_length,
    dupe_factor,
    short_seq_prob,
    masked_lm_prob,
    max_predictions_per_seq,
    rng,
    do_whole_word_mask=False,
    max_ngram_size=None,
):
  """Create `TrainingInstance`s from raw text."""
  all_documents = [[]]

  # Input file format:
  # (1) One sentence per line. These should ideally be actual sentences, not
  # entire paragraphs or arbitrary spans of text. (Because we use the
  # sentence boundaries for the "next sentence prediction" task).
  # (2) Blank lines between documents. Document boundaries are needed so
  # that the "next sentence prediction" task doesn't span between documents.
  for input_file in input_files:
    with tf.io.gfile.GFile(input_file, "rb") as reader:
      for line in reader:
        line = processor_text_fn(line)

        # Empty lines are used as document delimiters
        if not line:
          all_documents.append([])
        tokens = tokenizer.tokenize(line)
        if tokens:
          all_documents[-1].append(tokens)

  # Remove empty documents
  all_documents = [x for x in all_documents if x]
  rng.shuffle(all_documents)

  vocab_words = list(tokenizer.vocab.keys())
  instances = []
  for _ in range(dupe_factor):
    for document_index in range(len(all_documents)):
      instances.extend(
          create_instances_from_document(
              all_documents, document_index, max_seq_length, short_seq_prob,
              masked_lm_prob, max_predictions_per_seq, vocab_words, rng,
              do_whole_word_mask, max_ngram_size))

  rng.shuffle(instances)
  return instances