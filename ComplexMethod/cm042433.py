def _update_state(self, bounds_size: float, content_size: float) -> None:
    """Runs per render frame, independent of mouse events. Updates auto-scrolling state and velocity."""
    max_offset, min_offset = self._get_offset_bounds(bounds_size, content_size)

    if self._state == ScrollState.STEADY:
      # if we find ourselves out of bounds, scroll back in (from external layout dimension changes, etc.)
      if self.get_offset() > max_offset or self.get_offset() < min_offset:
        self._state = ScrollState.AUTO_SCROLL

    elif self._state == ScrollState.AUTO_SCROLL:
      # simple exponential return if out of bounds
      out_of_bounds = self.get_offset() > max_offset or self.get_offset() < min_offset
      if out_of_bounds and self._handle_out_of_bounds:
        target = max_offset if self.get_offset() > max_offset else min_offset

        dt = rl.get_frame_time() or 1e-6
        factor = 1.0 - math.exp(-BOUNCE_RETURN_RATE * dt)

        dist = target - self.get_offset()
        self.set_offset(self.get_offset() + dist * factor)  # ease toward the edge
        self._velocity *= (1.0 - factor)  # damp any leftover fling

        # Steady once we are close enough to the target
        if abs(dist) < 1 and abs(self._velocity) < MIN_VELOCITY:
          self.set_offset(target)
          self._velocity = 0.0
          self._state = ScrollState.STEADY

      elif abs(self._velocity) < MIN_VELOCITY:
        self._velocity = 0.0
        self._state = ScrollState.STEADY

      # Update the offset based on the current velocity
      dt = rl.get_frame_time()
      self.set_offset(self.get_offset() + self._velocity * dt)  # Adjust the offset based on velocity
      alpha = 1 - (dt / (self._AUTO_SCROLL_TC + dt))
      self._velocity *= alpha