def core(self, obs, prev_internal_state, prev_actions):
    """Core neural network taking in inputs and outputting sampling
    distribution parameters."""
    batch_size = tf.shape(obs[0])[0]
    if not self.recurrent:
      prev_internal_state = tf.zeros([batch_size, self.rnn_state_dim])

    cell = self.get_cell()

    b = tf.get_variable('input_bias', [self.cell_input_dim],
                        initializer=self.vector_init)
    cell_input = tf.nn.bias_add(tf.zeros([batch_size, self.cell_input_dim]), b)

    for i, (obs_dim, obs_type) in enumerate(self.env_spec.obs_dims_and_types):
      w = tf.get_variable('w_state%d' % i, [obs_dim, self.cell_input_dim],
                          initializer=self.matrix_init)
      if self.env_spec.is_discrete(obs_type):
        cell_input += tf.matmul(tf.one_hot(obs[i], obs_dim), w)
      elif self.env_spec.is_box(obs_type):
        cell_input += tf.matmul(obs[i], w)
      else:
        assert False

    if self.input_prev_actions:
      if self.env_spec.combine_actions:  # TODO(ofir): clean this up
        prev_action = prev_actions[0]
        for i, action_dim in enumerate(self.env_spec.orig_act_dims):
          act = tf.mod(prev_action, action_dim)
          w = tf.get_variable('w_prev_action%d' % i, [action_dim, self.cell_input_dim],
                              initializer=self.matrix_init)
          cell_input += tf.matmul(tf.one_hot(act, action_dim), w)
          prev_action = tf.to_int32(prev_action / action_dim)
      else:
        for i, (act_dim, act_type) in enumerate(self.env_spec.act_dims_and_types):
          w = tf.get_variable('w_prev_action%d' % i, [act_dim, self.cell_input_dim],
                              initializer=self.matrix_init)
          if self.env_spec.is_discrete(act_type):
            cell_input += tf.matmul(tf.one_hot(prev_actions[i], act_dim), w)
          elif self.env_spec.is_box(act_type):
            cell_input += tf.matmul(prev_actions[i], w)
          else:
            assert False

    output, next_state = cell(cell_input, prev_internal_state)

    return output, next_state