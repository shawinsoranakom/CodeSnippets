def _create_examples(self, lines, set_type):
    """Creates examples for the training and dev sets."""
    examples = []
    for (i, line) in enumerate(lines):
      if i == 0 and self.contains_header and set_type != "test":
        continue
      if i == 0 and self.test_contains_header and set_type == "test":
        continue
      guid = "%s-%s" % (set_type, i)

      a_column = (
          self.text_a_column if set_type != "test" else self.test_text_a_column)
      b_column = (
          self.text_b_column if set_type != "test" else self.test_text_b_column)

      # there are some incomplete lines in QNLI
      if len(line) <= a_column:
        logging.warning("Incomplete line, ignored.")
        continue
      text_a = line[a_column]

      if b_column is not None:
        if len(line) <= b_column:
          logging.warning("Incomplete line, ignored.")
          continue
        text_b = line[b_column]
      else:
        text_b = None

      if set_type == "test":
        label = self.get_labels()[0]
      else:
        if len(line) <= self.label_column:
          logging.warning("Incomplete line, ignored.")
          continue
        label = float(line[self.label_column])
      examples.append(
          InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))

    return examples