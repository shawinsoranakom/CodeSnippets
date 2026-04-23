def _do_move_animation(self, item: Widget, target_x: float, target_y: float) -> tuple[float, float]:
    # wait a frame before moving so we match potential pending scroll animation
    can_start_move = len(self._pending_lift) == 0

    if item in self._move_lift:
      lift_filter = self._move_lift[item]

      # Animate lift
      if len(self._pending_move) > 0:
        lift_filter.update(MOVE_LIFT)
        # start moving when almost lifted
        if abs(lift_filter.x - MOVE_LIFT) < 2:
          self._pending_lift.discard(item)
      else:
        # if done moving, animate down
        lift_filter.update(0)
        if abs(lift_filter.x) < 1:
          del self._move_lift[item]
      target_y -= lift_filter.x

    # Animate move
    if item in self._move_animations:
      move_filter = self._move_animations[item]

      # compare/update in content space to match filter
      content_x = target_x - self._scroll_offset
      if can_start_move:
        move_filter.update(content_x)

        # drop when close to target
        if abs(move_filter.x - content_x) < 10:
          self._pending_move.discard(item)

        # finished moving
        if abs(move_filter.x - content_x) < 1:
          del self._move_animations[item]
      target_x = move_filter.x + self._scroll_offset

    return target_x, target_y