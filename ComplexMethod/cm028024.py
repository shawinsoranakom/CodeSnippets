def episode(self):
    # Get a location. If not set, sample on at a vertex with a random
    # orientation
    location = self._location
    if location is None:
      num_nodes = self._env.graph.number_of_nodes()
      vertex = int(math.floor(self._rng.uniform(0, num_nodes)))
      xy = self._env.vertex_to_pose(vertex)
      theta = self._rng.uniform(0, 2 * math.pi)
      location = np.concatenate(
          [np.reshape(xy, [-1]), np.array([theta])], axis=0)
    else:
      vertex = self._env.pose_to_vertex(location)

    theta = location[2]
    neighbors = self._env.graph.neighbors(vertex)
    xy_s = [self._env.vertex_to_pose(n) for n in neighbors]

    def rotate(xy, theta):
      """Rotates a vector around the origin by angle theta.

      Args:
        xy: a numpy darray of shape (2, ) of floats containing the x and y
          coordinates of a vector.
        theta: a python float containing the rotation angle in radians.

      Returns:
        A numpy darray of floats of shape (2,) containing the x and y
          coordinates rotated xy.
      """
      rotated_x = np.cos(theta) * xy[0] - np.sin(theta) * xy[1]
      rotated_y = np.sin(theta) * xy[0] + np.cos(theta) * xy[1]
      return np.array([rotated_x, rotated_y])

    # Rotate all intersection biforcation by the orientation of the agent as the
    # intersection label is defined in an agent centered fashion.
    xy_s = [
        rotate(xy - location[0:2], -location[2] - math.pi / 4) for xy in xy_s
    ]
    th_s = [np.arctan2(xy[1], xy[0]) for xy in xy_s]

    out_shape = self._config.output.shape
    if len(out_shape) != 1:
      raise ValueError('Output shape should be of rank 1.')
    num_labels = out_shape[0]
    if num_labels != 16:
      raise ValueError('Currently only 16 labels are supported '
                       '(there are 16 different 4 way intersection types).')

    th_s = set([int(math.floor(4 * (th / (2 * np.pi) + 0.5))) for th in th_s])
    one_hot_label = np.zeros((num_labels,), dtype=np.float32)
    label = 0
    for th in th_s:
      label += pow(2, th)
    one_hot_label[int(label)] = 1.0

    query = self._env.observation(location).values()[0]
    return [], query, (one_hot_label, None)