def _read_one_file(file_name, label_list):
  """Reads one file and returns a list of `InputExample` instances."""
  lines = tf.io.gfile.GFile(file_name, "r").readlines()
  examples = []
  label_id_map = {label: i for i, label in enumerate(label_list)}
  sentence_id = 0
  example = InputExample(sentence_id=0)
  for line in lines:
    line = line.strip("\n")
    if line:
      # The format is: <token>\t<label> for train/dev set and <token> for test.
      items = line.split("\t")
      assert len(items) == 2 or len(items) == 1
      token = items[0].strip()

      # Assign a dummy label_id for test set
      label_id = label_id_map[items[1].strip()] if len(items) == 2 else 0
      example.add_word_and_label_id(token, label_id)
    else:
      # Empty line indicates a new sentence.
      if example.words:
        examples.append(example)
        sentence_id += 1
        example = InputExample(sentence_id=sentence_id)

  if example.words:
    examples.append(example)
  return examples