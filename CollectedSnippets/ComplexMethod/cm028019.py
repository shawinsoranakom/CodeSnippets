def episode_batch(self, batch_size):
    """Returns a batch of episodes.

    Args:
      batch_size: size of batch.

    Returns:
      (inputs, query, output, masks) where inputs is list of numpy arrays and
      query, output, and mask are numpy arrays. These arrays must be of shape
      and type as specified in the task configuration with one additional
      preceding dimension corresponding to the batch.

    Raises:
      ValueError: if self.episode() returns illegal values.
    """
    batched_inputs = collections.OrderedDict(
        [[mtype, []] for mtype in self.config.inputs])
    batched_queries = []
    batched_outputs = []
    batched_masks = []
    for _ in range(int(batch_size)):
      with self._lock:
        # The episode function needs to be thread-safe. Since the current
        # implementation for the envs are not thread safe we need to have lock
        # the operations here.
        inputs, query, outputs = self.episode()
      if not isinstance(outputs, tuple):
        raise ValueError('Outputs return value must be tuple.')
      if len(outputs) != 2:
        raise ValueError('Output tuple must be of size 2.')
      if inputs is not None:
        for modality_type in batched_inputs:
          batched_inputs[modality_type].append(
              np.expand_dims(inputs[modality_type], axis=0))

      if query is not None:
        batched_queries.append(np.expand_dims(query, axis=0))
      batched_outputs.append(np.expand_dims(outputs[0], axis=0))
      if outputs[1] is not None:
        batched_masks.append(np.expand_dims(outputs[1], axis=0))

    batched_inputs = {
        k: np.concatenate(i, axis=0) for k, i in batched_inputs.iteritems()
    }
    if batched_queries:
      batched_queries = np.concatenate(batched_queries, axis=0)
    batched_outputs = np.concatenate(batched_outputs, axis=0)
    if batched_masks:
      batched_masks = np.concatenate(batched_masks, axis=0).astype(np.float32)
    else:
      # When the array is empty, the default np.dtype is float64 which causes
      # py_func to crash in the tests.
      batched_masks = np.array([], dtype=np.float32)
    batched_inputs = [batched_inputs[k] for k in self._config.inputs]
    return batched_inputs, batched_queries, batched_outputs, batched_masks