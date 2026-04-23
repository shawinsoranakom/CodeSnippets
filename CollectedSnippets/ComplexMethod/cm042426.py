def handle_key_press(self, key):
    if key in (CAPS_LOCK_KEY, ABC_KEY):
      self._caps_lock = False
      self._layout_name = "lowercase"
    elif key == SHIFT_INACTIVE_KEY:
      self._last_shift_press_time = time.monotonic()
      self._layout_name = "uppercase"
    elif key == SHIFT_ACTIVE_KEY:
      if time.monotonic() - self._last_shift_press_time < DOUBLE_CLICK_THRESHOLD:
        self._caps_lock = True
      else:
        self._layout_name = "lowercase"
    elif key == NUMERIC_KEY:
      self._layout_name = "numbers"
    elif key == SYMBOL_KEY:
      self._layout_name = "specials"
    elif key == BACKSPACE_KEY:
      self._input_box.delete_char_before_cursor()
    else:
      self._input_box.add_char_at_cursor(key)
      if not self._caps_lock and self._layout_name == "uppercase":
        self._layout_name = "lowercase"