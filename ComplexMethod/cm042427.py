def _handle_keyboard_input(self):
    # Handle navigation keys
    key = rl.get_key_pressed()
    if key != 0:
      self._process_key(key)
      if key in (rl.KEY_LEFT, rl.KEY_RIGHT, rl.KEY_BACKSPACE, rl.KEY_DELETE):
        self._last_key_pressed = key
        self._key_press_time = 0

    # Handle repeats for held keys
    elif self._last_key_pressed != 0:
      if rl.is_key_down(self._last_key_pressed):
        self._key_press_time += 1
        if self._key_press_time > self._repeat_delay and self._key_press_time % self._repeat_rate == 0:
          self._process_key(self._last_key_pressed)
      else:
        self._last_key_pressed = 0

    # Handle text input
    char = rl.get_char_pressed()
    if char != 0 and char >= 32:  # Filter out control characters
      self.add_char_at_cursor(chr(char))