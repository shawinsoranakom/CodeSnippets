def _update_state(self, bounds: rl.Rectangle, content: rl.Rectangle):
    if DEBUG:
      rl.draw_rectangle_lines(0, 0, abs(int(self._velocity_filter_y.x)), 10, rl.RED)

    # Handle mouse wheel
    self._offset_filter_y.x += rl.get_mouse_wheel_move() * MOUSE_WHEEL_SCROLL_SPEED

    max_scroll_distance = max(0, content.height - bounds.height)
    if self._scroll_state == ScrollState.IDLE:
      above_bounds, below_bounds = self._check_bounds(bounds, content)

      # Decay velocity when idle
      if abs(self._velocity_filter_y.x) > MIN_VELOCITY:
        # Faster decay if bouncing back from out of bounds
        friction = math.exp(-BOUNCE_RETURN_RATE * 1 / gui_app.target_fps)
        self._velocity_filter_y.x *= friction ** 2 if (above_bounds or below_bounds) else friction
      else:
        self._velocity_filter_y.x = 0.0

      if above_bounds or below_bounds:
        if above_bounds:
          self._offset_filter_y.update(0)
        else:
          self._offset_filter_y.update(-max_scroll_distance)

      self._offset_filter_y.x += self._velocity_filter_y.x / gui_app.target_fps

    elif self._scroll_state == ScrollState.DRAGGING_CONTENT:
      # Mouse not moving, decay velocity
      if not len(gui_app.mouse_events):
        self._velocity_filter_y.update(0.0)

    # Settle to exact bounds
    if abs(self._offset_filter_y.x) < 1e-2:
      self._offset_filter_y.x = 0.0
    elif abs(self._offset_filter_y.x + max_scroll_distance) < 1e-2:
      self._offset_filter_y.x = -max_scroll_distance