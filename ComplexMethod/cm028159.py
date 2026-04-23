def get_inputs(self, time_step, obs, prev_actions,
                 internal_policy_states):
    """Get inputs to network as single tensor."""
    inputs = [tf.ones_like(time_step)]
    input_dim = 1

    if not self.input_policy_state:
      for i, (obs_dim, obs_type) in enumerate(self.env_spec.obs_dims_and_types):
        if self.env_spec.is_discrete(obs_type):
          inputs.append(
              tf.one_hot(obs[i], obs_dim))
          input_dim += obs_dim
        elif self.env_spec.is_box(obs_type):
          cur_obs = obs[i]
          inputs.append(cur_obs)
          inputs.append(cur_obs ** 2)
          input_dim += obs_dim * 2
        else:
          assert False

      if self.input_prev_actions:
        for i, (act_dim, act_type) in enumerate(self.env_spec.act_dims_and_types):
          if self.env_spec.is_discrete(act_type):
            inputs.append(
                tf.one_hot(prev_actions[i], act_dim))
            input_dim += act_dim
          elif self.env_spec.is_box(act_type):
            inputs.append(prev_actions[i])
            input_dim += act_dim
          else:
            assert False

    if self.input_policy_state:
      inputs.append(internal_policy_states)
      input_dim += self.internal_policy_dim

    if self.input_time_step:
      scaled_time = 0.01 * time_step
      inputs.extend([scaled_time, scaled_time ** 2, scaled_time ** 3])
      input_dim += 3

    return input_dim, tf.concat(inputs, 1)