def _process_key(self, key):
    if key == rl.KEY_LEFT:
      if self._cursor_position > 0:
        self.set_cursor_position(self._cursor_position - 1)
    elif key == rl.KEY_RIGHT:
      if self._cursor_position < len(self._input_text):
        self.set_cursor_position(self._cursor_position + 1)
    elif key == rl.KEY_BACKSPACE:
      self.delete_char_before_cursor()
    elif key == rl.KEY_DELETE:
      self.delete_char_at_cursor()
    elif key == rl.KEY_HOME:
      self.set_cursor_position(0)
    elif key == rl.KEY_END:
      self.set_cursor_position(len(self._input_text))