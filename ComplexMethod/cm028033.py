def get_unlabeled_sentences(self):
    while True:
      file_ids_and_names = sorted([
          (int(fname.split('-')[1].replace('.txt', '')), fname) for fname in
          tf.gfile.ListDirectory(self.config.unsupervised_data)])
      for fid, fname in file_ids_and_names:
        if fid < self.current_file:
          continue
        self.current_file = fid
        self.current_line = 0
        with tf.gfile.FastGFile(os.path.join(self.config.unsupervised_data,
                                             fname), 'r') as f:
          for i, line in enumerate(f):
            if i < self.current_line:
              continue
            self.current_line = i
            words = line.strip().split()
            if len(words) < self.config.max_sentence_length:
              yield words
      self.current_file = 0
      self.current_line = 0
      if self._one_pass:
        break