def _qrnn_pooling(self, multipler, constant):
    """Pooling step computes the internal states for all timesteps."""
    assert multipler.get_shape().as_list() == constant.get_shape().as_list()

    gate_static_shape = multipler.get_shape().as_list()
    gate_shape = tf.shape(multipler)

    feature_size = gate_static_shape[2]
    assert feature_size is not None
    batch_size = gate_static_shape[0] or gate_shape[0]
    max_timestep = gate_static_shape[1] or gate_shape[1]

    dynamic_loop = gate_static_shape[1] is None

    # Get multiplier/constant in [timestep, batch, feature_size] format
    multiplier_transposed = tf.transpose(multipler, [1, 0, 2])
    constant_transposed = tf.transpose(constant, [1, 0, 2])

    # Start state
    state = tf.zeros((batch_size, feature_size), tf.float32)
    if dynamic_loop:

      # One pooling step
      def _step(index, state, states):
        m = multiplier_transposed[index, :, :]
        c = constant_transposed[index, :, :]
        new_state = state * m + c
        next_index = index + 1 if self.forward else index - 1
        return next_index, new_state, states.write(index, new_state)

      # Termination condition
      def _termination(index, state, states):
        del state, states
        return (index < max_timestep) if self.forward else (index >= 0)

      states = tf.TensorArray(tf.float32, size=max_timestep)
      index = 0 if self.forward else max_timestep - 1

      # Dynamic pooling loop
      _, state, states = tf.while_loop(_termination, _step,
                                       [index, state, states])
      states = states.stack()
    else:
      # Unstack them to process one timestep at a time
      multiplier_list = tf.unstack(multiplier_transposed)
      constant_list = tf.unstack(constant_transposed)
      states = []

      # Unroll either forward or backward based on the flag `forward`
      timesteps = list(range(max_timestep)) if self.forward else reversed(
          list(range(max_timestep)))

      # Static pooling loop
      for time in timesteps:
        state = state * multiplier_list[time] + constant_list[time]
        states.append(state)

      # Stack them back in the right order
      states = tf.stack(states if self.forward else list(reversed(states)))

    # Change to [batch, timestep, feature_size]
    return tf.transpose(states, [1, 0, 2])