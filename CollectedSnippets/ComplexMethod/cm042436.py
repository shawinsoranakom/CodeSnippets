def _handle_mouse_event(self, mouse_event: MouseEvent, bounds: rl.Rectangle, content: rl.Rectangle):
    if self._scroll_state == ScrollState.IDLE:
      if rl.check_collision_point_rec(mouse_event.pos, bounds):
        if mouse_event.left_pressed:
          self._start_mouse_y = mouse_event.pos.y
          # Interrupt scrolling with new drag
          # TODO: stop scrolling with any tap, need to fix is_touch_valid
          if abs(self._velocity_filter_y.x) > MIN_VELOCITY_FOR_CLICKING:
            self._scroll_state = ScrollState.DRAGGING_CONTENT
            # Start velocity at initial measurement for more immediate response
            self._velocity_filter_y.initialized = False

        if mouse_event.left_down:
          if abs(mouse_event.pos.y - self._start_mouse_y) > DRAG_THRESHOLD:
            self._scroll_state = ScrollState.DRAGGING_CONTENT
            # Start velocity at initial measurement for more immediate response
            self._velocity_filter_y.initialized = False

    elif self._scroll_state == ScrollState.DRAGGING_CONTENT:
      if mouse_event.left_released:
        self._scroll_state = ScrollState.IDLE
      else:
        delta_y = mouse_event.pos.y - self._last_mouse_y
        above_bounds, below_bounds = self._check_bounds(bounds, content)
        # Rubber banding effect when out of bands
        if above_bounds or below_bounds:
          delta_y /= 3

        self._offset_filter_y.x += delta_y

        # Track velocity for inertia
        dt = mouse_event.t - self._last_drag_time
        if dt > 0:
          drag_velocity = delta_y / dt
          self._velocity_filter_y.update(drag_velocity)

        # TODO: just store last mouse event!
    self._last_drag_time = mouse_event.t
    self._last_mouse_y = mouse_event.pos.y