def _apply_drop_path(self, net, current_step=None,
                       use_summaries=False, drop_connect_version='v3'):
    """Apply drop_path regularization.

    Args:
      net: the Tensor that gets drop_path regularization applied.
      current_step: a float32 Tensor with the current global_step value,
        to be divided by hparams.total_training_steps. Usually None, which
        defaults to tf.train.get_or_create_global_step() properly casted.
      use_summaries: a Python boolean. If set to False, no summaries are output.
      drop_connect_version: one of 'v1', 'v2', 'v3', controlling whether
        the dropout rate is scaled by current_step (v1), layer (v2), or
        both (v3, the default).

    Returns:
      The dropped-out value of `net`.
    """
    drop_path_keep_prob = self._drop_path_keep_prob
    if drop_path_keep_prob < 1.0:
      assert drop_connect_version in ['v1', 'v2', 'v3']
      if drop_connect_version in ['v2', 'v3']:
        # Scale keep prob by layer number
        assert self._cell_num != -1
        # The added 2 is for the reduction cells
        num_cells = self._total_num_cells
        layer_ratio = (self._cell_num + 1)/float(num_cells)
        if use_summaries:
          with tf.device('/cpu:0'):
            tf.summary.scalar('layer_ratio', layer_ratio)
        drop_path_keep_prob = 1 - layer_ratio * (1 - drop_path_keep_prob)
      if drop_connect_version in ['v1', 'v3']:
        # Decrease the keep probability over time
        if current_step is None:
          current_step = tf.train.get_or_create_global_step()
        current_step = tf.cast(current_step, tf.float32)
        drop_path_burn_in_steps = self._total_training_steps
        current_ratio = current_step / drop_path_burn_in_steps
        current_ratio = tf.minimum(1.0, current_ratio)
        if use_summaries:
          with tf.device('/cpu:0'):
            tf.summary.scalar('current_ratio', current_ratio)
        drop_path_keep_prob = (1 - current_ratio * (1 - drop_path_keep_prob))
      if use_summaries:
        with tf.device('/cpu:0'):
          tf.summary.scalar('drop_path_keep_prob', drop_path_keep_prob)
      net = drop_path(net, drop_path_keep_prob)
    return net