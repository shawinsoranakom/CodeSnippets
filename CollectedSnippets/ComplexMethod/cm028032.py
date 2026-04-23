def _make_minibatch(self, ids):
    examples = [self.examples[i] for i in ids]
    sentence_lengths = np.array([len(e.words) for e in examples])
    max_word_length = min(max(max(len(word) for word in e.chars)
                              for e in examples),
                          self._config.max_word_length)
    characters = [[[embeddings.PAD] + [embeddings.START] + w[:max_word_length] +
                   [embeddings.END] + [embeddings.PAD] for w in e.chars]
                  for e in examples]
    # the first and last words are masked because they are start/end tokens
    mask = build_array([[0] + [1] * (length - 2) + [0]
                        for length in sentence_lengths])
    words = build_array([e.words for e in examples])
    chars = build_array(characters, dtype='int16')
    return Minibatch(
        task_name=self.task_name,
        size=ids.size,
        examples=examples,
        ids=ids,
        teacher_predictions={},
        words=words,
        chars=chars,
        lengths=sentence_lengths,
        mask=mask,
    )