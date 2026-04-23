def get_range_sensor_obs(self):
    """Returns egocentric range sensor observations of maze."""
    robot_x, robot_y, robot_z = self.wrapped_env.get_body_com("torso")[:3]
    ori = self.get_ori()

    structure = self.MAZE_STRUCTURE
    size_scaling = self.MAZE_SIZE_SCALING
    height = self.MAZE_HEIGHT

    segments = []
    # Get line segments (corresponding to outer boundary) of each immovable
    # block or drop-off.
    for i in range(len(structure)):
      for j in range(len(structure[0])):
        if structure[i][j] in [1, -1]:  # There's a wall or drop-off.
          cx = j * size_scaling - self._init_torso_x
          cy = i * size_scaling - self._init_torso_y
          x1 = cx - 0.5 * size_scaling
          x2 = cx + 0.5 * size_scaling
          y1 = cy - 0.5 * size_scaling
          y2 = cy + 0.5 * size_scaling
          struct_segments = [
              ((x1, y1), (x2, y1)),
              ((x2, y1), (x2, y2)),
              ((x2, y2), (x1, y2)),
              ((x1, y2), (x1, y1)),
          ]
          for seg in struct_segments:
            segments.append(dict(
                segment=seg,
                type=structure[i][j],
            ))
    # Get line segments (corresponding to outer boundary) of each movable
    # block within the agent's z-view.
    for block_name, block_type in self.movable_blocks:
      block_x, block_y, block_z = self.wrapped_env.get_body_com(block_name)[:3]
      if (block_z + height * size_scaling / 2 >= robot_z and
          robot_z >= block_z - height * size_scaling / 2):  # Block in view.
        x1 = block_x - 0.5 * size_scaling
        x2 = block_x + 0.5 * size_scaling
        y1 = block_y - 0.5 * size_scaling
        y2 = block_y + 0.5 * size_scaling
        struct_segments = [
            ((x1, y1), (x2, y1)),
            ((x2, y1), (x2, y2)),
            ((x2, y2), (x1, y2)),
            ((x1, y2), (x1, y1)),
        ]
        for seg in struct_segments:
          segments.append(dict(
              segment=seg,
              type=block_type,
          ))

    sensor_readings = np.zeros((self._n_bins, 3))  # 3 for wall, drop-off, block
    for ray_idx in range(self._n_bins):
      ray_ori = (ori - self._sensor_span * 0.5 +
                 (2 * ray_idx + 1.0) / (2 * self._n_bins) * self._sensor_span)
      ray_segments = []
      # Get all segments that intersect with ray.
      for seg in segments:
        p = maze_env_utils.ray_segment_intersect(
            ray=((robot_x, robot_y), ray_ori),
            segment=seg["segment"])
        if p is not None:
          ray_segments.append(dict(
              segment=seg["segment"],
              type=seg["type"],
              ray_ori=ray_ori,
              distance=maze_env_utils.point_distance(p, (robot_x, robot_y)),
          ))
      if len(ray_segments) > 0:
        # Find out which segment is intersected first.
        first_seg = sorted(ray_segments, key=lambda x: x["distance"])[0]
        seg_type = first_seg["type"]
        idx = (0 if seg_type == 1 else  # Wall.
               1 if seg_type == -1 else  # Drop-off.
               2 if maze_env_utils.can_move(seg_type) else  # Block.
               None)
        if first_seg["distance"] <= self._sensor_range:
          sensor_readings[ray_idx][idx] = (self._sensor_range - first_seg["distance"]) / self._sensor_range

    return sensor_readings