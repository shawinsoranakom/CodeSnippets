def _create_initial_state(
      self,
      initial_ids: tf.Tensor,
      initial_cache: Dict[str, tf.Tensor],
      batch_size: int,
      initial_log_probs: Optional[tf.Tensor] = None
  ) -> decoding_module.InitialState:
    """Return initial state dictionary and its shape invariants."""
    for key, value in initial_cache.items():
      for inner_value in tf.nest.flatten(value):
        if inner_value.dtype != self.dtype:
          raise TypeError(
              "initial_cache element for key '%s' has dtype %s that does not "
              "match sampling_module's dtype of %s. Value: %s" %
              (key, value.dtype.name, self.dtype.name, inner_value))

    # Current loop index (starts at 0)
    cur_index = tf.constant(0)

    # Alive sequence with shape [batch_size, 1]
    alive_seq = initial_ids
    alive_seq = tf.expand_dims(alive_seq, axis=-1)
    if self.padded_decode:
      alive_seq = tf.tile(alive_seq, [1, self.max_decode_length + 1])

    # Initial log probabilities with shape [batch_size, 1].
    if initial_log_probs is None:
      initial_log_probs = tf.constant([[0.]], dtype=self.dtype)
      alive_log_probs = tf.tile(initial_log_probs, [batch_size, 1])
    else:
      alive_log_probs = initial_log_probs

    alive_cache = initial_cache

    # Initialize tensor storing finished sequences [batch_size, 1, 1].
    finished_seq = tf.zeros(tf.shape(alive_seq), tf.int32)

    # Set scores of the initial finished seqs to negative infinity.
    finished_scores = tf.zeros([batch_size, 1], dtype=self.dtype)

    # Initialize finished flags with all False values.
    finished_flags = tf.zeros([batch_size, 1], tf.bool)

    # Create state dictionary and state shapes.
    state = {
        decoding_module.StateKeys.CUR_INDEX: cur_index,
        decoding_module.StateKeys.ALIVE_SEQ: alive_seq,
        decoding_module.StateKeys.ALIVE_LOG_PROBS: alive_log_probs,
        decoding_module.StateKeys.ALIVE_CACHE: alive_cache,
        decoding_module.StateKeys.FINISHED_SEQ: finished_seq,
        decoding_module.StateKeys.FINISHED_SCORES: finished_scores,
        decoding_module.StateKeys.FINISHED_FLAGS: finished_flags
    }

    if self.padded_decode:
      state_shape_invariants = {
          decoding_module.StateKeys.CUR_INDEX:
              tf.TensorShape([]),
          decoding_module.StateKeys.ALIVE_SEQ:
              tf.TensorShape([batch_size, self.max_decode_length + 1]),
          decoding_module.StateKeys.ALIVE_LOG_PROBS:
              tf.TensorShape([batch_size, 1]),
          decoding_module.StateKeys.ALIVE_CACHE:
              tf.nest.map_structure(lambda state: state.get_shape(),
                                    alive_cache),
          decoding_module.StateKeys.FINISHED_SEQ:
              tf.TensorShape([batch_size, self.max_decode_length + 1]),
          decoding_module.StateKeys.FINISHED_SCORES:
              tf.TensorShape([batch_size, 1]),
          decoding_module.StateKeys.FINISHED_FLAGS:
              tf.TensorShape([batch_size, 1])
      }
    else:
      state_shape_invariants = {
          decoding_module.StateKeys.CUR_INDEX:
              tf.TensorShape([]),
          decoding_module.StateKeys.ALIVE_SEQ:
              tf.TensorShape([None, None]),
          decoding_module.StateKeys.ALIVE_LOG_PROBS:
              tf.TensorShape([None, 1]),
          decoding_module.StateKeys.ALIVE_CACHE:
              tf.nest.map_structure(decoding_module.get_shape_keep_last_dim,
                                    alive_cache),
          decoding_module.StateKeys.FINISHED_SEQ:
              tf.TensorShape([None, None]),
          decoding_module.StateKeys.FINISHED_SCORES:
              tf.TensorShape([None, 1]),
          decoding_module.StateKeys.FINISHED_FLAGS:
              tf.TensorShape([None, 1])
      }

    if self.extra_cache_output:
      state.update(
          {decoding_module.StateKeys.INITIAL_OUTPUT_CACHE: alive_cache})
      if self.padded_decode:
        state_shape_invariants.update({
            decoding_module.StateKeys.INITIAL_OUTPUT_CACHE:
                tf.nest.map_structure(lambda state: state.get_shape(),
                                      alive_cache)
        })
      else:
        state_shape_invariants.update({
            decoding_module.StateKeys.INITIAL_OUTPUT_CACHE:
                tf.nest.map_structure(decoding_module.get_shape_keep_last_dim,
                                      alive_cache),
        })

    return state, state_shape_invariants