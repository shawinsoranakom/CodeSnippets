def _handle_mouse_event(self, mouse_event: MouseEvent) -> None:
    super()._handle_mouse_event(mouse_event)

    # Don't let touch events change filter state during dismiss animation
    if self._playing_dismiss_animation:
      return

    if mouse_event.left_pressed:
      # user is able to swipe away if starting near top of screen
      self._y_pos_filter.update_alpha(0.04)
      in_dismiss_area = mouse_event.pos.y < self._rect.height * self.BACK_TOUCH_AREA_PERCENTAGE

      if in_dismiss_area and self._back_enabled():
        self._drag_start_pos = mouse_event.pos

    elif mouse_event.left_down:
      if self._drag_start_pos is not None:
        # block swiping away if too much horizontal or upward movement
        # block (lock-in) threshold is higher than start dismissing
        horizontal_movement = abs(mouse_event.pos.x - self._drag_start_pos.x) > BLOCK_SWIPE_AWAY_THRESHOLD
        upward_movement = mouse_event.pos.y - self._drag_start_pos.y < -BLOCK_SWIPE_AWAY_THRESHOLD

        if not (horizontal_movement or upward_movement):
          # no blocking movement, check if we should start dismissing
          if mouse_event.pos.y - self._drag_start_pos.y > START_DISMISSING_THRESHOLD:
            self._dragging_down = True
        else:
          if not self._dragging_down:
            self._drag_start_pos = None

    elif mouse_event.left_released:
      # reset rc for either slide up or down animation
      self._y_pos_filter.update_alpha(0.1)

      # if far enough, trigger back navigation callback
      if self._drag_start_pos is not None:
        if mouse_event.pos.y - self._drag_start_pos.y > SWIPE_AWAY_THRESHOLD:
          self._playing_dismiss_animation = True

      self._drag_start_pos = None
      self._dragging_down = False