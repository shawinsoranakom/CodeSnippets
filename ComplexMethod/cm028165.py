def convert_actions_to_env(self, actions):
    if self.combine_actions:
      new_actions = []
      actions = actions[0]
      for dim in self.orig_act_dims:
        new_actions.append(np.mod(actions, dim))
        actions = (actions / dim).astype('int32')
      actions = new_actions

    if self.discretize_actions:
      new_actions = []
      idx = 0
      for i, (dim, typ) in enumerate(zip(self._act_dims, self._act_types)):
        if typ == spaces.discrete:
          new_actions.append(actions[idx])
          idx += 1
        elif typ == spaces.box:
          low, high = self.act_info[i]
          cur_action = []
          for j in xrange(dim):
            cur_action.append(
                low[j] + (high[j] - low[j]) * actions[idx] /
                float(self.discretize_actions))
            idx += 1
          new_actions.append(np.hstack(cur_action))
      actions = new_actions

    return actions