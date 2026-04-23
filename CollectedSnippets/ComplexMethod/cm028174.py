def multi_step(self, all_obs, initial_state, all_actions):
    """Calculate log-probs and other calculations on batch of episodes."""
    batch_size = tf.shape(initial_state)[0]
    time_length = tf.shape(all_obs[0])[0]

    # first reshape inputs as a single batch
    reshaped_obs = []
    for obs, (obs_dim, obs_type) in zip(all_obs, self.env_spec.obs_dims_and_types):
      if self.env_spec.is_discrete(obs_type):
        reshaped_obs.append(tf.reshape(obs, [time_length * batch_size]))
      elif self.env_spec.is_box(obs_type):
        reshaped_obs.append(tf.reshape(obs, [time_length * batch_size, obs_dim]))

    reshaped_act = []
    reshaped_prev_act = []
    for i, (act_dim, act_type) in enumerate(self.env_spec.act_dims_and_types):
      act = tf.concat([all_actions[i][1:], all_actions[i][0:1]], 0)
      prev_act = all_actions[i]
      if self.env_spec.is_discrete(act_type):
        reshaped_act.append(tf.reshape(act, [time_length * batch_size]))
        reshaped_prev_act.append(
            tf.reshape(prev_act, [time_length * batch_size]))
      elif self.env_spec.is_box(act_type):
        reshaped_act.append(
            tf.reshape(act, [time_length * batch_size, act_dim]))
        reshaped_prev_act.append(
            tf.reshape(prev_act, [time_length * batch_size, act_dim]))

    # now inputs go into single step as one large batch
    (internal_states, _, logits, log_probs,
     entropies, self_kls) = self.single_step(
         reshaped_obs, reshaped_act, reshaped_prev_act)

    # reshape the outputs back to original time-major format
    internal_states = tf.reshape(internal_states, [time_length, batch_size, -1])
    logits = [tf.reshape(logit, [time_length, batch_size, -1])
              for logit in logits]
    log_probs = [tf.reshape(log_prob, [time_length, batch_size])[:-1]
                 for log_prob in log_probs]
    entropies = [tf.reshape(ent, [time_length, batch_size])[:-1]
                 for ent in entropies]
    self_kls = [tf.reshape(self_kl, [time_length, batch_size])[:-1]
                for self_kl in self_kls]

    return internal_states, logits, log_probs, entropies, self_kls