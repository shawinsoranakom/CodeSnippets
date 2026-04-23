def _test_fresh_randomness(self, constructor_type):
    train_epochs = 5
    params = self.make_params(train_epochs=train_epochs)
    _, _, producer = data_preprocessing.instantiate_pipeline(
        dataset=DATASET,
        data_dir=self.temp_data_dir,
        params=params,
        constructor_type=constructor_type,
        deterministic=True)

    producer.start()

    results = []
    g = tf.Graph()
    with g.as_default():
      for _ in range(train_epochs):
        input_fn = producer.make_input_fn(is_training=True)
        dataset = input_fn(params)
        results.extend(self.drain_dataset(dataset=dataset, g=g))

    producer.join()
    assert producer._fatal_exception is None

    positive_counts, negative_counts = defaultdict(int), defaultdict(int)
    md5 = hashlib.md5()
    for features, labels in results:
      data_list = [
          features[movielens.USER_COLUMN].flatten(),
          features[movielens.ITEM_COLUMN].flatten(),
          features[rconst.VALID_POINT_MASK].flatten(),
          labels.flatten()
      ]
      for i in data_list:
        md5.update(i.tobytes())

      for u, i, v, l in zip(*data_list):
        if not v:
          continue  # ignore padding

        if l:
          positive_counts[(u, i)] += 1
        else:
          negative_counts[(u, i)] += 1

    self.assertRegex(md5.hexdigest(), FRESH_RANDOMNESS_MD5)

    # The positive examples should appear exactly once each epoch
    self.assertAllEqual(
        list(positive_counts.values()), [train_epochs for _ in positive_counts])

    # The threshold for the negatives is heuristic, but in general repeats are
    # expected, but should not appear too frequently.

    pair_cardinality = NUM_USERS * NUM_ITEMS
    neg_pair_cardinality = pair_cardinality - len(self.seen_pairs)

    # Approximation for the expectation number of times that a particular
    # negative will appear in a given epoch. Implicit in this calculation is the
    # treatment of all negative pairs as equally likely. Normally is not
    # necessarily reasonable; however the generation in self.setUp() will
    # approximate this behavior sufficiently for heuristic testing.
    e_sample = len(self.seen_pairs) * NUM_NEG / neg_pair_cardinality

    # The frequency of occurance of a given negative pair should follow an
    # approximately binomial distribution in the limit that the cardinality of
    # the negative pair set >> number of samples per epoch.
    approx_pdf = scipy.stats.binom.pmf(
        k=np.arange(train_epochs + 1), n=train_epochs, p=e_sample)

    # Tally the actual observed counts.
    count_distribution = [0 for _ in range(train_epochs + 1)]
    for i in negative_counts.values():
      i = min([i, train_epochs])  # round down tail for simplicity.
      count_distribution[i] += 1
    count_distribution[0] = neg_pair_cardinality - sum(count_distribution[1:])

    # Check that the frequency of negative pairs is approximately binomial.
    for i in range(train_epochs + 1):
      if approx_pdf[i] < 0.05:
        continue  # Variance will be high at the tails.

      observed_fraction = count_distribution[i] / neg_pair_cardinality
      deviation = (2 * abs(observed_fraction - approx_pdf[i]) /
                   (observed_fraction + approx_pdf[i]))

      self.assertLess(deviation, 0.2)