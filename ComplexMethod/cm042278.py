def _render(self, rect: rl.Rectangle):
    sm = ui_state.sm

    # Check if data is up-to-date
    if (sm.recv_frame["liveCalibration"] < ui_state.started_frame or
        sm.recv_frame["modelV2"] < ui_state.started_frame):
      return

    # Set up clipping region
    self._clip_region = rl.Rectangle(
      rect.x - CLIP_MARGIN, rect.y - CLIP_MARGIN, rect.width + 2 * CLIP_MARGIN, rect.height + 2 * CLIP_MARGIN
    )

    # Update state
    self._experimental_mode = sm['selfdriveState'].experimentalMode

    live_calib = sm['liveCalibration']
    self._path_offset_z = live_calib.height[0] if live_calib.height else HEIGHT_INIT[0]

    if sm.updated['carParams']:
      self._longitudinal_control = sm['carParams'].openpilotLongitudinalControl

    model = sm['modelV2']
    radar_state = sm['radarState'] if sm.valid['radarState'] else None
    lead_one = radar_state.leadOne if radar_state else None
    render_lead_indicator = self._longitudinal_control and radar_state is not None

    # Update model data when needed
    model_updated = sm.updated['modelV2']
    if model_updated or sm.updated['radarState'] or self._transform_dirty:
      if model_updated:
        self._update_raw_points(model)

      path_x_array = self._path.raw_points[:, 0]
      if path_x_array.size == 0:
        return

      self._update_model(lead_one, path_x_array)
      if render_lead_indicator:
        self._update_leads(radar_state, path_x_array)
      self._transform_dirty = False

    # Draw elements
    self._draw_lane_lines()
    self._draw_path(sm)

    if render_lead_indicator and radar_state:
      self._draw_lead_indicator()