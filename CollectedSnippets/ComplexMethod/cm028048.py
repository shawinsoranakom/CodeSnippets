def __call__(self, batch_size, **kwargs):
    """Sample a batch of context.

    Args:
      batch_size: Batch size.
    Returns:
      Two [batch_size, num_context_dims] tensors.
    """
    spec = self._context_spec
    context_range = self._context_range
    if isinstance(context_range[0], (int, float)):
      contexts = tf.random_uniform(
          shape=[
              batch_size,
          ] + spec.shape.as_list(),
          minval=context_range[0],
          maxval=context_range[1],
          dtype=spec.dtype)
    elif isinstance(context_range[0], (list, tuple, np.ndarray)):
      assert len(spec.shape.as_list()) == 1
      assert spec.shape.as_list()[0] == len(context_range[0])
      assert spec.shape.as_list()[0] == len(context_range[1])
      contexts = tf.concat(
          [
              tf.random_uniform(
                  shape=[
                      batch_size, 1,
                  ] + spec.shape.as_list()[1:],
                  minval=context_range[0][i],
                  maxval=context_range[1][i],
                  dtype=spec.dtype) for i in range(spec.shape.as_list()[0])
          ],
          axis=1)
    else: raise NotImplementedError(context_range)
    self._validate_contexts(contexts)
    if 'sampler_fn' in kwargs:
      other_contexts = kwargs['sampler_fn']()
    else:
      other_contexts = contexts
    state, next_state = kwargs['state'], kwargs['next_state']
    if state is not None and next_state is not None:
      my_context_range = (np.array(context_range[1]) - np.array(context_range[0])) / 2 * np.ones(spec.shape.as_list())
      contexts = tf.concat(
          [0.1 * my_context_range[:self._k] *
           tf.random_normal(tf.shape(state[:, :self._k]), dtype=state.dtype) +
           tf.random_shuffle(state[:, :self._k]) - state[:, :self._k],
           other_contexts[:, self._k:]], 1)
      #contexts = tf.Print(contexts,
      #                    [contexts, tf.reduce_max(contexts, 0),
      #                     tf.reduce_min(state, 0), tf.reduce_max(state, 0)], 'contexts', summarize=15)
      next_contexts = tf.concat( #LALA
          [state[:, :self._k] + contexts[:, :self._k] - next_state[:, :self._k],
           other_contexts[:, self._k:]], 1)
      next_contexts = contexts  #LALA cosine
    else:
      next_contexts = contexts
    return tf.stop_gradient(contexts), tf.stop_gradient(next_contexts)