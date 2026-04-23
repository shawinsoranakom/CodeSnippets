def __init__(self, words, word_vocab, char_vocab):
    words = words[:]
    # Fix inconsistent tokenization between datasets
    for i in range(len(words)):
      if (words[i].lower() == '\'t' and i > 0 and
          words[i - 1].lower() in CONTRACTION_WORDS):
        words[i] = words[i - 1][-1] + words[i]
        words[i - 1] = words[i - 1][:-1]

    self.words = ([embeddings.START] +
                  [word_vocab[embeddings.normalize_word(w)] for w in words] +
                  [embeddings.END])
    self.chars = ([[embeddings.MISSING]] +
                  [[char_vocab[c] for c in embeddings.normalize_chars(w)]
                   for w in words] +
                  [[embeddings.MISSING]])