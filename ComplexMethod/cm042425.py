def _render(self, rect: rl.Rectangle):
    rect = rl.Rectangle(rect.x + CONTENT_MARGIN, rect.y + CONTENT_MARGIN, rect.width - 2 * CONTENT_MARGIN, rect.height - 2 * CONTENT_MARGIN)
    self._title.render(rl.Rectangle(rect.x, rect.y, rect.width, 95))
    self._sub_title.render(rl.Rectangle(rect.x, rect.y + 95, rect.width, 60))
    self._cancel_button.render(rl.Rectangle(rect.x + rect.width - 386, rect.y, 386, 125))

    # Draw input box and password toggle
    input_margin = 25
    input_box_rect = rl.Rectangle(rect.x + input_margin, rect.y + 160, rect.width - input_margin, 100)
    self._render_input_area(input_box_rect)

    # Process backspace key repeat if it's held down
    if not self._all_keys[BACKSPACE_KEY].is_pressed:
      self._backspace_pressed = False

    if self._backspace_pressed:
      current_time = time.monotonic()
      time_since_press = current_time - self._backspace_press_time

      # After initial delay, start repeating with shorter intervals
      if time_since_press > DELETE_REPEAT_DELAY:
        time_since_last_repeat = current_time - self._backspace_last_repeat
        if time_since_last_repeat > DELETE_REPEAT_INTERVAL:
          self._input_box.delete_char_before_cursor()
          self._backspace_last_repeat = current_time

    layout = KEYBOARD_LAYOUTS[self._layout_name]

    h_space, v_space = 15, 15
    row_y_start = rect.y + 300  # Starting Y position for the first row
    key_height = (rect.height - 300 - 3 * v_space) / 4
    key_max_width = (rect.width - (len(layout[2]) - 1) * h_space) / len(layout[2])

    # Iterate over the rows of keys in the current layout
    for row, keys in enumerate(layout):
      key_width = min((rect.width - (180 if row == 1 else 0) - h_space * (len(keys) - 1)) / len(keys), key_max_width)
      start_x = rect.x + (90 if row == 1 else 0)

      for i, key in enumerate(keys):
        if i > 0:
          start_x += h_space

        new_width = (key_width * 3 + h_space * 2) if key == SPACE_KEY else (key_width * 2 + h_space if key == ENTER_KEY else key_width)
        key_rect = rl.Rectangle(start_x, row_y_start + row * (key_height + v_space), new_width, key_height)
        start_x += new_width

        is_enabled = key != ENTER_KEY or len(self._input_box.text) >= self._min_text_size

        if key == BACKSPACE_KEY and self._all_keys[BACKSPACE_KEY].is_pressed and not self._backspace_pressed:
          self._backspace_pressed = True
          self._backspace_press_time = time.monotonic()
          self._backspace_last_repeat = time.monotonic()

        if key in self._key_icons:
          if key == SHIFT_ACTIVE_KEY and self._caps_lock:
            key = CAPS_LOCK_KEY
          self._all_keys[key].set_enabled(is_enabled)
          self._all_keys[key].render(key_rect)
        else:
          self._all_keys[key].set_enabled(is_enabled)
          self._all_keys[key].render(key_rect)