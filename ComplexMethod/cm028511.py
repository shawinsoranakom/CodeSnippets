def prepare(self, negative_multiplier=3.):
    """Constructs negative sampling and handling train/test differences."""
    desc = ("prepare data for training"
            if self.is_train else "prepare data for testing")
    total_missed_entities = 0
    total_entities = 0
    for sid, (tokens, labels) in tqdm(enumerate(self.read_file()), desc=desc):
      self.all_tokens.append(tokens)
      self.all_labels.append(labels)
      entity_spans = self.bio_labels_to_spans(labels)
      entity_spans_dict = {
          (start, end): ent_type for start, end, ent_type in entity_spans
      }
      num_entities = len(entity_spans_dict)
      num_negatives = int(
          (len(tokens) + num_entities * 10) * negative_multiplier)
      num_negatives = min(num_negatives, len(tokens) * (len(tokens) + 1) // 2)
      min_words = 1
      max_words = len(tokens)
      total_entities += len(entity_spans)

      spans = []
      if self.is_train:
        is_token_entity_prefix = [0] * (len(tokens) + 1)
        for start, end, _ in entity_spans:
          for i in range(start, end + 1):
            is_token_entity_prefix[i + 1] = 1
        for i in range(len(tokens)):
          is_token_entity_prefix[i + 1] += is_token_entity_prefix[i]

        negative_spans = []
        negative_spans_probs = []
        for n_words in range(min_words, max_words + 1):
          for i in range(len(tokens) - n_words + 1):
            j = i + n_words - 1
            ent_type = entity_spans_dict.get((i, j), "O")
            if not self.is_train or ent_type != "O":
              spans.append((i, j, "mask", ent_type))
            else:
              negative_spans.append((i, j, "mask", ent_type))
              intersection_size = (is_token_entity_prefix[j + 1] -
                                   is_token_entity_prefix[i] + 1) / (
                                       j + 1 - i)
              negative_spans_probs.append(math.e**intersection_size)

        if negative_spans and num_negatives > 0:
          negative_spans_probs = np.array(negative_spans_probs) / np.sum(
              negative_spans_probs)
          negative_span_indices = np.random.choice(
              len(negative_spans),
              num_negatives,
              replace=True,
              p=negative_spans_probs)
          spans.extend([negative_spans[x] for x in negative_span_indices])
      else:
        for n_words in range(min_words, max_words + 1):
          for i in range(len(tokens) - n_words + 1):
            j = i + n_words - 1
            ent_type = entity_spans_dict.get((i, j), "O")
            spans.append((i, j, "mask", ent_type))

      for instance in self.process_word_list_and_spans_to_inputs(
          sid, tokens, spans):
        self.data.append(instance)
    print(f"{total_missed_entities}/{total_entities} are ignored due to length")
    print(f"Total {self.__len__()} instances")