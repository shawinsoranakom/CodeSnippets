def _count_tokens(files,
                  file_byte_limit=1e6,
                  correct_strip=True,
                  master_char_set=None):
  """Return token counts of words in the files.

  Samples file_byte_limit bytes from each file, and counts the words that appear
  in the samples. The samples are semi-evenly distributed across the file.

  Args:
    files: List of filepaths
    file_byte_limit: Max number of bytes that will be read from each file.
    correct_strip: Whether to convert text to unicode before strip. This affects
      vocabulary generation for PY2. Sets correct_strip to False in PY2 to
      reproduce previous common public result. Sets correct_strip to True will
      let PY2 and PY3 get a consistent vocabulary.
    master_char_set: the char set.

  Returns:
    Dictionary mapping tokens to the number of times they appear in the sampled
    lines from the files.
  """
  if master_char_set is None:
    master_char_set = _ALPHANUMERIC_CHAR_SET

  token_counts = collections.defaultdict(int)

  for filepath in files:
    with tf.io.gfile.GFile(filepath, mode="r") as reader:
      file_byte_budget = file_byte_limit
      counter = 0
      lines_to_skip = int(reader.size() / (file_byte_budget * 2))
      for line in reader:
        if counter < lines_to_skip:
          counter += 1
        else:
          if file_byte_budget < 0:
            break
          if correct_strip:
            line = native_to_unicode(line)
          line = line.strip()
          file_byte_budget -= len(line)
          counter = 0

          # Add words to token counts
          for token in _split_string_to_tokens(
              native_to_unicode(line), master_char_set):
            token_counts[token] += 1
  return token_counts