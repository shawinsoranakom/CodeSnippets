def __call__(self, batch_size, **kwargs):
    """Sample a batch of context.

    Args:
      batch_size: Batch size.
    Returns:
      Two [batch_size, num_context_dims] tensors.
    """
    batch = self._replay.GetRandomBatch(batch_size)
    next_states = batch[4]
    if self._prefetch_queue_capacity > 0:
      batch_queue = slim.prefetch_queue.prefetch_queue(
          [next_states],
          capacity=self._prefetch_queue_capacity,
          name='%s/batch_context_queue' % self._scope)
      next_states = batch_queue.dequeue()
    if self._override_indices is not None:
      assert self._context_range is not None and isinstance(
          self._context_range[0], (int, long, float))
      next_states = tf.concat(
          [
              tf.random_uniform(
                  shape=next_states[:, :1].shape,
                  minval=self._context_range[0],
                  maxval=self._context_range[1],
                  dtype=next_states.dtype)
              if i in self._override_indices else next_states[:, i:i + 1]
              for i in range(self._context_spec.shape.as_list()[0])
          ],
          axis=1)
    if self._state_indices is not None:
      next_states = tf.concat(
          [
              next_states[:, i:i + 1]
              for i in range(self._context_spec.shape.as_list()[0])
          ],
          axis=1)
    self._validate_contexts(next_states)
    return next_states, next_states