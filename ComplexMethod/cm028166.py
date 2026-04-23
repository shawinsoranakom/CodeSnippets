def add(self, episodes, priorities, new_idxs=None):
    """Add episodes to buffer."""
    if new_idxs is None:
      idx = 0
      new_idxs = []
      while self.cur_size < self.max_size and idx < len(episodes):
        self.buffer[self.cur_size] = episodes[idx]
        new_idxs.append(self.cur_size)
        self.cur_size += 1
        idx += 1

      if idx < len(episodes):
        remove_idxs = self.remove_n(len(episodes) - idx)
        for remove_idx in remove_idxs:
          self.buffer[remove_idx] = episodes[idx]
          new_idxs.append(remove_idx)
          idx += 1
    else:
      assert len(new_idxs) == len(episodes)
      for new_idx, ep in zip(new_idxs, episodes):
        self.buffer[new_idx] = ep

    self.priorities[new_idxs] = priorities
    self.priorities[0:self.init_length] = np.max(
        self.priorities[self.init_length:])

    assert len(self.buffer) == self.cur_size
    return new_idxs