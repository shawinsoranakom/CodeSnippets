def init_state(self, state_name, batch_size, dtype, learned_state=False):
    """Creates an initial state compatible with this cell.

    Args:
      state_name: name of the state tensor
      batch_size: model batch size
      dtype: dtype for the tensor values i.e. tf.float32
      learned_state: whether the initial state should be learnable. If false,
        the initial state is set to all 0's

    Returns:
      ret: the created initial state
    """
    state_size = (
        self.state_size_flat if self._flatten_state else self.state_size)
    # list of 2 zero tensors or variables tensors,
    # depending on if learned_state is true
    # pylint: disable=g-long-ternary,g-complex-comprehension
    ret_flat = [(contrib_variables.model_variable(
        state_name + str(i),
        shape=s,
        dtype=dtype,
        initializer=tf.truncated_normal_initializer(stddev=0.03))
                 if learned_state else tf.zeros(
                     [batch_size] + s, dtype=dtype, name=state_name))
                for i, s in enumerate(state_size)]

    # duplicates initial state across the batch axis if it's learned
    if learned_state:
      ret_flat = [tf.stack([tensor for i in range(int(batch_size))])
                  for tensor in ret_flat]
    for s, r in zip(state_size, ret_flat):
      r = tf.reshape(r, [-1] + s)
    ret = tf.nest.pack_sequence_as(structure=[1, 1], flat_sequence=ret_flat)
    return ret