def _combine_unused_states(self, net):
    """Concatenate the unused hidden states of the cell."""
    used_hiddenstates = self._used_hiddenstates

    final_height = int(net[-1].shape[2])
    final_num_filters = get_channel_dim(net[-1].shape)
    assert len(used_hiddenstates) == len(net)
    for idx, used_h in enumerate(used_hiddenstates):
      curr_height = int(net[idx].shape[2])
      curr_num_filters = get_channel_dim(net[idx].shape)

      # Determine if a reduction should be applied to make the number of
      # filters match.
      should_reduce = final_num_filters != curr_num_filters
      should_reduce = (final_height != curr_height) or should_reduce
      should_reduce = should_reduce and not used_h
      if should_reduce:
        stride = 2 if final_height != curr_height else 1
        with tf.variable_scope('reduction_{}'.format(idx)):
          net[idx] = factorized_reduction(
              net[idx], final_num_filters, stride)

    states_to_combine = (
        [h for h, is_used in zip(net, used_hiddenstates) if not is_used])

    # Return the concat of all the states
    concat_axis = get_channel_index()
    net = tf.concat(values=states_to_combine, axis=concat_axis)
    return net