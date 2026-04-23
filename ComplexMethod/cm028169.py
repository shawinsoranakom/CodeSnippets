def get_from_replay_buffer(self, batch_size):
    """Sample a batch of episodes from the replay buffer."""
    if self.replay_buffer is None or len(self.replay_buffer) < 1 * batch_size:
      return None, None

    desired_count = batch_size * self.max_step
    # in the case of batch_by_steps, we sample larger and larger
    # amounts from the replay buffer until we have enough steps.
    while True:
      if batch_size > len(self.replay_buffer):
        batch_size = len(self.replay_buffer)
      episodes, probs = self.replay_buffer.get_batch(batch_size)
      count = sum(len(ep[-2]) for ep in episodes)
      if count >= desired_count or not self.batch_by_steps:
        break
      if batch_size == len(self.replay_buffer):
        return None, None
      batch_size *= 1.2

    return (self.convert_to_batched_episodes(episodes), probs)