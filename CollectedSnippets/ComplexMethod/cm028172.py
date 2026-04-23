def reset_if(self, predicate=None):
    if predicate is None:
      predicate = self.dones
    if self.count != 1:
      assert np.all(predicate)
      return self.reset()
    self.num_episodes_played += sum(predicate)
    output = [self.env_spec.convert_obs_to_list(env.reset())
              if pred else None
              for env, pred in zip(self.envs, predicate)]
    for i, pred in enumerate(predicate):
      if pred:
        self.dones[i] = False
    return output