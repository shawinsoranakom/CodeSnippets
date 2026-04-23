def convert_to_batched_episodes(self, episodes, max_length=None):
    """Convert batch-major list of episodes to time-major batch of episodes."""
    lengths = [len(ep[-2]) for ep in episodes]
    max_length = max_length or max(lengths)

    new_episodes = []
    for ep, length in zip(episodes, lengths):
      initial, observations, actions, rewards, terminated = ep
      observations = [np.resize(obs, [max_length + 1] + list(obs.shape)[1:])
                      for obs in observations]
      actions = [np.resize(act, [max_length + 1] + list(act.shape)[1:])
                 for act in actions]
      pads = np.array([0] * length + [1] * (max_length - length))
      rewards = np.resize(rewards, [max_length]) * (1 - pads)
      new_episodes.append([initial, observations, actions, rewards,
                           terminated, pads])

    (initial, observations, actions, rewards,
     terminated, pads) = zip(*new_episodes)
    observations = [np.swapaxes(obs, 0, 1)
                    for obs in zip(*observations)]
    actions = [np.swapaxes(act, 0, 1)
               for act in zip(*actions)]
    rewards = np.transpose(rewards)
    pads = np.transpose(pads)

    return (initial, observations, actions, rewards, terminated, pads)