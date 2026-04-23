def build(self):
    utils.log('loading pretrained embeddings from',
              self.config.pretrained_embeddings_file)
    for special in SPECIAL_TOKENS:
      self._add_vector(special)
    for extra in _EXTRA_WORDS:
      self._add_vector(extra)
    with tf.gfile.GFile(
        self.config.pretrained_embeddings_file, 'r') as f:
      for i, line in enumerate(f):
        if i % 10000 == 0:
          utils.log('on line', i)

        split = line.decode('utf8').split()
        w = normalize_word(split[0])

        try:
          vec = np.array(map(float, split[1:]), dtype='float32')
          if vec.size != self.vector_size:
            utils.log('vector for line', i, 'has size', vec.size, 'so skipping')
            utils.log(line[:100] + '...')
            continue
        except:
          utils.log('can\'t parse line', i, 'so skipping')
          utils.log(line[:100] + '...')
          continue
        if w not in self.vocabulary:
          self.vocabulary[w] = len(self.vectors)
          self.vectors.append(vec)
    utils.log('writing vectors!')
    self._write()