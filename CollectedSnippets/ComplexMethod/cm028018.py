def build(self, feeds, state):
    history, goal, _ = self._embed_task_ios(feeds)
    _print_debug_ios(history, goal, None)

    params = self._lstm_hparams
    cell = lambda: tf.contrib.rnn.BasicLSTMCell(params.cell_size)
    stacked_lstm = tf.contrib.rnn.MultiRNNCell(
        [cell() for _ in range(params.num_layers)])
    # history is of shape batch_size x seq_len x embedding_dimension
    batch_size, seq_len, _ = tuple(history.get_shape().as_list())

    if state is None:
      state = stacked_lstm.zero_state(batch_size, tf.float32)
    for t in range(seq_len):
      if params.concat_goal_everywhere:
        lstm_input = tf.concat([tf.squeeze(history[:, t, :]), goal], axis=1)
      else:
        lstm_input = tf.squeeze(history[:, t, :])
      output, state = stacked_lstm(lstm_input, state)

    with tf.variable_scope('output_decoder'):
      oconfig = self._task_config.output.shape
      assert len(oconfig) == 1
      features = tf.concat([output, goal], axis=1)
      assert len(output.get_shape().as_list()) == 2
      assert len(goal.get_shape().as_list()) == 2
      decoder = embedders.MLPEmbedder(
          layers=self._embedder_hparams.predictions.layer_sizes + oconfig)
      # Prediction is done off the last step lstm output and the goal.
      predictions = decoder.build(features)

    return predictions, state