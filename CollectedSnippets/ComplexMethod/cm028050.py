def reset(self, mode, agent=None, action_fn=None, state=None):
    """Returns ops that reset the context.

    Args:
      mode: a string representing the mode=[train, explore, eval].
    Returns:
      a list of ops that reset the context.
    """
    if agent is None:
      values = self.sample_contexts(mode=mode, batch_size=1)[0]
      if values is None:
        return []
      values = [value[0] for value in values]
      values[0] = uvf_utils.tf_print(
          values[0],
          values,
          message='context:reset, mode=%s' % mode,
          first_n=10,
          name='context:reset:%s' % mode)
      all_ops = []
      for _, context_vars in sorted(self.context_vars.items()):
        ops = [tf.assign(var, value) for var, value in zip(context_vars, values)]
      all_ops += ops
      all_ops.append(self.set_env_context_op(values))
      all_ops.append(tf.assign(self.t, 0))  # reset timer
      return all_ops
    else:
      ops = agent.tf_context.reset(mode)
      # NOTE: The code is currently written in such a way that the higher level
      # policy does not provide a low-level context until the second
      # observation.  Insead, we just zero-out low-level contexts.
      for key, context_vars in sorted(self.context_vars.items()):
        ops += [tf.assign(var, tf.zeros_like(var)) for var, meta_var in
                zip(context_vars, agent.tf_context.context_vars[key])]

      ops.append(tf.assign(self.t, 0))  # reset timer
      return ops