def _create_initial_state(
      self, initial_ids, initial_cache, batch_size, constraint_mask=None
  ):
    """Return initial state dictionary and its shape invariants."""
    for key, value in initial_cache.items():
      for inner_value in tf.nest.flatten(value):
        if inner_value.dtype != self.dtype:
          raise TypeError(
              "initial_cache element for key '%s' has dtype %s that does not "
              "match SequenceBeamSearch's dtype of %s. Value: %s" %
              (key, inner_value.dtype.name, self.dtype.name, inner_value))

    # Current loop index (starts at 0)
    cur_index = tf.constant(0)

    # Create alive sequence with shape [batch_size, beam_size, 1]
    alive_seq = expand_to_beam_size(initial_ids, self.beam_size)
    alive_seq = tf.expand_dims(alive_seq, axis=2)
    if self.padded_decode:
      alive_seq = tf.tile(alive_seq, [1, 1, self.max_decode_length + 1])

    # Create tensor for storing initial log probabilities.
    # Assume initial_ids are prob 1.0
    initial_log_probs = tf.constant([[0.] + [-float("inf")] *
                                     (self.beam_size - 1)],
                                    dtype=self.dtype)
    alive_log_probs = tf.tile(initial_log_probs, [batch_size, 1])

    # Expand all values stored in the dictionary to the beam size, so that each
    # beam has a separate cache.
    alive_cache = tf.nest.map_structure(
        lambda t: expand_to_beam_size(t, self.beam_size), initial_cache)

    # Initialize tensor storing finished sequences with filler values.
    finished_seq = tf.zeros(tf.shape(alive_seq), tf.int32)

    # Set scores of the initial finished seqs to negative infinity.
    finished_scores = tf.ones([batch_size, self.beam_size],
                              dtype=self.dtype) * -inf(self.dtype)

    # Initialize finished flags with all False values.
    finished_flags = tf.zeros([batch_size, self.beam_size], tf.bool)

    # Create state dictionary
    state = {
        _StateKeys.CUR_INDEX: cur_index,
        _StateKeys.ALIVE_SEQ: alive_seq,
        _StateKeys.ALIVE_LOG_PROBS: alive_log_probs,
        _StateKeys.ALIVE_CACHE: alive_cache,
        _StateKeys.FINISHED_SEQ: finished_seq,
        _StateKeys.FINISHED_SCORES: finished_scores,
        _StateKeys.FINISHED_FLAGS: finished_flags
    }
    if constraint_mask is not None:
      state[_StateKeys.CONSTRAINT_MASK] = constraint_mask

    # Create state invariants for each value in the state dictionary. Each
    # dimension must be a constant or None. A None dimension means either:
    #   1) the dimension's value is a tensor that remains the same but may
    #      depend on the input sequence to the model (e.g. batch size).
    #   2) the dimension may have different values on different iterations.
    if self.padded_decode:
      state_shape_invariants = {
          _StateKeys.CUR_INDEX:
              tf.TensorShape([]),
          _StateKeys.ALIVE_SEQ:
              tf.TensorShape(
                  [batch_size, self.beam_size, self.max_decode_length + 1]),
          _StateKeys.ALIVE_LOG_PROBS:
              tf.TensorShape([batch_size, self.beam_size]),
          _StateKeys.ALIVE_CACHE:
              tf.nest.map_structure(lambda state: state.get_shape(),
                                    alive_cache),
          _StateKeys.FINISHED_SEQ:
              tf.TensorShape(
                  [batch_size, self.beam_size, self.max_decode_length + 1]),
          _StateKeys.FINISHED_SCORES:
              tf.TensorShape([batch_size, self.beam_size]),
          _StateKeys.FINISHED_FLAGS:
              tf.TensorShape([batch_size, self.beam_size])
      }
    else:
      state_shape_invariants = {
          _StateKeys.CUR_INDEX:
              tf.TensorShape([]),
          _StateKeys.ALIVE_SEQ:
              tf.TensorShape([None, self.beam_size, None]),
          _StateKeys.ALIVE_LOG_PROBS:
              tf.TensorShape([None, self.beam_size]),
          _StateKeys.ALIVE_CACHE:
              tf.nest.map_structure(_get_shape_keep_last_dim, alive_cache),
          _StateKeys.FINISHED_SEQ:
              tf.TensorShape([None, self.beam_size, None]),
          _StateKeys.FINISHED_SCORES:
              tf.TensorShape([None, self.beam_size]),
          _StateKeys.FINISHED_FLAGS:
              tf.TensorShape([None, self.beam_size])
      }
    if constraint_mask is not None:
      state_shape_invariants[_StateKeys.CONSTRAINT_MASK] = tf.TensorShape(
          [self.vocab_size]
      )

    return state, state_shape_invariants