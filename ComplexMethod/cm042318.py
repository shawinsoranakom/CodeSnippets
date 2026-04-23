def _render(self, _):
    # draw current text so far below everything. text floats left but always stays in view
    text = self._keyboard.text()
    candidate_char = self._keyboard.get_candidate_character()
    text_size = measure_text_cached(gui_app.font(FontWeight.ROMAN), text + candidate_char or self._hint_label.text, self.TEXT_INPUT_SIZE)

    bg_block_margin = 5
    text_x = PADDING / 2 + self._enter_img.width + PADDING
    text_field_rect = rl.Rectangle(text_x, self._rect.y + PADDING - bg_block_margin,
                                   self._rect.width - text_x * 2,
                                   text_size.y)

    # draw text input
    # push text left with a gradient on left side if too long
    if text_size.x > text_field_rect.width:
      text_x -= text_size.x - text_field_rect.width

    rl.begin_scissor_mode(int(text_field_rect.x), int(text_field_rect.y), int(text_field_rect.width), int(text_field_rect.height))
    rl.draw_text_ex(gui_app.font(FontWeight.ROMAN), text, rl.Vector2(text_x, text_field_rect.y), self.TEXT_INPUT_SIZE, 0, rl.WHITE)

    # draw grayed out character user is hovering over
    if candidate_char:
      candidate_char_size = measure_text_cached(gui_app.font(FontWeight.ROMAN), candidate_char, self.TEXT_INPUT_SIZE)
      rl.draw_text_ex(gui_app.font(FontWeight.ROMAN), candidate_char,
                      rl.Vector2(min(text_x + text_size.x, text_field_rect.x + text_field_rect.width) - candidate_char_size.x, text_field_rect.y),
                      self.TEXT_INPUT_SIZE, 0, rl.Color(255, 255, 255, 128))

    rl.end_scissor_mode()

    # draw gradient on left side to indicate more text
    if text_size.x > text_field_rect.width:
      rl.draw_rectangle_gradient_ex(rl.Rectangle(text_field_rect.x, text_field_rect.y, 80, text_field_rect.height),
                                    rl.BLACK, rl.BLANK, rl.BLANK, rl.BLACK)

    # draw cursor
    blink_alpha = (math.sin(rl.get_time() * 6) + 1) / 2
    if text:
      cursor_x = min(text_x + text_size.x + 3, text_field_rect.x + text_field_rect.width)
    else:
      cursor_x = text_field_rect.x - 6
    rl.draw_rectangle_rounded(rl.Rectangle(cursor_x, text_field_rect.y, 4, text_size.y),
                              1, 4, rl.Color(255, 255, 255, int(255 * blink_alpha)))

    # draw backspace icon with nice fade
    self._backspace_img_alpha.update(255 * bool(text))
    if self._backspace_img_alpha.x > 1:
      color = rl.Color(255, 255, 255, int(self._backspace_img_alpha.x))
      rl.draw_texture_ex(self._backspace_img, rl.Vector2(self._rect.width - self._backspace_img.width - 27, self._rect.y + 14), 0.0, 1.0, color)

    if not text and self._hint_label.text and not candidate_char:
      # draw description if no text entered yet and not drawing candidate char
      hint_rect = rl.Rectangle(text_field_rect.x, text_field_rect.y,
                               self._rect.width - text_field_rect.x - PADDING,
                               text_field_rect.height)
      self._hint_label.render(hint_rect)

    # TODO: move to update state
    # make rect take up entire area so it's easier to click
    self._top_left_button_rect = rl.Rectangle(self._rect.x, self._rect.y, text_field_rect.x, self._rect.height - self._keyboard.get_keyboard_height())
    self._top_right_button_rect = rl.Rectangle(text_field_rect.x + text_field_rect.width, self._rect.y,
                                               self._rect.width - (text_field_rect.x + text_field_rect.width), self._top_left_button_rect.height)

    # draw enter button
    self._enter_img_alpha.update(255 if len(text) >= self._minimum_length else 0)
    color = rl.Color(255, 255, 255, int(self._enter_img_alpha.x))
    rl.draw_texture_ex(self._enter_img, rl.Vector2(self._rect.x + PADDING / 2, self._rect.y), 0.0, 1.0, color)
    color = rl.Color(255, 255, 255, 255 - int(self._enter_img_alpha.x))
    rl.draw_texture_ex(self._enter_disabled_img, rl.Vector2(self._rect.x + PADDING / 2, self._rect.y), 0.0, 1.0, color)

    # keyboard goes over everything
    self._keyboard.render(self._rect)

    # draw debugging rect bounds
    if DEBUG:
      rl.draw_rectangle_lines_ex(text_field_rect, 1, rl.Color(100, 100, 100, 255))
      rl.draw_rectangle_lines_ex(self._top_right_button_rect, 1, rl.Color(0, 255, 0, 255))
      rl.draw_rectangle_lines_ex(self._top_left_button_rect, 1, rl.Color(0, 255, 0, 255))