def episode(self):
    """Episode data.

    Returns:
      observations: a tuple with one element. This element is a numpy array of
        size in_seq_len x observation_size x observation_size x 3 containing
        in_seq_len images.
      query: a numpy array of size
        2 x observation_size X observation_size x 3 containing a pair of query
        images.
      A tuple of size two. First element is a numpy array of size 2 containing
        a one hot vector of whether the two observations are neighobring. Second
        element is a boolean numpy value denoting whether this is a valid
        episode.
    """
    observations, states, path = self._exploration()
    assert len(observations.values()[0]) == len(states)
    path_to_obs, _ = self._obs_to_state(path, states)
    # Restrict path to ones for which observations have been generated.
    path = [p for p in path if p in path_to_obs]
    # Sample first query.
    query1_index = self._rng.choice(path)
    # Sample label.
    label = self._rng.randint(2)
    # Sample second query.
    # If label == 1, then second query must be nearby, otherwise not.
    closest_indices = nx.single_source_shortest_path(
        self._env.graph, query1_index, self._max_distance).keys()
    if label == 0:
      # Closest indices on the path.
      indices = [p for p in path if p not in closest_indices]
    else:
      # Indices which are not closest on the path.
      indices = [p for p in closest_indices if p in path]

    query2_index = self._rng.choice(indices)
    # Generate an observation.
    query1, query1_index, _ = self._sample_obs(
        [query1_index],
        observations.values()[0],
        states,
        path_to_obs,
        max_obs_index=None,
        use_exploration_obs=True)
    query2, query2_index, _ = self._sample_obs(
        [query2_index],
        observations.values()[0],
        states,
        path_to_obs,
        max_obs_index=None,
        use_exploration_obs=True)

    queries = np.concatenate(
        [np.expand_dims(q, axis=0) for q in [query1, query2]])
    labels = np.array([0, 0])
    labels[label] = 1
    is_valid = np.array([1])

    self.info['observation_states'] = states
    self.info['query_indices_in_observations'] = [query1_index, query2_index]

    return observations, queries, (labels, is_valid)