def reward_fn(*args, **kwargs):
      """Returns rewards, discounts."""
      reward_tuples = [
          reward_fn(*args, **kwargs) for reward_fn in reward_fns_list
      ]
      rewards_list = [reward_tuple[0] for reward_tuple in reward_tuples]
      discounts_list = [reward_tuple[1] for reward_tuple in reward_tuples]
      ndims = max([r.shape.ndims for r in rewards_list])
      if ndims > 1:  # expand reward shapes to allow broadcasting
        for i in range(len(rewards_list)):
          for _ in range(rewards_list[i].shape.ndims - ndims):
            rewards_list[i] = tf.expand_dims(rewards_list[i], axis=-1)
          for _ in range(discounts_list[i].shape.ndims - ndims):
            discounts_list[i] = tf.expand_dims(discounts_list[i], axis=-1)
      rewards = tf.add_n(
          [r * tf.to_float(w) for r, w in zip(rewards_list, reward_weights)])
      discounts = discounts_list[0]
      for d in discounts_list[1:]:
        discounts *= d

      return rewards, discounts