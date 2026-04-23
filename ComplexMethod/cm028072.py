def create_epoch_tuples(self, net):
    """Creates epoch tuples with the hard-negative re-mining.

    Negative examples are selected from clusters different than the cluster
    of the query image, as the clusters are ideally non-overlapping. For
    every query image we choose  hard-negatives, that is, non-matching images
    with the most similar descriptor. Hard-negatives depend on the current
    CNN parameters. K-nearest neighbors from all non-matching images are
    selected. Query images are selected randomly. Positives examples are
    fixed for the related query image during the whole training process.

    Args:
      net: Model, network to be used for negative re-mining.

    Raises:
      ValueError: If the pool_size is smaller than the number of negative
        images per tuple.

    Returns:
      avg_l2: Float, average negative L2-distance.
    """
    self._n = 0

    if self._num_negatives < self._pool_size:
      raise ValueError("Unable to create epoch tuples. Negative pool_size "
                       "should be larger than the number of negative images "
                       "per tuple.")

    global_features_utils.debug_and_log(
            '>> Creating tuples for an epoch of {}-{}...'.format(self._name,
                                                                 self._mode),
            True)
    global_features_utils.debug_and_log(">> Used network: ", True)
    global_features_utils.debug_and_log(net.meta_repr(), True)

    ## Selecting queries.
    # Draw `num_queries` random queries for the tuples.
    idx_list = np.arange(len(self._query_pool))
    np.random.shuffle(idx_list)
    idxs2query_pool = idx_list[:self._num_queries]
    self._qidxs = [self._query_pool[i] for i in idxs2query_pool]

    ## Selecting positive pairs.
    # Positives examples are fixed for each query during the whole training
    # process.
    self._pidxs = [self._positive_pool[i] for i in idxs2query_pool]

    ## Selecting negative pairs.
    # If `num_negatives` = 0 create dummy nidxs.
    # Useful when only positives used for training.
    if self._num_negatives == 0:
      self._nidxs = [[] for _ in range(len(self._qidxs))]
      return 0

    # Draw pool_size random images for pool of negatives images.
    neg_idx_list = np.arange(len(self.images))
    np.random.shuffle(neg_idx_list)
    neg_images_idxs = neg_idx_list[:self._pool_size]

    global_features_utils.debug_and_log(
            '>> Extracting descriptors for query images...', debug=True)

    img_list = self._img_names_to_full_path([self.images[i] for i in
                                             self._qidxs])
    qvecs = global_model.extract_global_descriptors_from_list(
            net,
            images=img_list,
            image_size=self._imsize,
            print_freq=self._print_freq)

    global_features_utils.debug_and_log(
            '>> Extracting descriptors for negative pool...', debug=True)

    poolvecs = global_model.extract_global_descriptors_from_list(
            net,
            images=self._img_names_to_full_path([self.images[i] for i in
                                                 neg_images_idxs]),
            image_size=self._imsize,
            print_freq=self._print_freq)

    global_features_utils.debug_and_log('>> Searching for hard negatives...',
                                        debug=True)

    # Compute dot product scores and ranks.
    scores = tf.linalg.matmul(poolvecs, qvecs, transpose_a=True)
    ranks = tf.argsort(scores, axis=0, direction='DESCENDING')

    sum_ndist = 0.
    n_ndist = 0.

    # Selection of negative examples.
    self._nidxs = []

    for q, qidx in enumerate(self._qidxs):
      # We are not using the query cluster, those images are potentially
      # positive.
      qcluster = self._clusters[qidx]
      clusters = [qcluster]
      nidxs = []
      rank = 0

      while len(nidxs) < self._num_negatives:
        if rank >= tf.shape(ranks)[0]:
          raise ValueError("Unable to create epoch tuples. Number of required "
                           "negative images is larger than the number of "
                           "clusters in the dataset.")
        potential = neg_images_idxs[ranks[rank, q]]
        # Take at most one image from the same cluster.
        if not self._clusters[potential] in clusters:
          nidxs.append(potential)
          clusters.append(self._clusters[potential])
          dist = tf.norm(qvecs[:, q] - poolvecs[:, ranks[rank, q]],
                         axis=0).numpy()
          sum_ndist += dist
          n_ndist += 1
        rank += 1

      self._nidxs.append(nidxs)

    global_features_utils.debug_and_log(
            '>> Average negative l2-distance: {:.2f}'.format(
                    sum_ndist / n_ndist))

    # Return average negative L2-distance.
    return sum_ndist / n_ndist