def negative_distance(states,
                      actions,
                      rewards,
                      next_states,
                      contexts,
                      state_scales=1.0,
                      goal_scales=1.0,
                      reward_scales=1.0,
                      weight_index=None,
                      weight_vector=None,
                      summarize=False,
                      termination_epsilon=1e-4,
                      state_indices=None,
                      goal_indices=None,
                      vectorize=False,
                      relative_context=False,
                      diff=False,
                      norm='L2',
                      epsilon=1e-10,
                      bonus_epsilon=0., #5.,
                      offset=0.0):
  """Returns the negative euclidean distance between next_states and contexts.

  Args:
    states: A [batch_size, num_state_dims] Tensor representing a batch
        of states.
    actions: A [batch_size, num_action_dims] Tensor representing a batch
      of actions.
    rewards: A [batch_size] Tensor representing a batch of rewards.
    next_states: A [batch_size, num_state_dims] Tensor representing a batch
      of next states.
    contexts: A list of [batch_size, num_context_dims] Tensor representing
      a batch of contexts.
    state_scales: multiplicative scale for (next) states. A scalar or 1D tensor,
      must be broadcastable to number of state dimensions.
    goal_scales: multiplicative scale for goals. A scalar or 1D tensor,
      must be broadcastable to number of goal dimensions.
    reward_scales: multiplicative scale for rewards. A scalar or 1D tensor,
      must be broadcastable to number of reward dimensions.
    weight_index: (integer) The context list index that specifies weight.
    weight_vector: (a number or a list or Numpy array) The weighting vector,
      broadcastable to `next_states`.
    summarize: (boolean) enable summary ops.
    termination_epsilon: terminate if dist is less than this quantity.
    state_indices: (a list of integers) list of state indices to select.
    goal_indices: (a list of integers) list of goal indices to select.
    vectorize: Return a vectorized form.
    norm: L1 or L2.
    epsilon: small offset to ensure non-negative/zero distance.

  Returns:
    A new tf.float32 [batch_size] rewards Tensor, and
      tf.float32 [batch_size] discounts tensor.
  """
  del actions, rewards  # Unused
  stats = {}
  record_tensor(next_states, state_indices, stats, 'next_states')
  states = index_states(states, state_indices)
  next_states = index_states(next_states, state_indices)
  goals = index_states(contexts[0], goal_indices)
  if relative_context:
    goals = states + goals
  sq_dists = tf.squared_difference(next_states * state_scales,
                                   goals * goal_scales)
  old_sq_dists = tf.squared_difference(states * state_scales,
                                       goals * goal_scales)
  record_tensor(sq_dists, None, stats, 'sq_dists')
  if weight_vector is not None:
    sq_dists *= tf.convert_to_tensor(weight_vector, dtype=next_states.dtype)
    old_sq_dists *= tf.convert_to_tensor(weight_vector, dtype=next_states.dtype)
  if weight_index is not None:
    #sq_dists *= contexts[weight_index]
    weights = tf.abs(index_states(contexts[0], weight_index))
    #weights /= tf.reduce_sum(weights, -1, keepdims=True)
    sq_dists *= weights
    old_sq_dists *= weights
  if norm == 'L1':
    dist = tf.sqrt(sq_dists + epsilon)
    old_dist = tf.sqrt(old_sq_dists + epsilon)
    if not vectorize:
      dist = tf.reduce_sum(dist, -1)
      old_dist = tf.reduce_sum(old_dist, -1)
  elif norm == 'L2':
    if vectorize:
      dist = sq_dists
      old_dist = old_sq_dists
    else:
      dist = tf.reduce_sum(sq_dists, -1)
      old_dist = tf.reduce_sum(old_sq_dists, -1)
    dist = tf.sqrt(dist + epsilon)  # tf.gradients fails when tf.sqrt(-0.0)
    old_dist = tf.sqrt(old_dist + epsilon)  # tf.gradients fails when tf.sqrt(-0.0)
  else:
    raise NotImplementedError(norm)
  discounts = dist > termination_epsilon
  if summarize:
    with tf.name_scope('RewardFn/'):
      tf.summary.scalar('mean_dist', tf.reduce_mean(dist))
      tf.summary.histogram('dist', dist)
      summarize_stats(stats)
  bonus = tf.to_float(dist < bonus_epsilon)
  dist *= reward_scales
  old_dist *= reward_scales
  if diff:
    return bonus + offset + tf.to_float(old_dist - dist), tf.to_float(discounts)
  return bonus + offset + tf.to_float(-dist), tf.to_float(discounts)