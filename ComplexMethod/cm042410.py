def _handle_mouse_event(self, mouse_event: MouseEvent) -> None:
    keyboard_pos_y = self._rect.y + self._rect.height - self._txt_bg.height
    if mouse_event.left_pressed:
      if mouse_event.pos.y > keyboard_pos_y:
        self._dragging_on_keyboard = True
    elif mouse_event.left_released:
      self._dragging_on_keyboard = False

    if mouse_event.left_down and self._dragging_on_keyboard:
      self._closest_key = self._get_closest_key()
      if self._selected_key_t is None:
        self._selected_key_t = rl.get_time()

      # unselect key temporarily if mouse goes above keyboard
      if mouse_event.pos.y <= keyboard_pos_y:
        self._closest_key = (None, float('inf'))

    if DEBUG:
      print('HANDLE MOUSE EVENT', mouse_event, self._closest_key[0].char if self._closest_key[0] else 'None')