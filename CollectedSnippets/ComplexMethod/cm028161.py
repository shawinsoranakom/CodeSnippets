def get_objective(self):
    tau = self.tau
    if self.tau_decay is not None:
      assert self.tau_start >= self.tau
      tau = tf.maximum(
          tf.train.exponential_decay(
              self.tau_start, self.global_step, 100, self.tau_decay),
          self.tau)

    if self.objective in ['pcl', 'a3c', 'trpo', 'upcl']:
      cls = (objective.PCL if self.objective in ['pcl', 'upcl'] else
             objective.TRPO if self.objective == 'trpo' else
             objective.ActorCritic)
      policy_weight = 1.0

      return cls(self.learning_rate,
                 clip_norm=self.clip_norm,
                 policy_weight=policy_weight,
                 critic_weight=self.critic_weight,
                 tau=tau, gamma=self.gamma, rollout=self.rollout,
                 eps_lambda=self.eps_lambda, clip_adv=self.clip_adv,
                 use_target_values=self.use_target_values)
    elif self.objective in ['reinforce', 'urex']:
      cls = (full_episode_objective.Reinforce
             if self.objective == 'reinforce' else
             full_episode_objective.UREX)
      return cls(self.learning_rate,
                 clip_norm=self.clip_norm,
                 num_samples=self.num_samples,
                 tau=tau, bonus_weight=1.0)  # TODO: bonus weight?
    else:
      assert False, 'Unknown objective %s' % self.objective