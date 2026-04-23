def _handle_mouse_event(self, mouse_event: MouseEvent, bounds: rl.Rectangle, bounds_size: float,
                          content_size: float) -> None:
    max_offset, min_offset = self._get_offset_bounds(bounds_size, content_size)
    # simple exponential return if out of bounds
    out_of_bounds = self.get_offset() > max_offset or self.get_offset() < min_offset
    if DEBUG:
      print('Mouse event:', mouse_event)

    mouse_pos = self._get_mouse_pos(mouse_event)

    if not self.enabled:
      # Reset state if not enabled
      self._state = ScrollState.STEADY
      self._velocity = 0.0
      self._velocity_buffer.clear()

    elif self._state == ScrollState.STEADY:
      if rl.check_collision_point_rec(mouse_event.pos, bounds):
        if mouse_event.left_pressed:
          self._state = ScrollState.PRESSED
          self._initial_click_event = mouse_event

    elif self._state == ScrollState.PRESSED:
      initial_click_pos = self._get_mouse_pos(cast(MouseEvent, self._initial_click_event))
      diff = abs(mouse_pos - initial_click_pos)
      if mouse_event.left_released:
        # Special handling for down and up clicks across two frames
        # TODO: not sure what that means or if it's accurate anymore
        if out_of_bounds:
          self._state = ScrollState.AUTO_SCROLL
        elif diff <= MIN_DRAG_PIXELS:
          self._state = ScrollState.STEADY
        else:
          self._state = ScrollState.MANUAL_SCROLL
      elif diff > MIN_DRAG_PIXELS:
        self._state = ScrollState.MANUAL_SCROLL

    elif self._state == ScrollState.MANUAL_SCROLL:
      if mouse_event.left_released:
        # Touch rejection: when releasing finger after swiping and stopping, panel
        # reports a few erroneous touch events with high velocity, try to ignore.

        # If velocity decelerates very quickly, assume user doesn't intend to auto scroll.
        # Catches two cases: 1) swipe, stop finger, then lift (stale high velocity in buffer)
        # 2) dirty finger lift where finger rotates/slides producing spurious velocity spike.
        # TODO: this heuristic false-positives on fast swipes because 140Hz touch polling
        #  jitter causes velocity to oscillate (not real deceleration). Better approaches:
        #  - Use evdev kernel timestamps to eliminate velocity oscillation at the source
        #  - Replace with a time-since-last-event check (40ms timeout) for swipe-stop-lift
        high_decel = False
        if len(self._velocity_buffer) > 2:
          # We limit max to first half since final few velocities can surpass first few
          abs_velocity_buffer = [(abs(v), i) for i, v in enumerate(self._velocity_buffer)]
          max_idx = max(abs_velocity_buffer[:len(abs_velocity_buffer) // 2])[1]
          min_idx = min(abs_velocity_buffer)[1]
          if DEBUG:
            print('min_idx:', min_idx, 'max_idx:', max_idx, 'velocity buffer:', self._velocity_buffer)
          if (abs(self._velocity_buffer[min_idx]) * REJECT_DECELERATION_FACTOR < abs(self._velocity_buffer[max_idx]) and
              max_idx < min_idx):
            if DEBUG:
              print('deceleration too high, going to STEADY')
            high_decel = True

        self._velocity = weighted_velocity(self._velocity_buffer)

        # If final velocity is below some threshold, switch to steady state too
        low_speed = abs(self._velocity) <= MIN_VELOCITY_FOR_CLICKING * 1.5  # plus some margin

        if out_of_bounds or not (high_decel or low_speed):
          self._state = ScrollState.AUTO_SCROLL
        else:
          # TODO: we should just set velocity and let autoscroll go back to steady. delays one frame but who cares
          self._velocity = 0.0
          self._state = ScrollState.STEADY
        self._velocity_buffer.clear()
      else:
        # Update velocity for when we release the mouse button.
        # Do not update velocity on the same frame the mouse was released
        previous_mouse_pos = self._get_mouse_pos(cast(MouseEvent, self._previous_mouse_event))
        delta_x = mouse_pos - previous_mouse_pos
        delta_t = max((mouse_event.t - cast(MouseEvent, self._previous_mouse_event).t), 1e-6)
        self._velocity = delta_x / delta_t
        self._velocity = max(-MAX_SPEED, min(MAX_SPEED, self._velocity))
        self._velocity_buffer.append(self._velocity)

        # rubber-banding: reduce dragging when out of bounds
        # TODO: this drifts when dragging quickly
        if out_of_bounds:
          delta_x *= 0.25

        # Update the offset based on the mouse movement
        # Use internal _offset directly to preserve precision (don't round via get_offset())
        # TODO: make get_offset return float
        current_offset = self._offset.x if self._horizontal else self._offset.y
        self.set_offset(current_offset + delta_x)

    elif self._state == ScrollState.AUTO_SCROLL:
      if mouse_event.left_pressed:
        # Decide whether to click or scroll (block click if moving too fast)
        if abs(self._velocity) <= MIN_VELOCITY_FOR_CLICKING:
          # Traveling slow enough, click
          self._state = ScrollState.PRESSED
          self._initial_click_event = mouse_event
        else:
          # Go straight into manual scrolling to block erroneous input
          self._state = ScrollState.MANUAL_SCROLL
          # Reset velocity for touch down and up events that happen in back-to-back frames
          self._velocity = 0.0