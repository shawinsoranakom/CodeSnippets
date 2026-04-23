def build(
      self,
      observations,
      prev_state,
  ):
    """Builds the model that represents the policy of the agent.

    Args:
      observations: Dictionary of observations from different modalities. Keys
        are the name of the modalities. Observation should have the following
        key-values.
          observations['goal']: One-hot tensor that indicates the semantic
            category of the goal. The shape should be
            (batch_size x max_sequence_length x goals).
          observations[task_env.ModalityTypes.PREV_ACTION]: has action_size + 1
            elements where the first action_size numbers are the one hot vector
            of the previous action and the last element indicates whether the
            previous action was successful or not. If
            task_env.ModalityTypes.PREV_ACTION is not in the observation, it
            will not be used in the policy.
      prev_state: Previous state of the model. It should be a tuple of (c,h)
        where c and h are the previous cell value and hidden state of the lstm.
        Each element of tuple has shape of (batch_size x lstm_cell_size).
        If it is set to None, then it initializes the state of the lstm with all
        zeros.

    Returns:
      Tuple of (action, state) where action is the action logits and state is
      the state of the model after taking new observation.
    Raises:
      ValueError: If any of the modality names is not in observations or
        embedders_dict.
      ValueError: If 'goal' is not in the observations.
    """

    for modality_name in self._modality_names:
      if modality_name not in observations:
        raise ValueError('modality name does not exist in observations: {} not '
                         'in {}'.format(modality_name, observations.keys()))
      if modality_name not in self._embedders:
        if modality_name == task_env.ModalityTypes.PREV_ACTION:
          continue
        raise ValueError('modality name does not have corresponding embedder'
                         ' {} not in {}'.format(modality_name,
                                                self._embedders.keys()))

    if task_env.ModalityTypes.GOAL not in observations:
      raise ValueError('goal should be provided in the observations')

    goal = observations[task_env.ModalityTypes.GOAL]
    prev_action = None
    if task_env.ModalityTypes.PREV_ACTION in observations:
      prev_action = observations[task_env.ModalityTypes.PREV_ACTION]

    with tf.variable_scope('policy'):
      with slim.arg_scope(
          [slim.fully_connected],
          activation_fn=tf.nn.relu,
          weights_initializer=tf.truncated_normal_initializer(stddev=0.01),
          weights_regularizer=slim.l2_regularizer(self._weight_decay)):
        all_inputs = []

        # Concatenating the embedding of each modality by applying the embedders
        # to corresponding observations.
        def embed(name):
          with tf.variable_scope('embed_{}'.format(name)):
            # logging.info('Policy uses embedding %s', name)
            return self._embedders[name].build(observations[name])

        all_inputs = map(embed, [
            x for x in self._modality_names
            if x != task_env.ModalityTypes.PREV_ACTION
        ])

        # Computing goal embedding.
        shape = goal.get_shape().as_list()
        with tf.variable_scope('embed_goal'):
          encoded_goal = tf.reshape(goal, [shape[0] * shape[1], -1])
          encoded_goal = slim.fully_connected(encoded_goal,
                                              self._target_embedding_size)
          encoded_goal = tf.reshape(encoded_goal, [shape[0], shape[1], -1])
          all_inputs.append(encoded_goal)

        # Concatenating all the modalities and goal.
        all_inputs = tf.concat(all_inputs, axis=-1, name='concat_embeddings')

        shape = all_inputs.get_shape().as_list()
        all_inputs = tf.reshape(all_inputs, [shape[0] * shape[1], shape[2]])

        # Applying fully connected layers.
        encoded_inputs = slim.fully_connected(all_inputs, self._fc_channels)
        encoded_inputs = slim.fully_connected(encoded_inputs, self._fc_channels)

        if not self._feedforward_mode:
          encoded_inputs = tf.reshape(encoded_inputs,
                                      [shape[0], shape[1], self._fc_channels])
          lstm_outputs, lstm_state = self._build_lstm(
              encoded_inputs=encoded_inputs,
              prev_state=prev_state,
              episode_length=tf.ones((shape[0],), dtype=tf.float32) *
              self._max_episode_length,
              prev_action=prev_action,
          )
        else:
          # If feedforward_mode=True, directly compute bypass the whole LSTM
          # computations.
          lstm_outputs = encoded_inputs

        lstm_outputs = slim.fully_connected(lstm_outputs, self._fc_channels)
        action_values = slim.fully_connected(
            lstm_outputs, self._action_size, activation_fn=None)
        action_values = tf.reshape(action_values, [shape[0], shape[1], -1])
        if not self._feedforward_mode:
          return action_values, lstm_state
        else:
          return action_values, None