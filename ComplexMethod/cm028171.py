def setup(self, train=True):
    """Setup Tensorflow Graph."""

    self.setup_placeholders()

    tf.summary.scalar('avg_episode_reward', self.avg_episode_reward)
    tf.summary.scalar('greedy_episode_reward', self.greedy_episode_reward)

    with tf.variable_scope('model', reuse=None):
      # policy network
      with tf.variable_scope('policy_net'):
        (self.policy_internal_states, self.logits, self.log_probs,
         self.entropies, self.self_kls) = \
            self.policy.multi_step(self.observations,
                                   self.internal_state,
                                   self.actions)
        self.out_log_probs = sum(self.log_probs)
        self.kl = self.policy.calculate_kl(self.other_logits, self.logits)
        self.avg_kl = (tf.reduce_sum(sum(self.kl)[:-1] * (1 - self.pads)) /
                       tf.reduce_sum(1 - self.pads))

      # value network
      with tf.variable_scope('value_net'):
        (self.values,
         self.regression_input,
         self.regression_weight) = self.baseline.get_values(
            self.observations, self.actions,
            self.policy_internal_states, self.logits)

      # target policy network
      with tf.variable_scope('target_policy_net'):
        (self.target_policy_internal_states,
         self.target_logits, self.target_log_probs,
         _, _) = \
            self.policy.multi_step(self.observations,
                                   self.internal_state,
                                   self.actions)

      # target value network
      with tf.variable_scope('target_value_net'):
        (self.target_values, _, _) = self.baseline.get_values(
            self.observations, self.actions,
            self.target_policy_internal_states, self.target_logits)

      # construct copy op online --> target
      all_vars = tf.trainable_variables()
      online_vars = [p for p in all_vars if
                     '/policy_net' in p.name or '/value_net' in p.name]
      target_vars = [p for p in all_vars if
                     'target_policy_net' in p.name or 'target_value_net' in p.name]
      online_vars.sort(key=lambda p: p.name)
      target_vars.sort(key=lambda p: p.name)
      aa = self.target_network_lag
      self.copy_op = tf.group(*[
          target_p.assign(aa * target_p + (1 - aa) * online_p)
          for online_p, target_p in zip(online_vars, target_vars)])

      if train:
        # evaluate objective
        (self.loss, self.raw_loss, self.regression_target,
         self.gradient_ops, self.summary) = self.objective.get(
            self.rewards, self.pads,
            self.values[:-1, :],
            self.values[-1, :] * (1 - self.terminated),
            self.log_probs, self.prev_log_probs, self.target_log_probs,
            self.entropies, self.logits, self.target_values[:-1, :],
            self.target_values[-1, :] * (1 - self.terminated))

        self.regression_target = tf.reshape(self.regression_target, [-1])

        self.policy_vars = [
            v for v in tf.trainable_variables()
            if '/policy_net' in v.name]
        self.value_vars = [
            v for v in tf.trainable_variables()
            if '/value_net' in v.name]

        # trust region optimizer
        if self.trust_region_policy_opt is not None:
          with tf.variable_scope('trust_region_policy', reuse=None):
            avg_self_kl = (
                tf.reduce_sum(sum(self.self_kls) * (1 - self.pads)) /
                tf.reduce_sum(1 - self.pads))

            self.trust_region_policy_opt.setup(
                self.policy_vars, self.raw_loss, avg_self_kl,
                self.avg_kl)

        # value optimizer
        if self.value_opt is not None:
          with tf.variable_scope('trust_region_value', reuse=None):
            self.value_opt.setup(
                self.value_vars,
                tf.reshape(self.values[:-1, :], [-1]),
                self.regression_target,
                tf.reshape(self.pads, [-1]),
                self.regression_input, self.regression_weight)

    # we re-use variables for the sampling operations
    with tf.variable_scope('model', reuse=True):
      scope = ('target_policy_net' if self.sample_from == 'target'
               else 'policy_net')
      with tf.variable_scope(scope):
        self.next_internal_state, self.sampled_actions = \
            self.policy.sample_step(self.single_observation,
                                    self.internal_state,
                                    self.single_action)
        self.greedy_next_internal_state, self.greedy_sampled_actions = \
            self.policy.sample_step(self.single_observation,
                                    self.internal_state,
                                    self.single_action,
                                    greedy=True)