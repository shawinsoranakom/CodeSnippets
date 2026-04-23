def _update_state(self):
    super()._update_state()

    new_y = 0.0

    if self._dragging_down:
      self._nav_bar.set_alpha(1.0)

    # FIXME: disabling this widget on new push_widget still causes this widget to track mouse events without mouse down
    if not self.enabled:
      self._drag_start_pos = None

    if self._drag_start_pos is not None:
      last_mouse_event = gui_app.last_mouse_event
      # push entire widget as user drags it away
      new_y = max(last_mouse_event.pos.y - self._drag_start_pos.y, 0)
      if new_y < SWIPE_AWAY_THRESHOLD:
        new_y /= 2  # resistance until mouse release would dismiss widget

    if self._playing_dismiss_animation:
      new_y = self._rect.height + DISMISS_PUSH_OFFSET

    new_y = self._y_pos_filter.update(new_y)
    if abs(new_y) < 1 and abs(self._y_pos_filter.velocity.x) < 0.5:
      new_y = self._y_pos_filter.x = 0.0
      self._y_pos_filter.velocity.x = 0.0

      if self._shown_callback is not None:
        self._shown_callback()
        self._shown_callback = None

    if new_y > self._rect.height + DISMISS_PUSH_OFFSET - 10:
      gui_app.pop_widget()

      # Only one callback should ever be fired
      if self._dismiss_callback is not None:
        self._dismiss_callback()
        self._dismiss_callback = None
      elif self._back_callback is not None:
        self._back_callback()

      self._playing_dismiss_animation = False
      self._drag_start_pos = None
      self._dragging_down = False

    self.set_position(self._rect.x, new_y)