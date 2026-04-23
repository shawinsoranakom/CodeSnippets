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
    state, next_state = kwargs['state'], kwargs['next_state']
    if state is not None and next_state is not None:
      pass
      #contexts = tf.concat(
      #    [tf.random_normal(tf.shape(state[:, :self._k]), dtype=tf.float64) +
      #     tf.random_shuffle(state[:, :self._k]),
      #     contexts[:, self._k:]], 1)

    return contexts, contexts