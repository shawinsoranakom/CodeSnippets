def _test_end_to_end(self, constructor_type):
    params = self.make_params(train_epochs=1)
    _, _, producer = data_preprocessing.instantiate_pipeline(
        dataset=DATASET,
        data_dir=self.temp_data_dir,
        params=params,
        constructor_type=constructor_type,
        deterministic=True)

    producer.start()
    producer.join()
    assert producer._fatal_exception is None

    user_inv_map = {v: k for k, v in producer.user_map.items()}
    item_inv_map = {v: k for k, v in producer.item_map.items()}

    # ==========================================================================
    # == Training Data =========================================================
    # ==========================================================================
    g = tf.Graph()
    with g.as_default():
      input_fn = producer.make_input_fn(is_training=True)
      dataset = input_fn(params)

    first_epoch = self.drain_dataset(dataset=dataset, g=g)

    counts = defaultdict(int)
    train_examples = {
        True: set(),
        False: set(),
    }

    md5 = hashlib.md5()
    for features, labels in first_epoch:
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

        u_raw = user_inv_map[u]
        i_raw = item_inv_map[i]
        if ((u_raw, i_raw) in self.seen_pairs) != l:
          # The evaluation item is not considered during false negative
          # generation, so it will occasionally appear as a negative example
          # during training.
          assert not l
          self.assertEqual(i_raw, self.holdout[u_raw][1])
        train_examples[l].add((u_raw, i_raw))
        counts[(u_raw, i_raw)] += 1

    self.assertRegex(md5.hexdigest(), END_TO_END_TRAIN_MD5)

    num_positives_seen = len(train_examples[True])
    self.assertEqual(producer._train_pos_users.shape[0], num_positives_seen)

    # This check is more heuristic because negatives are sampled with
    # replacement. It only checks that negative generation is reasonably random.
    self.assertGreater(
        len(train_examples[False]) / NUM_NEG / num_positives_seen, 0.9)

    # This checks that the samples produced are independent by checking the
    # number of duplicate entries. If workers are not properly independent there
    # will be lots of repeated pairs.
    self.assertLess(np.mean(list(counts.values())), 1.1)

    # ==========================================================================
    # == Eval Data =============================================================
    # ==========================================================================
    with g.as_default():
      input_fn = producer.make_input_fn(is_training=False)
      dataset = input_fn(params)

    eval_data = self.drain_dataset(dataset=dataset, g=g)

    current_user = None
    md5 = hashlib.md5()
    for features in eval_data:
      data_list = [
          features[movielens.USER_COLUMN].flatten(),
          features[movielens.ITEM_COLUMN].flatten(),
          features[rconst.DUPLICATE_MASK].flatten()
      ]
      for i in data_list:
        md5.update(i.tobytes())

      for idx, (u, i, d) in enumerate(zip(*data_list)):
        u_raw = user_inv_map[u]
        i_raw = item_inv_map[i]
        if current_user is None:
          current_user = u

        # Ensure that users appear in blocks, as the evaluation logic expects
        # this structure.
        self.assertEqual(u, current_user)

        # The structure of evaluation data is 999 negative examples followed
        # by the holdout positive.
        if not (idx + 1) % (rconst.NUM_EVAL_NEGATIVES + 1):
          # Check that the last element in each chunk is the holdout item.
          self.assertEqual(i_raw, self.holdout[u_raw][1])
          current_user = None

        elif i_raw == self.holdout[u_raw][1]:
          # Because the holdout item is not given to the negative generation
          # process, it can appear as a negative. In that case, it should be
          # masked out as a duplicate. (Since the true positive is placed at
          # the end and would therefore lose the tie.)
          assert d

        else:
          # Otherwise check that the other 999 points for a user are selected
          # from the negatives.
          assert (u_raw, i_raw) not in self.seen_pairs

    self.assertRegex(md5.hexdigest(), END_TO_END_EVAL_MD5)