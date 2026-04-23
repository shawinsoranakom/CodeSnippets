def _render(self, rect: rl.Rectangle):
    spacing = RIGHT_ITEM_PADDING
    button_y = rect.y + (rect.height - BUTTON_HEIGHT) / 2

    for i, _text in enumerate(self.buttons):
      button_x = rect.x + i * (self.button_width + spacing)
      button_rect = rl.Rectangle(button_x, button_y, self.button_width, BUTTON_HEIGHT)

      # Check button state
      mouse_pos = rl.get_mouse_position()
      is_pressed = rl.check_collision_point_rec(mouse_pos, button_rect) and self.enabled and self.is_pressed
      is_selected = i == self.selected_button

      # Button colors
      if is_selected:
        bg_color = rl.Color(51, 171, 76, 255)  # Green
      elif is_pressed:
        bg_color = rl.Color(74, 74, 74, 255)  # Dark gray
      else:
        bg_color = rl.Color(57, 57, 57, 255)  # Gray

      if not self.enabled:
        bg_color = rl.Color(bg_color.r, bg_color.g, bg_color.b, 150)  # Dim

      # Draw button
      rl.draw_rectangle_rounded(button_rect, 1.0, 20, bg_color)

      # Draw text
      text = _resolve_value(_text, "")
      text_size = measure_text_cached(self._font, text, 40)
      text_x = button_x + (self.button_width - text_size.x) / 2
      text_y = button_y + (BUTTON_HEIGHT - text_size.y) / 2
      text_color = rl.Color(228, 228, 228, 255) if self.enabled else rl.Color(150, 150, 150, 255)
      rl.draw_text_ex(self._font, text, rl.Vector2(text_x, text_y), 40, 0, text_color)