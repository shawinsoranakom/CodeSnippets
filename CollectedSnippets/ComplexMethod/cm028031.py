def get_minibatches(self, minibatch_size):
    by_bucket = collections.defaultdict(list)
    for i, e in enumerate(self.examples):
      by_bucket[get_bucket(self._config, len(e.words))].append(i)

    # save memory by weighting examples so longer sentences have
    # smaller minibatches.
    weight = lambda ind: np.sqrt(len(self.examples[ind].words))
    total_weight = float(sum(weight(i) for i in range(len(self.examples))))
    weight_per_batch = minibatch_size * total_weight / len(self.examples)
    cumulative_weight = 0.0
    id_batches = []
    for _, ids in by_bucket.iteritems():
      ids = np.array(ids)
      np.random.shuffle(ids)
      curr_batch, curr_weight = [], 0.0
      for i, curr_id in enumerate(ids):
        curr_batch.append(curr_id)
        curr_weight += weight(curr_id)
        if (i == len(ids) - 1 or cumulative_weight + curr_weight >=
            (len(id_batches) + 1) * weight_per_batch):
          cumulative_weight += curr_weight
          id_batches.append(np.array(curr_batch))
          curr_batch, curr_weight = [], 0.0
    random.shuffle(id_batches)

    for id_batch in id_batches:
      yield self._make_minibatch(id_batch)