def preprocess_and_tokenize_input_files(
    input_files: Iterable[str],
    tokenizer: tokenization.FullSentencePieceTokenizer,
    use_eod: bool = True,
    do_lower_case: bool = False,
    log_example_freq: int = 100000) -> List[Tuple[np.array, np.array]]:
  """Preprocesses and encodes raw text from input files.

  This function preprocesses raw text and encodes them into tokens using a
  `SentencePieceModel` tokenization method. This also provides the sentence
  indicator for each token.

  Args:
    input_files: The list of input file names.
    tokenizer: The SentencePiece tokenizer that has the attribute `sp_model`.
    use_eod: Whether or not to use an EOD indicator. If `False`, then EOD is
      not included.
    do_lower_case: Whether or not to apply lower casing during raw text
      preprocessing.
    log_example_freq: The optional field for how many lines to process before
      emitting an info log.

  Returns:
    The preprocessed list. Each entry in the list is a tuple consisting of
    the token IDs and the sentence IDs.

  """
  all_data = []
  eod_symbol = special_symbols["<eod>"]

  total_number_of_lines = 0

  # Input file format:
  # (1) One sentence per line. These should ideally be actual sentences, not
  # entire paragraphs or arbitrary spans of text. (Because we use the
  # sentence boundaries for the "next sentence prediction" task).
  # (2) Blank lines between documents. Document boundaries are needed so
  # that the "next sentence prediction" task doesn't span between documents.
  for input_file in input_files:
    line_count = 0
    logging.info("Preprocessing %s", input_file)

    all_tokens = []
    all_sentence_ids = []

    sentence_id = True

    with tf.io.gfile.GFile(input_file, "rb") as reader:
      while True:
        line = tokenization.convert_to_unicode(reader.readline())
        if not line:
          break

        line_count += 1
        if line_count % log_example_freq == 0:
          logging.info("Loading line %d", line_count)

        line = line.strip()

        if not line:
          if use_eod:
            token_ids = [eod_symbol]
            sentence_id = not sentence_id
          else:
            continue
        else:
          preprocessed_line = _preprocess_line(
              line=line, do_lower_case=do_lower_case)
          token_ids = tokenization.encode_ids(
              sp_model=tokenizer.sp_model, text=preprocessed_line)

        all_tokens.extend(token_ids)
        all_sentence_ids.extend([sentence_id] * len(token_ids))
        sentence_id = not sentence_id
      logging.info("Finished processing %s. Number of lines: %d",
                   input_file, line_count)
      if line_count == 0:
        continue
      total_number_of_lines += line_count
      all_tokens = np.array(all_tokens, dtype=np.int64)
      all_sentence_ids = np.array(all_sentence_ids, dtype=bool)
      all_data.append((all_tokens, all_sentence_ids))

  logging.info("Completed text preprocessing. Total number of lines: %d",
               total_number_of_lines)
  return all_data