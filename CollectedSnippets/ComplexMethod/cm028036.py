def label_mapping(self):
    if not self._config.for_preprocessing:
      return utils.load_cpickle(self.label_mapping_path)

    tag_counts = collections.Counter()
    train_tags = set()
    for split in ['train', 'dev', 'test']:
      for words, tags in self.get_labeled_sentences(split):
        if not self._is_token_level:
          span_labels = tagging_utils.get_span_labels(tags)
          tags = tagging_utils.get_tags(
              span_labels, len(words), self._config.label_encoding)
        for tag in tags:
          if self._task_name == 'depparse':
            tag = tag.split('-')[1]
          tag_counts[tag] += 1
          if split == 'train':
            train_tags.add(tag)
    if self._task_name == 'ccg':
      # for CCG, there are tags in the test sets that aren't in the train set
      # all tags not in the train set get mapped to a special label
      # the model will never predict this label because it never sees it in the
      # training set
      not_in_train_tags = []
      for tag, count in tag_counts.items():
        if tag not in train_tags:
          not_in_train_tags.append(tag)
      label_mapping = {
          label: i for i, label in enumerate(sorted(filter(
            lambda t: t not in not_in_train_tags, tag_counts.keys())))
      }
      n = len(label_mapping)
      for tag in not_in_train_tags:
        label_mapping[tag] = n
    else:
      labels = sorted(tag_counts.keys())
      if self._task_name == 'depparse':
        labels.remove('root')
        labels.insert(0, 'root')
      label_mapping = {label: i for i, label in enumerate(labels)}
    return label_mapping