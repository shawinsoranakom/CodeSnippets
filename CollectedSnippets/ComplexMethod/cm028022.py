def episode(self):
    """Episode data.

    Returns:
      observations: a tuple with one element. This element is a numpy array of
        size in_seq_len x observation_size x observation_size x 3 containing
        in_seq_len images.
      query: a numpy array of size
        in_seq_len x observation_size X observation_size x 3 containing a query
        image.
      A tuple of size two. First element is a in_seq_len x 2 numpy array of
        either 1.0 or 0.0. The i-th element denotes whether the i-th query
        image is neraby (value 1.0) or not (value 0.0) to the i-th observation.
        The second element in the tuple is a mask, a numpy array of size
        in_seq_len x 1 and values 1.0 or 0.0 denoting whether the query is
        valid or not (it can happen that the query is not valid, e.g. there are
        not enough observations to have a meaningful queries).
    """
    observations, states, path = self._exploration()
    assert len(observations.values()[0]) == len(states)

    # The observations are taken along a smoothed trajectory following the path.
    # We compute a mapping between the obeservations and the map vertices.
    path_to_obs, obs_to_path = self._obs_to_state(path, states)

    # Go over all observations, and sample a query. With probability 0.5 this
    # query is a nearby observation (defined as belonging to the same vertex
    # in path).
    g = self._env.graph
    queries = []
    labels = []
    validity_masks = []
    query_index_in_observations = []
    for i, curr_o in enumerate(observations.values()[0]):
      p = obs_to_path[i]
      low = max(0, i - self._max_distance)

      # A list of lists of vertex indices. Each list in this group corresponds
      # to one possible label.
      index_groups = [[], [], []]
      # Nearby visited indices, label 1.
      nearby_visited = [
          ii for ii in path[low:i + 1] + g[p].keys() if ii in obs_to_path[:i]
      ]
      nearby_visited = [ii for ii in index_groups[1] if ii in path_to_obs]
      # NOT Nearby visited indices, label 0.
      not_nearby_visited = [ii for ii in path[:low] if ii not in g[p].keys()]
      not_nearby_visited = [ii for ii in index_groups[0] if ii in path_to_obs]
      # NOT visited indices, label 2.
      not_visited = [
          ii for ii in range(g.number_of_nodes()) if ii not in path[:i + 1]
      ]

      index_groups = [not_nearby_visited, nearby_visited, not_visited]

      # Consider only labels for which there are indices.
      allowed_labels = [ii for ii, group in enumerate(index_groups) if group]
      label = self._rng.choice(allowed_labels)

      indices = list(set(index_groups[label]))
      max_obs_index = None if label == 2 else i
      use_exploration_obs = False if label == 2 else True
      o, obs_index, _ = self._sample_obs(
          indices=indices,
          observations=observations.values()[0],
          observation_states=states,
          path_to_obs=path_to_obs,
          max_obs_index=max_obs_index,
          use_exploration_obs=use_exploration_obs)
      query_index_in_observations.append(obs_index)

      # If we cannot sample a valid query, we mark it as not valid in mask.
      if o is None:
        label = 0.0
        o = curr_o
        validity_masks.append(0)
      else:
        validity_masks.append(1)

      queries.append(o.values()[0])
      labels.append(label)

    query = np.concatenate([np.expand_dims(q, axis=0) for q in queries], axis=0)

    def one_hot(label, num_labels=3):
      a = np.zeros((num_labels,), dtype=np.float)
      a[int(label)] = 1.0
      return a

    outputs = np.stack([one_hot(l) for l in labels], axis=0)
    validity_mask = np.reshape(
        np.array(validity_masks, dtype=np.int32), [-1, 1])

    self.info['query_index_in_observations'] = query_index_in_observations
    self.info['observation_states'] = states

    return observations, query, (outputs, validity_mask)