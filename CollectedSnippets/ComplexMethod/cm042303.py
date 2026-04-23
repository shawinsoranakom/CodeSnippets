def _update_model(self, lead, path_x_array):
    """Update model visualization data based on model message"""
    max_distance = np.clip(path_x_array[-1], MIN_DRAW_DISTANCE, MAX_DRAW_DISTANCE)
    max_idx = self._get_path_length_idx(self._lane_lines[0].raw_points[:, 0], max_distance)

    # Update lane lines using raw points
    line_width_factor = 0.12
    for i, lane_line in enumerate(self._lane_lines):
      if i in (1, 2):
        line_width_factor = 0.16
      lane_line.projected_points = self._map_line_to_polygon(
        lane_line.raw_points, line_width_factor * self._lane_line_probs[i], 0.0, max_idx
      )

    # Update road edges using raw points
    for road_edge in self._road_edges:
      road_edge.projected_points = self._map_line_to_polygon(road_edge.raw_points, line_width_factor, 0.0, max_idx)

    # Update path using raw points
    if lead and lead.status:
      lead_d = lead.dRel * 2.0
      max_distance = np.clip(lead_d - min(lead_d * 0.35, 10.0), 0.0, max_distance)

    soon_acceleration = self._acceleration_x[len(self._acceleration_x) // 4] if len(self._acceleration_x) > 0 else 0
    self._acceleration_x_filter.update(soon_acceleration)
    self._acceleration_x_filter2.update(soon_acceleration)

    # make path width wider/thinner when initially braking/accelerating
    if self._experimental_mode and False:
      high_pass_acceleration = self._acceleration_x_filter.x - self._acceleration_x_filter2.x
      y_off = np.interp(high_pass_acceleration, [-1, 0, 1], [0.9 * 2, 0.9, 0.9 / 2])
    else:
      y_off = 0.9

    max_idx = self._get_path_length_idx(path_x_array, max_distance)
    self._path.projected_points = self._map_line_to_polygon(
      self._path.raw_points, y_off, self._path_offset_z, max_idx, allow_invert=False
    )

    self._update_experimental_gradient()