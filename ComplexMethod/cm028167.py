def _sample_episodes(self, sess, greedy=False):
    """Sample episodes from environment using model."""
    # reset environments as necessary
    obs_after_reset = self.env.reset_if(self.start_episode)

    for i, obs in enumerate(obs_after_reset):
      if obs is not None:
        self.step_count[i] = 0
        self.internal_state[i] = self.initial_internal_state()
        for j in xrange(len(self.env_spec.obs_dims)):
          self.last_obs[j][i] = obs[j]
        for j in xrange(len(self.env_spec.act_dims)):
          self.last_act[j][i] = -1
        self.last_pad[i] = 0

    # maintain episode as a single unit if the last sampling
    # batch ended before the episode was terminated
    if self.unify_episodes:
      assert len(obs_after_reset) == 1
      new_ep = obs_after_reset[0] is not None
    else:
      new_ep = True

    self.start_id = 0 if new_ep else len(self.all_obs[:])

    initial_state = self.internal_state
    all_obs = [] if new_ep else self.all_obs[:]
    all_act = ([self.last_act] if new_ep else self.all_act[:])
    all_pad = [] if new_ep else self.all_pad[:]
    rewards = [] if new_ep else self.rewards[:]

    # start stepping in the environments
    step = 0
    while not self.env.all_done():
      self.step_count += 1 - np.array(self.env.dones)

      next_internal_state, sampled_actions = self.model.sample_step(
          sess, self.last_obs, self.internal_state, self.last_act,
          greedy=greedy)

      env_actions = self.env_spec.convert_actions_to_env(sampled_actions)
      next_obs, reward, next_dones, _ = self.env.step(env_actions)

      all_obs.append(self.last_obs)
      all_act.append(sampled_actions)
      all_pad.append(self.last_pad)
      rewards.append(reward)

      self.internal_state = next_internal_state
      self.last_obs = next_obs
      self.last_act = sampled_actions
      self.last_pad = np.array(next_dones).astype('float32')

      step += 1
      if self.max_step and step >= self.max_step:
        break

    self.all_obs = all_obs[:]
    self.all_act = all_act[:]
    self.all_pad = all_pad[:]
    self.rewards = rewards[:]

    # append final observation
    all_obs.append(self.last_obs)

    return initial_state, all_obs, all_act, rewards, all_pad