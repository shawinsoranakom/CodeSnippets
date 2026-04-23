def _create_examples(self, split_name, set_type):
    """Creates examples for the training/dev/test sets."""
    if split_name not in self.dataset:
      raise ValueError("Split {} not available.".format(split_name))
    dataset = self.dataset[split_name].as_numpy_iterator()
    examples = []
    text_b, weight = None, None
    for i, example in enumerate(dataset):
      guid = "%s-%s" % (set_type, i)
      if set_type == "test":
        text_a = self.process_text_fn(example[self.test_text_key])
        if self.test_text_b_key:
          text_b = self.process_text_fn(example[self.test_text_b_key])
        label = self.test_label
      else:
        text_a = self.process_text_fn(example[self.text_key])
        if self.text_b_key:
          text_b = self.process_text_fn(example[self.text_b_key])
        label = self.label_type(example[self.label_key])
        if self.skip_label is not None and label == self.skip_label:
          continue
      if self.weight_key:
        weight = float(example[self.weight_key])
      examples.append(
          InputExample(
              guid=guid,
              text_a=text_a,
              text_b=text_b,
              label=label,
              weight=weight))
    return examples