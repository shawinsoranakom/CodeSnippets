def _update_state(self):
    # Get monitoring state
    _ = self.get_driver_data()
    pitch = self._pitch_filter.update(self._face_pitch)
    yaw = self._yaw_filter.update(self._face_yaw)

    # hysteresis on looking center
    if abs(pitch) < LOOKING_CENTER_THRESHOLD_LOWER and abs(yaw) < LOOKING_CENTER_THRESHOLD_LOWER:
      self._looking_center = True
    elif abs(pitch) > LOOKING_CENTER_THRESHOLD_UPPER or abs(yaw) > LOOKING_CENTER_THRESHOLD_UPPER:
      self._looking_center = False
    self._looking_center_filter.update(1 if self._looking_center else 0)

    if DEBUG:
      pitchd = math.degrees(pitch)
      yawd = math.degrees(yaw)

      rl.draw_line_ex((0, 100), (200, 100), 3, rl.RED)
      rl.draw_line_ex((0, 120), (200, 120), 3, rl.RED)
      rl.draw_line_ex((0, 140), (200, 140), 3, rl.RED)

      pitch_x = 100 + pitchd
      yaw_x = 100 + yawd
      rl.draw_circle(int(pitch_x), 100, 5, rl.GREEN)
      rl.draw_circle(int(yaw_x), 120, 5, rl.GREEN)

    # filter head rotation, handling wrap-around
    rotation = math.degrees(math.atan2(pitch * 2, yaw))  # reduce yaw sensitivity
    angle_diff = rotation - self._rotation_filter.x
    angle_diff = ((angle_diff + 180) % 360) - 180
    self._rotation_filter.update(self._rotation_filter.x + angle_diff)

    if not self.should_draw:
      self._fade_filter.update(0.0)
    elif not self.effective_active:
      self._fade_filter.update(0.35)
    else:
      self._fade_filter.update(1.0)